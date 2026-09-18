"""Content-based MODIFIED detection (no registry file).

A file counts as MODIFIED when it carries one of our generator signatures.
Every mod stamps its output with the unified "#HuntezPatch - Generated: ..."
line (plus a per-mod identity line), so no sidecar state is needed.
Restore puts originals (without signatures) back, so marks clear by itself.
"""
import os

from core.file_ops import read_physical

MOD_SIGNATURES = ("HuntezPatch - Generated",)
_HEAD_CHARS = 1000


def _norm(path):
    try:
        return os.path.normcase(os.path.abspath(path))
    except Exception:
        return path


def has_mod_signature(path):
    """True when a physical file contains a generator signature."""
    try:
        if not path or not os.path.isfile(path):
            return False
        info = read_physical(path)
        head = (info.get('text') or '')[:_HEAD_CHARS]
        return any(sig in head for sig in MOD_SIGNATURES)
    except Exception:
        return False


def get_modified_files(game_path, mod_ids, dlc_root):
    """Full normalized paths of modded files (game plain/.dvpl + DLC .dvpl)."""
    from core import orchestrator as _orc
    found = set()
    if not game_path:
        return found
    for mid in (mod_ids or []):
        try:
            rels = _orc.mod_rel_paths(mid)
        except Exception:
            continue
        for rel in rels:
            for cand in (os.path.join(game_path, "Data", rel),
                         os.path.join(game_path, "Data", rel) + ".dvpl"):
                try:
                    if os.path.isfile(cand) and has_mod_signature(cand):
                        found.add(_norm(cand))
                except Exception:
                    continue
            if dlc_root:
                dlc_cand = os.path.join(dlc_root, rel) + ".dvpl"
                try:
                    if os.path.isfile(dlc_cand) and has_mod_signature(dlc_cand):
                        found.add(_norm(dlc_cand))
                except Exception:
                    continue
    return found
