"""ServersClusterSelector operation: forced server list + per-cluster entries.

Release-client findings (обычныйклиент logs + live tests):
  * ON_TOGGLE_CHANGED dies after the ServerSelection->Content redirect —
    the release PreLogin controller has no handler, and a UI-action flip of
    preLoginData.showServersAsList did NOT work in-game. The toggle is dead,
    period: the list view is forced directly and the toggle button is hidden.
  * CHOOSE_CLUSTER dies at HelperButtons (dialog never opens). Dev buttons
    are pure visuals: HelperButtons.yaml / PreLogin.yaml / PreLogin.actions
    leftovers from older mod versions are reverted to stock here.
  * The client reads the server list NOT from Data but from the cache:
    %LocalAppData%/wotblitz/DAVAProject/region_cache/regions_<ver>.yaml
    (version from Data/version). The mod patches the cache (read-only, so the
    client cannot silently rebuild it) plus both Data twins of
    regions_publish.yaml as the source.

Cluster entries are full copies of the parent region block renamed to
"Parent Host" (Europe EU_C0, ...), with hosts reduced to that single host.
The untouched parent stays as AUTO (all hosts, ping-based). Same realm =>
same account/progress. Row keys stay ASCII (neutral for all languages).

Row template experiment (ServerDescriptionPrototype.yaml): the row only sees
descr.name/flag/index, so the localized parent + cluster suffix are rendered
by when-chains built at generate time from the actual regions mapping:
main label = when descr.name == "<child>" -> localize("<parent>"), ... else
descr.name; second line = when descr.name == "<child>" -> "(<host>)", ...
else "". All constructs (when-chains, string ==, localize(literal), ""
default) already occur in shipped UI files. If the game ignores the second
line, rows still work with raw keys (graceful fallback).

Idempotent: re-running yields 0 changes. Legacy reverts converge from any
older mod version to byte-identical stock (stamp stripped).
"""
import re

from ..headers import ACTIONS_PREFIX, YAML_PREFIX, normalize_text_header
from .constants import LEGACY_REVERT_FILES

TOGGLE_ACTION_BLOCK = (
    "\n"
    "action ON_TOGGLE_CHANGED\n"
    "{\n"
    "  ChangeData(preLoginData.showServersAsList, not preLoginData.showServersAsList);\n"
    "}\n"
)

# PreLogin.yaml: HelperButtons condition without the null-guard (as written
# by older mod versions) -> guarded stock form.
_UNGUARDED_MARK = ("NewGameNetEase or preLoginData.activePreLoginScreen"
                   " == ePreLoginScreen.NewGame or preLoginData.activePreLoginScreen"
                   " == ePreLoginScreen.Entry")


def _strip_stamp(lines, style):
    """Remove our own unified stamp line (legacy revert only)."""
    if lines and lines[0].strip().startswith(
            YAML_PREFIX if style == "yaml" else ACTIONS_PREFIX):
        return lines[1:], True
    return lines, False


def _region_blocks(lines):
    """Split the Regions: section into [(key, start, end)] (end exclusive)."""
    try:
        regions_idx = next(i for i, l in enumerate(lines) if l.strip() == "Regions:")
    except StopIteration:
        return []
    end_idx = len(lines)
    for i in range(regions_idx + 1, len(lines)):
        if lines[i] and not lines[i][0].isspace() and lines[i].strip().endswith(":"):
            end_idx = i
            break
    blocks = []
    for i in range(regions_idx + 1, end_idx):
        l = lines[i]
        if l.startswith("    ") and not l.startswith("     ") and l.rstrip().endswith(":"):
            blocks.append([l.strip()[:-1], i])
    for b in range(len(blocks)):
        blocks[b].append(blocks[b + 1][1] if b + 1 < len(blocks) else end_idx)
    return blocks


def _hosts_of(block):
    """[(host_key, [lines incl. sublines])] from a region block (may be [])."""
    hs = None
    for i, l in enumerate(block):
        if l.startswith("        ") and not l.startswith("         ") and l.strip() == "hosts:":
            hs = i
            break
    if hs is None:
        return []
    hosts = []
    i = hs + 1
    while i < len(block):
        l = block[i]
        if l.startswith("            ") and not l.startswith("             ") and l.rstrip().endswith(":"):
            hk = l.strip()[:-1]
            sub = [l]
            i += 1
            while i < len(block) and (block[i].startswith("                ") or not block[i].strip()):
                if block[i].strip():
                    sub.append(block[i])
                i += 1
            hosts.append((hk, sub))
            continue
        if l.startswith("        ") and not l.startswith("         ") and l.strip():
            break
        i += 1
    return hosts


# child_key -> (parent_key, host_key), built while expanding regions in this
# process. Feeds the row-template chains (main label + suffix line).
_ROW_INDEX = {}


def prime_row_index(game_path, project="wargaming"):
    """(Re)build the row index from Data regions + region cache (read-only).

    Lets the row template be generated after/without a regions-write pass.
    Never raises.
    """
    _ROW_INDEX.clear()
    try:
        import os
        from core.file_ops import read_physical
        from core.Mods.server_select.cache import find_region_cache_files
        cands = []
        for cand in (os.path.join(game_path, "Data", "regions_publish.yaml"),
                     os.path.join(game_path, "Data", "regions_publish.yaml.dvpl")):
            if os.path.isfile(cand):
                cands.append(cand)
        try:
            cands.extend(find_region_cache_files(game_path, project) or [])
        except Exception:
            pass
        for cand in cands:
            try:
                _expand_regions(read_physical(cand)["text"])
            except Exception:
                continue
    except Exception:
        pass


def _canonical_child(parent, host):
    return "%s %s" % (parent, host)


def _strip_numbers(lines, lo, hi):
    """Remove our ^NNN key prefixes inside [lo, hi). Returns (lines, n)."""
    out = []
    n = 0
    for i, l in enumerate(lines):
        if lo <= i < hi:
            m = re.match(r"^    \d{3} (.*)$", l)
            if m and m.group(1).rstrip().endswith(":"):
                out.append("    " + m.group(1))
                n += 1
                continue
        out.append(l)
    return out, n


def _expand_regions(text):
    """Cluster duplicates + sequential ^NNN ordering (sorting experiment).

    1. Strip previous numbering (idempotence across renumberings).
    2. Remove stale single-host copies; expand multi-host regions into
       "Parent Host" children (full parent copy, single host).
    3. Renumber ALL regions sequentially in file order ("001 Europe",
       "002 Europe EU_C0", ...). If the client sorts by key, the list follows
       file order in every language; the row/login templates hide the numbers
       from display, so a display-sort behaves exactly as before.
    _ROW_INDEX maps final key -> (orig_bare_key, host_or_None) for template
    and login chains (parents included so their numbers never render).
    Returns (new_text, added:int, removed:int, renamed:int).
    """
    lines = text.splitlines()
    blocks = _region_blocks(lines)
    if not blocks:
        return text, 0, 0, 0
    lines, _ = _strip_numbers(lines, blocks[0][1], blocks[-1][2])
    blocks = _region_blocks(lines)
    by_key = {k: (s, e) for k, s, e in blocks}
    hosts_by_key = {}
    for k, s, e in blocks:
        hosts_by_key[k] = _hosts_of(lines[s:e])

    def is_canonical(k):
        for p, (s, e) in by_key.items():
            for hk, _ in hosts_by_key.get(p, []):
                if len(hosts_by_key.get(p, [])) > 1 and k == _canonical_child(p, hk):
                    return True
        return False

    # Stale = single-host region whose host also lives in another region,
    # and which is not canonical (bare keys, "Parent_Host", Cyrillic keys).
    stale = set()
    for k, s, e in blocks:
        hosts = hosts_by_key.get(k, [])
        if len(hosts) != 1:
            continue
        if is_canonical(k):
            continue
        hk = hosts[0][0]
        elsewhere = any(hk in [h for h, _ in hosts_by_key.get(o, [])]
                        for o in by_key if o != k)
        if elsewhere:
            stale.add(k)

    added = 0
    created = {}  # bare child key -> (parent, host)
    kids_by_parent = {}  # parent key -> [child_lines]
    for key, s, e in blocks:
        if key in stale:
            continue
        block = [l for l in lines[s:e]]
        hosts = hosts_by_key.get(key, [])
        if len(hosts) < 2:
            continue
        for hk, sub in hosts:
            ck = _canonical_child(key, hk)
            if ck in by_key:
                continue  # already present — keep as-is
            created[ck] = (key, hk)
            child = []
            k = 0
            while k < len(block):
                l = block[k]
                if k == 0:
                    child.append("    %s:" % ck)
                    k += 1
                    continue
                if l.startswith("        ") and not l.startswith("         ") and l.strip() == "hosts:":
                    child.append(l)
                    child.append("            %s:" % hk)
                    for sl in sub[1:]:
                        child.append(sl)
                    k += 1
                    while k < len(block):
                        l2 = block[k]
                        if l2.startswith("            ") and not l2.startswith("             ") \
                                and l2.rstrip().endswith(":"):
                            k += 1
                            while k < len(block) and (block[k].startswith("                ")
                                                      or not block[k].strip()):
                                k += 1
                            continue
                        if l2.startswith("        ") and not l2.startswith("         ") and l2.strip():
                            break
                        child.append(l2)
                        k += 1
                    continue
                child.append(l)
                k += 1
            kids_by_parent.setdefault(key, []).append(child)
            added += 1
    removed = len(stale)
    # Drop stale blocks, then insert each parent's children right after it.
    stale_ranges = [(s, e) for k, s, e in blocks if k in stale]
    kept = [l for i, l in enumerate(lines)
            if not any(s <= i < e for s, e in stale_ranges)]
    kb = {k: (s, e) for k, s, e in _region_blocks(kept)}
    out = []
    for i, l in enumerate(kept):
        out.append(l)
        for k, (s, e) in kb.items():
            if e == i + 1 and k in kids_by_parent:
                for child in kids_by_parent[k]:
                    out.extend(child)
    # Renumber pass: every region gets ^NNN in file order. Stash maps the
    # final key -> (orig_bare_key, host_or_None); kept children resolve via
    # the multi-host map so reruns keep working without recreating them.
    blocks = _region_blocks(out)
    hosts_now = {}
    for k, s, e in blocks:
        hosts_now[k] = _hosts_of(out[s:e])
    multi_now = {k: [hk for hk, _ in hs] for k, hs in hosts_now.items()
                 if len(hs) > 1}
    seq = 0
    renamed = 0
    for k, s, e in blocks:
        seq += 1
        nkey = "%03d %s" % (seq, k)
        for i in range(s, e):
            if out[i].startswith("    ") and not out[i].startswith("     ") \
                    and out[i].rstrip().endswith(":"):
                if out[i].strip()[:-1] != nkey:
                    renamed += 1
                out[i] = "    %s:" % nkey
                break
        if k in created:
            _ROW_INDEX[nkey] = created[k]
            continue
        hs = hosts_now.get(k, [])
        hit = None
        if len(hs) == 1:
            for p, hks in multi_now.items():
                for hk in hks:
                    if k == p + " " + hk and hs[0][0] == hk:
                        hit = (p, hk)
                        break
                if hit:
                    break
        _ROW_INDEX[nkey] = hit if hit else (k, None)
    new_text = "\n".join(out)
    if new_text == text:
        return text, 0, 0, 0
    return new_text, added, removed, renamed


def _revert_legacy(text, filename):
    """Restore stock content of dev-button leftovers. Returns (text, changes, notes)."""
    notes = []
    changes = 0
    style = "actions" if filename.endswith(".actions") else "yaml"
    lines = text.splitlines()
    had_trailing_nl = text.endswith("\n")
    lines, stripped = _strip_stamp(lines, style)
    if stripped:
        changes += 1
        notes.append("stamp removed")
    if filename.endswith("HelperButtons.yaml"):
        out = []
        for line in lines:
            if '["visible", "true"]' in line:
                line = line.replace('["visible", "true"]',
                                    '["visible", "devButtonsData.isChooseClusterAvailable"]')
                changes += 1
                notes.append("cluster button gate restored")
            out.append(line)
        lines = out
    elif filename.endswith("PreLogin.yaml"):
        out = []
        for line in lines:
            if "condition:" in line and "(not isNull(devButtonsData))" not in line \
                    and _UNGUARDED_MARK in line:
                line = line.replace('"(preLoginData.activePreLoginScreen',
                                    '"(not isNull(devButtonsData)) and (preLoginData.activePreLoginScreen')
                changes += 1
                notes.append("devButtonsData guard restored")
            out.append(line)
        lines = out
    elif filename.endswith("PreLogin.actions"):
        body = "\n".join(lines)
        if TOGGLE_ACTION_BLOCK in body:
            body = body.replace(TOGGLE_ACTION_BLOCK, "\n")
            changes += 1
            notes.append("dead toggle action removed")
        lines = body.split("\n")
    new_text = "\n".join(lines)
    if had_trailing_nl and not new_text.endswith("\n"):
        new_text += "\n"
    return new_text, changes, notes


def _esc(s):
    return s.replace('"', '\\"')


def _login_chains(source, wrap_localize):
    """(main, sub) when-chains over a region-name source expression.

    main maps every known cluster key to localize("<parent>") with the stock
    expression as else (wrap_localize=True keeps the localize() call around
    the else, like the ServerLink key arg; False keeps it bare, like the
    LastServer text). sub maps cluster keys to "(<host>)" with else "".
    Returns None when the row index is empty (nothing to map).
    """
    pairs = sorted(_ROW_INDEX.items())
    hosts_only = [(c, p, h) for c, (p, h) in pairs if h is not None]
    if not hosts_only:
        return None
    else_main = "localize(%s)" % source if wrap_localize else source
    main = "when " + ", ".join(
        '%s == \\"%s\\" -> localize(\\"%s\\")' % (source, _esc(c), _esc(p))
        for c, (p, h) in pairs) + ", " + else_main
    sub = "when " + ", ".join(
        '%s == \\"%s\\" -> \\"(%s)\\"' % (source, _esc(c), _esc(h))
        for c, p, h in hosts_only) + ', \\"\\"'
    return main, sub


def _suffix_block(dash_indent, marker, classes, chain):
    """Minimal label control lines (blank-line style like shipped files)."""
    j = dash_indent + "    "
    return [
        dash_indent + '-   class: "UIControl"',
        "",
        j + 'name: "%s"' % marker,
        "",
        j + 'input: false',
        "",
        j + 'classes: "%s"' % classes,
        "",
        j + 'components:',
        "",
        j + '    UITextComponent: {}',
        "",
        j + '    SizePolicy:',
        "",
        j + '        horizontalPolicy: "PercentOfContent"',
        "",
        j + '        verticalPolicy: "PercentOfContent"',
        "",
        j + '    StyleSheet:',
        "",
        j + '        styles: "~res:/UI/Screens3/Font.style.yaml"',
        "",
        j + 'bindings:',
        "",
        j + '- ["UITextComponent.text", "%s"]' % chain,
    ]


def _block_bounds(lines, name_idx):
    """(start, end) of the '-   class:' item containing lines[name_idx]."""
    start = name_idx
    while start > 0 and not lines[start].lstrip().startswith("-   class:"):
        start -= 1
    indent = lines[start][:len(lines[start]) - len(lines[start].lstrip())]
    end = start + 1
    while end < len(lines):
        l = lines[end]
        if l.lstrip().startswith("-   class:"):
            cur = l[:len(l) - len(l.lstrip())]
            if len(cur) <= len(indent):
                break
        end += 1
    return start, end, indent


def _login_screens(text, is_entry):
    """Localize selected-region display on login screens.

    ServerLink key arg: cluster keys -> localize(parent), else stock.
    Suffix siblings after ServerLink (+ LastServer on Entry): "(host)"/"".
    Returns (new_text, changes, notes).
    """
    notes = []
    changes = 0
    lines = text.splitlines()
    had_trailing_nl = text.endswith("\n")

    key_mark = "when preLoginData.currentRegion.name =="
    key_stock = '"key": "localize(preLoginData.currentRegion.name)"'
    last_mark = "when preLoginData.lastLogin.region =="
    last_stock = '- ["UITextComponent.text", "preLoginData.lastLogin.region"]'

    ch = _login_chains("preLoginData.currentRegion.name", True)
    ch_last = _login_chains("preLoginData.lastLogin.region", False)
    if ch is None:
        return text, 0, ["no cluster index, login screens untouched"]
    main_link, sub_link = ch
    main_last, sub_last = ch_last

    out = list(lines)
    # 1. ServerLink key arg (rebuild when already chained).
    for i, l in enumerate(out):
        s = l.strip()
        if s.startswith('"key":') and (key_mark in s or key_stock in s):
            pre = l[:len(l) - len(l.lstrip())]
            out[i] = pre + '"key": "%s"' % main_link
            if out[i] != l:
                changes += 1
                notes.append("server link localized")
            break
    # 2. Suffix sibling after ServerLink (rebuild its binding if present).
    idx = next((i for i, l in enumerate(out) if l.strip() == 'name: "ServerLink"'), None)
    midx = next((i for i, l in enumerate(out) if l.strip() == 'name: "ServerClusterSuffix"'), None)
    if idx is not None and midx is None:
        _, end, indent = _block_bounds(out, idx)
        # insert before the next sibling (end) — same indent as ServerLink
        sib = _suffix_block(indent, "ServerClusterSuffix",
                            "t-body regular white-wild-sand-50-text", sub_link)
        out[end:end] = sib
        changes += 1
        notes.append("server suffix added")
    elif midx is not None:
        start, end, _ = _block_bounds(out, midx)
        for i in range(start, end):
            if out[i].strip().startswith('- ["UITextComponent.text",'):
                pre = out[i][:len(out[i]) - len(out[i].lstrip())]
                nl = pre + '- ["UITextComponent.text", "%s"]' % sub_link
                if nl != out[i]:
                    out[i] = nl
                    changes += 1
                    notes.append("server suffix rebuilt")
                break
    if is_entry:
        # 3. LastServer text.
        for i, l in enumerate(out):
            s = l.strip()
            if s == last_stock or (s.startswith('- ["UITextComponent.text",') and last_mark in s):
                pre = l[:len(l) - len(l.lstrip())]
                nl = pre + '- ["UITextComponent.text", "%s"]' % main_last
                if nl != l:
                    out[i] = nl
                    changes += 1
                    notes.append("last server localized")
                break
        # 4. Suffix sibling after LastServer (rebuild its binding if present).
        idx = next((i for i, l in enumerate(out) if l.strip() == 'name: "LastServer"'), None)
        midx = next((i for i, l in enumerate(out) if l.strip() == 'name: "LastClusterSuffix"'), None)
        if idx is not None and midx is None:
            _, end, indent = _block_bounds(out, idx)
            sib = _suffix_block(indent, "LastClusterSuffix",
                                "t-caption regular white-wild-sand-50-text", sub_last)
            out[end:end] = sib
            changes += 1
            notes.append("last server suffix added")
        elif midx is not None:
            start, end, _ = _block_bounds(out, midx)
            for i in range(start, end):
                if out[i].strip().startswith('- ["UITextComponent.text",'):
                    pre = out[i][:len(out[i]) - len(out[i].lstrip())]
                    nl = pre + '- ["UITextComponent.text", "%s"]' % sub_last
                    if nl != out[i]:
                        out[i] = nl
                        changes += 1
                        notes.append("last server suffix rebuilt")
                    break
    new_text = "\n".join(out)
    if had_trailing_nl and not new_text.endswith("\n"):
        new_text += "\n"
    return new_text, changes, notes


def _row_template(text):
    """Insert a cluster-suffix second line into the server list row.

    NameCol (vertical) replaces Label: main label text = when-chain mapping
    every known cluster key to localize("<parent>") with else descr.name
    (stock rows untouched); ClusterLine text = when-chain mapping cluster
    keys to "(<host>)" with else "" (empty on stock rows). Root row height
    48 -> 64. Chains come from _ROW_INDEX (prime_row_index first).
    Returns (new_text, changes, notes).
    """
    notes = []
    changes = 0
    lines = text.splitlines()
    had_trailing_nl = text.endswith("\n")

    pairs = sorted(_ROW_INDEX.items())
    hosts_only = [(c, p, h) for c, (p, h) in pairs if h is not None]
    main_chain = "when " + ", ".join(
        'descr.name == \\"%s\\" -> localize(\\"%s\\")' % (_esc(c), _esc(p))
        for c, (p, h) in pairs) + (", " if pairs else "") + "descr.name"
    sub_chain = "when " + ", ".join(
        'descr.name == \\"%s\\" -> \\"(%s)\\"' % (_esc(c), _esc(h))
        for c, p, h in hosts_only) + (", " if hosts_only else "") + '\\"\\"'
    main_line = '- ["UITextComponent.text", "%s"]' % main_chain
    sub_line = '- ["UITextComponent.text", "%s"]' % sub_chain

    # Root row height 48 -> 64 (sole 48px box in the stock template; Label
    # keeps 32, ClusterLine takes 20 + 2 spacing).
    height_hits = sum(l.count('verticalValue: 48.000000') for l in lines)
    if height_hits:
        lines = [l.replace('verticalValue: 48.000000', 'verticalValue: 64.000000')
                 for l in lines]
        changes += height_hits
        notes.append("row height 48 -> 64")
    # Locate Label block: its '-   class:' line back from 'name: "Label"',
    # or the existing NameCol block for rebuilds.
    idx_label = next((i for i, l in enumerate(lines) if l.strip() == 'name: "Label"'), None)
    idx_namecol = next((i for i, l in enumerate(lines) if l.strip() == 'name: "NameCol"'), None)
    idx_flag = next((i for i, l in enumerate(lines) if l.strip() == 'name: "Flag"'), None)
    if (idx_label is None and idx_namecol is None) or idx_flag is None:
        return text, 0, ["row template structure not recognized"]
    if idx_namecol is not None:
        # Rebuild: NameCol '-   class:' line back from its name line.
        start = idx_namecol
        while start > 0 and not lines[start].lstrip().startswith("-   class:"):
            start -= 1
    else:
        start = idx_label
        while start > 0 and not lines[start].lstrip().startswith("-   class:"):
            start -= 1
    # Flag block start similarly back from its name line.
    end = idx_flag
    while end > 0 and not lines[end].lstrip().startswith("-   class:"):
        end -= 1
    # Original Label block (for structure copy): from a stock file take the
    # Label block verbatim (8sp-based); NameCol children sit one level deeper
    # (+4 on emit). On rebuilds derive it from the inner Label child.
    label_block = None
    if idx_namecol is None:
        label_block = list(lines[start:end])
    else:
        # Rebuild path: reconstruct stock Label block from current NameCol by
        # taking the inner Label child (name "Label") out of it.
        inner = []
        j = next((k for k, l in enumerate(lines[start:end])
                  if l.strip() == 'name: "Label"'), None)
        if j is None:
            return text, 0, ["NameCol without Label"]
        k = j
        while k > 0 and not lines[start:end][k].lstrip().startswith("-   class:"):
            k -= 1
        m = k + 1
        # inner Label child ends before ClusterLine '-' or NameCol end
        while m < len(lines[start:end]) and not (
                lines[start:end][m].lstrip().startswith("-   class:")
                and m != k):
            m += 1
        inner = lines[start:end][k:m]
        # de-indent one level (12sp->8sp) to recover stock shape
        label_block = [l[4:] if l.startswith("    ") else l for l in inner]
        # restore stock binding (will be re-chained below)
        label_block = [re.sub(r'^(\s*)- \["UITextComponent\.text", ".*"\]$',
                              r'\1- ["UITextComponent.text", "descr.name"]', l)
                       for l in label_block]
    # Height tally (root 48->64 done above only when marker fresh; recompute)
    before_struct = "\n".join(lines)
    out_lines = lines[:start]
    # NameCol header (item at 8sp like its Content siblings, name at 12sp)
    out_lines.append('        -   class: "UIControl"')
    out_lines.append("")
    out_lines.append('            name: "NameCol"')
    out_lines.append("")
    out_lines.append('            input: false')
    out_lines.append("")
    out_lines.append('            components:')
    out_lines.append("")
    out_lines.append('                LinearLayout:')
    out_lines.append("")
    out_lines.append('                    orientation: "TopDown"')
    out_lines.append("")
    out_lines.append('                    spacing: 2.000000')
    out_lines.append("")
    out_lines.append('                SizePolicy:')
    out_lines.append("")
    out_lines.append('                    horizontalPolicy: "FixedSize"')
    out_lines.append("")
    out_lines.append('                    horizontalValue: 256.000000')
    out_lines.append("")
    out_lines.append('                    verticalPolicy: "PercentOfChildrenSum"')
    out_lines.append("")
    out_lines.append('            children:')
    out_lines.append("")
    for src_name, dst_name, chain, classes, vsize in (
            ("Label", "Label", main_line, None, None),
            ("Label", "ClusterLine", sub_line,
             "t-body regular white-wild-sand-50-text", "20.000000")):
        for l in label_block:
            nl = "    " + l
            if dst_name == "ClusterLine":
                if l.strip() == 'name: "Label"':
                    nl = nl.replace('name: "Label"', 'name: "ClusterLine"')
                elif 'classes:' in l and classes:
                    nl = re.sub(r'classes: ".*"', 'classes: "%s"' % classes, nl)
                elif 'verticalValue: 32.000000' in l and vsize:
                    nl = nl.replace('verticalValue: 32.000000',
                                    'verticalValue: %s' % vsize)
            if l.strip().startswith('- ["UITextComponent.text",'):
                # preserve indent, swap binding (both copies get own chain)
                pre = nl[:len(nl) - len(nl.lstrip())]
                nl = pre + (main_line if dst_name == "Label" else sub_line)
            out_lines.append(nl)
    out_lines.extend(lines[end:])
    new_text = "\n".join(out_lines)
    if new_text != before_struct:
        changes += 1
        notes.append("cluster second line rebuilt" if idx_namecol is not None
                     else "cluster second line added")
    if had_trailing_nl and not new_text.endswith("\n"):
        new_text += "\n"
    return new_text, changes, notes


def modify_server_select_text(text, filename=""):
    """Apply ServersClusterSelector transforms. Returns (new_text, changes, notes)."""
    notes = []
    changes = 0
    name = (filename or "").replace("\\", "/")

    if any(name.endswith(r) for r in LEGACY_REVERT_FILES):
        return _revert_legacy(text, name)

    if name.endswith("Entry.yaml") or name.endswith("NewGame.yaml"):
        lines = text.splitlines()
        had_trailing_nl = text.endswith("\n")
        lines, header_changed = normalize_text_header(lines, "yaml", [])
        if header_changed:
            changes += 1
            notes.append("header added")
        new_text, ch2, notes2 = _login_screens(
            "\n".join(lines), is_entry=name.endswith("Entry.yaml"))
        changes += ch2
        notes.extend(notes2)
        new_text = new_text if new_text.endswith("\n") or not had_trailing_nl else new_text + "\n"
        return new_text, changes, notes

    if name.endswith(".actions"):
        lines = text.splitlines()
        had_trailing_nl = text.endswith("\n")
        lines, header_changed = normalize_text_header(lines, "actions", [])
        if header_changed:
            changes += 1
            notes.append("header added")
        new_text = "\n".join(lines)
        if had_trailing_nl and not new_text.endswith("\n"):
            new_text += "\n"
        return new_text, changes, notes

    base = name.rsplit("/", 1)[-1]
    if base == "regions_publish.yaml" or (base.startswith("regions_") and base.endswith(".yaml")):
        lines = text.splitlines()
        had_trailing_nl = text.endswith("\n")
        lines, header_changed = normalize_text_header(lines, "yaml", [])
        if header_changed:
            changes += 1
            notes.append("header added")
        body = "\n".join(lines)
        body, added, removed, renamed = _expand_regions(body)
        if added:
            changes += added
            notes.append("cluster regions added: %d" % added)
        if removed:
            changes += removed
            notes.append("stale cluster regions removed: %d" % removed)
        if renamed:
            changes += renamed
            notes.append("regions renumbered: %d" % renamed)
        new_text = body
        if had_trailing_nl and not new_text.endswith("\n"):
            new_text += "\n"
        return new_text, changes, notes

    if name.endswith("ServerDescriptionPrototype.yaml"):
        lines = text.splitlines()
        had_trailing_nl = text.endswith("\n")
        lines, header_changed = normalize_text_header(lines, "yaml", [])
        if header_changed:
            changes += 1
            notes.append("header added")
        new_text, ch2, notes2 = _row_template("\n".join(lines))
        changes += ch2
        notes.extend(notes2)
        new_text = new_text if new_text.endswith("\n") or not had_trailing_nl else new_text + "\n"
        return new_text, changes, notes

    # UI yaml files (ServerSelection.yaml: hide dead toggle, force list).
    lines = text.splitlines()
    had_trailing_nl = text.endswith("\n")
    lines, header_changed = normalize_text_header(lines, "yaml", [])
    if header_changed:
        changes += 1
        notes.append("header added")

    out = []
    current = ""
    for line in lines:
        m = re.search(r'name:\s*"([^"]+)"', line)
        if m:
            current = m.group(1)
        if name.endswith("ServerSelection.yaml"):
            if "preLoginData.showListToggleButton" in line:
                n = line.count("preLoginData.showListToggleButton")
                line = line.replace("preLoginData.showListToggleButton", "false")
                changes += n
            elif current == "ToggleViewButton":
                if 'condition: "true"' in line:
                    line = line.replace('condition: "true"', 'condition: "false"')
                    changes += 1
                    notes.append("toggle condition hidden")
                elif '["visible", "true"]' in line:
                    line = line.replace('["visible", "true"]', '["visible", "false"]')
                    changes += 1
                    notes.append("toggle hidden")
                elif '["UILayerComponent.layer", "true"]' in line:
                    line = line.replace('["UILayerComponent.layer", "true"]',
                                        '["UILayerComponent.layer", "false"]')
                    changes += 1
                    notes.append("toggle layer hidden")
            if "preLoginData.showServersAsList" in line:
                n = line.count("preLoginData.showServersAsList")
                line = line.replace("preLoginData.showServersAsList", "true")
                changes += n
            # Search field: NUMBER_LETTER blocks non-English input and the
            # ASCII-capable keyboard hides other layouts. Drop the filter
            # (default = free text) and use the default keyboard so names can
            # be typed in any language. Whether non-English queries MATCH
            # depends on the C++ side (keys vs displayed names) — game test.
            if line.strip() == '"filterRegExp": "NUMBER_LETTER"':
                changes += 1
                notes.append("search input filter removed")
                continue
            if line.strip() == '"keyboardType": "eKeyboardType.KEYBOARD_TYPE_ASCII_CAPABLE"':
                line = line.replace("KEYBOARD_TYPE_ASCII_CAPABLE", "KEYBOARD_TYPE_DEFAULT")
                changes += 1
                notes.append("search keyboard opened")
        out.append(line)

    new_text = "\n".join(out)
    if had_trailing_nl:
        new_text += "\n"
    return new_text, changes, notes


def describe_server_select_patch(filename, changes):
    return f"{filename}: {changes} edit(s)"
