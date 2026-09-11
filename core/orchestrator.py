"""Unified orchestrator for HiddenTanks + AutoRanksOFF.

Generation policy (safe):
  1. read originals (game / DLC)
  2. transform in memory, write to temp staging dir first
  3. backup originals to <game>/BlitzMods_Backup/<mod_id>/{Game,DLC}
  4. copy staged files over the originals (DLC -> read-only)

Export policy:
  Result/<bundle>/Mod/{Data,packs} + Backup/{Data,packs}

DLC rule: DLC files are ALWAYS DVPL (even in NON-DVPL mode).
Game files keep the encoding of the physical file that was found
(DVPL mode prefers *.dvpl, NON-DVPL prefers plain).
"""
import os
import shutil
import stat
import xml.etree.ElementTree as ET

from core import file_ops
from core.file_ops import (
    resolve_game_physical, dlc_physical, read_physical, write_physical,
    make_staging, install_one, get_game_version,
)
from core.hidden_tanks import NATIONS, process_xml, generate_tree_yaml, get_nation_stat, classify_tank
from core.autoranks import AUTORANKS_FILES, modify_autoranks_text

BACKUP_DIR_NAME = "BlitzMods_Backup"

MOD_IDS = ("hidden_tanks", "autoranks")


def mod_rel_paths(mod_id):
    if mod_id == "hidden_tanks":
        rels = []
        for _code, (_name, tree_rel, list_rel) in NATIONS.items():
            rels.extend([tree_rel, list_rel])
        return rels
    if mod_id == "autoranks":
        return list(AUTORANKS_FILES)
    return []


def check_dlc_presence(dlc_root, mod_ids):
    """Return {mod_id: [rel,...]} of DLC files that exist on disk."""
    from core.dlc_utils import find_existing_dlc_files
    out = {}
    for mid in mod_ids:
        out[mid] = find_existing_dlc_files(dlc_root, mod_rel_paths(mid))
    return out


def _pick_source(game_path, rel, use_dlc, dlc_root, dvpl_mode):
    """Return (src_path, is_dlc) or (None, False). DLC preferred when enabled."""
    if use_dlc and dlc_root:
        cand = os.path.join(dlc_root, rel) + ".dvpl"
        if os.path.exists(cand):
            return cand, True
    phys = resolve_game_physical(game_path, rel, dvpl_mode)
    if phys:
        return phys, False
    return None, False


def _log_nondvpl_twins(game_path, rels, dvpl_mode, log, tr):
    """In NON-DVPL, hint when a game file exists only as .dvpl (skipped by design)."""
    if dvpl_mode != 'NON-DVPL':
        return
    for rel in rels:
        twin = os.path.join(game_path, "Data", rel) + ".dvpl"
        if os.path.exists(twin):
            if tr:
                log(tr('log_nondvpl_skip', file=twin))
            else:
                log(f"  ! NON-DVPL skips DVPL file: {twin} (unpack it or switch to DVPL mode)")


def _stage_write(staging, name, text, encoding, is_dvpl, comp):
    dst = os.path.join(staging, name)
    write_physical(dst, text, encoding, is_dvpl, comp)
    return dst


# ---------------- HiddenTanks ----------------

def _hidden_nation_pair(game_path, code, dvpl_mode, use_dlc, dlc_root, log, tr):
    _name, tree_rel, list_rel = NATIONS[code]
    tree_src, tree_dlc = _pick_source(game_path, tree_rel, use_dlc, dlc_root, dvpl_mode)
    list_src, list_dlc = _pick_source(game_path, list_rel, use_dlc, dlc_root, dvpl_mode)
    if not tree_src or not list_src:
        log(tr('log_files_not_found') if tr else "  files not found, skipping")
        _log_nondvpl_twins(game_path, (tree_rel, list_rel), dvpl_mode, log, tr)
        return None
    log((tr('log_reading_tree', file=tree_src) if tr else f"  Reading tree: {tree_src}"))
    t = read_physical(tree_src)
    log((tr('log_reading_list', file=list_src) if tr else f"  Reading list: {list_src}"))
    li = read_physical(list_src)
    if not t['text'].strip() or not li['text'].strip():
        log(tr('log_empty_file') if tr else "  empty file, skipping")
        return None
    new_list, tank_data = process_xml(li['text'])
    new_tree = generate_tree_yaml(t['text'], tank_data, nation_code=code)
    stat_ = get_nation_stat(tank_data, t['text'])
    return {
        'code': code, 'tree_rel': tree_rel, 'list_rel': list_rel,
        'tree_src': tree_src, 'list_src': list_src,
        'tree_dlc': tree_dlc, 'list_dlc': list_dlc,
        'tree': t, 'list': li,
        'new_tree': new_tree, 'new_list': new_list,
        'stat': stat_,
    }


def _count_mod_jobs(game_path, mod_ids, dvpl_mode, use_dlc, dlc_root):
    """Upfront file count for progress (hidden: 2 per usable nation)."""
    total = 0
    if "hidden_tanks" in mod_ids:
        for code, (_name, tree_rel, list_rel) in NATIONS.items():
            tree_src, _ = _pick_source(game_path, tree_rel, use_dlc, dlc_root, dvpl_mode)
            list_src, _ = _pick_source(game_path, list_rel, use_dlc, dlc_root, dvpl_mode)
            if tree_src and list_src:
                total += 2
    if "autoranks" in mod_ids:
        for rel in AUTORANKS_FILES:
            src, _ = _pick_source(game_path, rel, use_dlc, dlc_root, dvpl_mode)
            if src:
                total += 1
    return total


def _make_ticker(progress_cb, total):
    done = [0]

    def tick(n=1):
        done[0] += n
        if progress_cb is not None:
            try:
                progress_cb(done[0], total)
            except Exception:
                pass

    tick(0)
    return tick


def _run_hidden(game_path, dvpl_mode, use_dlc, dlc_root, log, tr, do_write, tick=None):
    """do_write(staged_tree, staged_list, pair) -> per-nation commit. Returns stats."""
    stats = {}
    for code, (name, _t, _l) in NATIONS.items():
        log(tr('log_processing_nation', code=code, name=name) if tr else f"Processing {code}...")
        pair = _hidden_nation_pair(game_path, code, dvpl_mode, use_dlc, dlc_root, log, tr)
        if pair is None:
            continue
        do_write(pair)
        if tick is not None:
            tick(2)
        stats[code] = pair['stat']
        log(tr('log_completed', code=code) if tr else f"  done {code}")
    return stats


# ---------------- AutoRanks ----------------

def _run_autoranks(game_path, dvpl_mode, use_dlc, dlc_root, log, tr, do_write, tick=None):
    stats = {'files_total': 0, 'files_changed': 0, 'edits': 0, 'details': []}
    for rel in AUTORANKS_FILES:
        src, is_dlc = _pick_source(game_path, rel, use_dlc, dlc_root, dvpl_mode)
        if not src:
            log((tr('log_autoranks_missing', file=rel) if tr else f"  missing: {rel}, skipping"))
            _log_nondvpl_twins(game_path, (rel,), dvpl_mode, log, tr)
            continue
        stats['files_total'] += 1
        log((tr('log_reading_file', file=src) if tr else f"  Reading: {src}"))
        info = read_physical(src)
        new_text, changes, _notes = modify_autoranks_text(info['text'], rel)
        if changes > 0:
            stats['files_changed'] += 1
            stats['edits'] += changes
        stats['details'].append({'rel': rel, 'src': src, 'is_dlc': is_dlc, 'changes': changes})
        do_write(rel, src, is_dlc, info, new_text, changes)
        if tick is not None:
            tick(1)
    return stats


# ---------------- Public: generate / export / restore / stats ----------------

def _backup_path(game_path, mod_id, is_dlc, src_path, dlc_root):
    root = os.path.join(game_path, BACKUP_DIR_NAME, mod_id)
    if is_dlc and dlc_root:
        rel = os.path.relpath(src_path, dlc_root)
        return os.path.join(root, "DLC", rel)
    rel = os.path.relpath(src_path, game_path)
    return os.path.join(root, "Game", rel)


def generate_mods(game_path, mod_ids, dvpl_mode, use_dlc, dlc_root, log=print, tr=None,
                  progress_cb=None):
    """Staged generation: transform to temp dir, then backup + install. Returns stats dict."""
    staging = make_staging()
    pending = []  # (staged_file, final_dst, is_dlc, backup_dst)
    all_stats = {}
    total = _count_mod_jobs(game_path, mod_ids, dvpl_mode, use_dlc, dlc_root)
    tick = _make_ticker(progress_cb, total)

    def t(key, **kw):
        return tr(key, **kw) if tr else key

    try:
        if "hidden_tanks" in mod_ids:
            def commit_hidden(pair):
                st_tree = _stage_write(staging, f"ht_{pair['code']}_tree",
                                       pair['new_tree'], pair['tree']['encoding'],
                                       pair['tree']['is_dvpl'], pair['tree']['comp'])
                st_list = _stage_write(staging, f"ht_{pair['code']}_list",
                                       pair['new_list'], pair['list']['encoding'],
                                       pair['list']['is_dvpl'], pair['list']['comp'])
                pending.append((st_tree, pair['tree_src'], pair['tree_dlc'],
                                _backup_path(game_path, "hidden_tanks", pair['tree_dlc'], pair['tree_src'], dlc_root)))
                pending.append((st_list, pair['list_src'], pair['list_dlc'],
                                _backup_path(game_path, "hidden_tanks", pair['list_dlc'], pair['list_src'], dlc_root)))
            all_stats["hidden_tanks"] = _run_hidden(game_path, dvpl_mode, use_dlc, dlc_root, log, tr, commit_hidden, tick=tick)

        if "autoranks" in mod_ids:
            def commit_ar(rel, src, is_dlc, info, new_text, changes):
                st = _stage_write(staging, "ar_" + os.path.basename(rel).replace("/", "_").replace("\\", "_"),
                                  new_text, info['encoding'], info['is_dvpl'], info['comp'])
                pending.append((st, src, is_dlc, _backup_path(game_path, "autoranks", is_dlc, src, dlc_root)))
            all_stats["autoranks"] = _run_autoranks(game_path, dvpl_mode, use_dlc, dlc_root, log, tr, commit_ar, tick=tick)

        # Stage complete -> backup originals, then install
        for staged, dst, is_dlc, backup_dst in pending:
            os.makedirs(os.path.dirname(backup_dst), exist_ok=True)
            if not os.path.exists(backup_dst):
                shutil.copy2(dst, backup_dst)
                log(t('log_backup_file', file=backup_dst))
        for staged, dst, is_dlc, _b in pending:
            install_one(staged, dst, set_readonly=bool(is_dlc))
            log(t('log_installed_file', file=dst))
        if progress_cb is not None:
            try:
                progress_cb(total, total)
            except Exception:
                pass
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return all_stats


def export_mods(game_path, mod_ids, dvpl_mode, use_dlc, dlc_root, log=print, tr=None,
                progress_cb=None):
    version = get_game_version(game_path)
    bundle = f"BlitzMods_{'+'.join(mod_ids)}_{version}"
    result_root = os.path.join(os.getcwd(), "result", bundle)
    mod_root = os.path.join(result_root, "Mod")
    backup_root = os.path.join(result_root, "Backup")
    os.makedirs(mod_root, exist_ok=True)
    os.makedirs(backup_root, exist_ok=True)
    total = _count_mod_jobs(game_path, mod_ids, dvpl_mode, use_dlc, dlc_root)
    tick = _make_ticker(progress_cb, total)

    def t(key, **kw):
        return tr(key, **kw) if tr else key

    def out_paths(is_dlc, rel, is_dvpl_src):
        """Map to export paths under Mod/Backup with Data/packs layout."""
        if is_dlc:
            rel_dvpl = rel + ".dvpl"
            return (os.path.join(mod_root, "packs", rel_dvpl),
                    os.path.join(backup_root, "packs", rel_dvpl))
        # game file: keep extension it had (plain or .dvpl)
        return (os.path.join(mod_root, "Data", rel),
                os.path.join(backup_root, "Data", rel))

    # NOTE: export writers below append extension when needed via _export_write
    def _export_write(dst_base, text, encoding, is_dvpl, comp, want_dvpl_suffix):
        dst = dst_base if not want_dvpl_suffix or dst_base.endswith(".dvpl") else dst_base + ".dvpl"
        write_physical(dst, text, encoding, is_dvpl, comp)
        return dst

    if "hidden_tanks" in mod_ids:
        def commit_hidden(pair):
            for kind in ("tree", "list"):
                rel = pair[f"{kind}_rel"]
                src = pair[f"{kind}_src"]
                is_dlc = pair[f"{kind}_dlc"]
                info = pair[kind]
                new_text = pair[f"new_{kind}"]
                mod_dst_b, bak_dst_b = out_paths(is_dlc, rel, info['is_dvpl'])
                want_suffix = bool(is_dlc or info['is_dvpl'])
                _export_write(mod_dst_b, new_text, info['encoding'], want_suffix, info['comp'], want_suffix)
                _export_write(bak_dst_b, info['text'], info['encoding'], want_suffix, info['comp'], want_suffix)
        _run_hidden(game_path, dvpl_mode, use_dlc, dlc_root, log, tr, commit_hidden, tick=tick)

    if "autoranks" in mod_ids:
        def commit_ar(rel, src, is_dlc, info, new_text, changes):
            mod_dst_b, bak_dst_b = out_paths(is_dlc, rel, info['is_dvpl'])
            want_suffix = bool(is_dlc or info['is_dvpl'])
            _export_write(mod_dst_b, new_text, info['encoding'], want_suffix, info['comp'], want_suffix)
            _export_write(bak_dst_b, info['text'], info['encoding'], want_suffix, info['comp'], want_suffix)
        _run_autoranks(game_path, dvpl_mode, use_dlc, dlc_root, log, tr, commit_ar, tick=tick)

    if progress_cb is not None:
        try:
            progress_cb(total, total)
        except Exception:
            pass
    log(t('log_export_completed_to', path=result_root))
    return result_root


def restore_mods(game_path, mod_ids, dlc_root, log=print, tr=None, progress_cb=None):
    def t(key, **kw):
        return tr(key, **kw) if tr else key
    # collect first so progress has an upfront total
    jobs = []
    for mod_id in mod_ids:
        root = os.path.join(game_path, BACKUP_DIR_NAME, mod_id)
        if not os.path.exists(root):
            log(t('log_no_backup_for', mod=mod_id))
            continue
        for prefix, base in (("Game", game_path), ("DLC", dlc_root)):
            src_root = os.path.join(root, prefix)
            if not os.path.exists(src_root) or not base:
                continue
            for dirpath, _dirs, files in os.walk(src_root):
                for f in files:
                    src = os.path.join(dirpath, f)
                    rel = os.path.relpath(src, src_root)
                    jobs.append((src, os.path.join(base, rel), prefix == "DLC"))
    total = len(jobs)
    tick = _make_ticker(progress_cb, total)
    for src, dst, readonly in jobs:
        install_one(src, dst, set_readonly=readonly)
        log(t('log_restored_file', file=dst))
        tick(1)
    if progress_cb is not None:
        try:
            progress_cb(total, total)
        except Exception:
            pass
    log(t('log_restored_count', count=len(jobs)))
    return len(jobs)


def collect_stats(game_path, mod_ids, dvpl_mode, use_dlc, dlc_root, log=print, tr=None,
                  progress_cb=None):
    """Read-only stats (no writes)."""
    total = (len(NATIONS) if "hidden_tanks" in mod_ids else 0) + \
            (len(AUTORANKS_FILES) if "autoranks" in mod_ids else 0)
    tick = _make_ticker(progress_cb, total)
    out = {}
    if "hidden_tanks" in mod_ids:
        stats = {}
        for code in NATIONS:
            pair = _hidden_nation_pair(game_path, code, dvpl_mode, use_dlc, dlc_root, log, tr)
            tick(1)
            if pair is None:
                continue
            stats[code] = pair['stat']
        out["hidden_tanks"] = stats
    if "autoranks" in mod_ids:
        details = []
        for rel in AUTORANKS_FILES:
            src, is_dlc = _pick_source(game_path, rel, use_dlc, dlc_root, dvpl_mode)
            tick(1)
            if not src:
                details.append({'rel': rel, 'found': False})
                continue
            info = read_physical(src)
            _new, changes, _n = modify_autoranks_text(info['text'], rel)
            details.append({'rel': rel, 'found': True, 'is_dlc': is_dlc,
                            'src': src, 'would_change': changes})
        out["autoranks"] = details
    if progress_cb is not None:
        try:
            progress_cb(total, total)
        except Exception:
            pass
    return out
