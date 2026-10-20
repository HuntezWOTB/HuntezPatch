"""TanksStatistics operation: stats column + mastery badge in OwnedTankCell.

WG gets the proven StatisticsHolder block plus the MasteryBadge (highest
earned mark of mastery right of the level badge). Lesta gets the TankStats
block plus its own MasteryBadge variant (Lesta-tuned offsets, inserted
before the TankStats column). Only the base indent is adapted at runtime;
inner lines are byte-exact. Line endings (CRLF on Lesta) are preserved.
"""
from ..headers import normalize_text_header
from .constants import (TANKSTATS_BLOCK, TANKSTATS_ANCHOR,
                        tankstats_block_for_project, MASTERY_BLOCK,
                        MASTERY_VARS, MASTERY_ANCHOR, MASTERY_VARS_ANCHOR,
                        MASTERY_BLOCK_LESTA, MASTERY_VARS_LESTA)


def _find_stats_anchor(lines, project):
    """Return the item start line index for the stats anchor control."""
    want = 'name: "%s"' % TANKSTATS_ANCHOR
    if (project or "wargaming").lower() == "lesta":
        # Lesta nests TankInfo twice: pick the shallowest item whose block
        # contains the NameContainer (the info cluster the column aligns
        # to as a sibling); on indent ties the later (inner) item wins.
        best = None
        for i, line in enumerate(lines):
            if line.strip() != want:
                continue
            start = i
            while start > 0 and not lines[start].lstrip().startswith('-   class:'):
                start -= 1
            indent = lines[start][:len(lines[start]) - len(lines[start].lstrip())]
            end = start + 1
            while end < len(lines):
                cur_line = lines[end]
                if cur_line.lstrip().startswith('-   class:'):
                    cur = cur_line[:len(cur_line) - len(cur_line.lstrip())]
                    if len(cur) <= len(indent):
                        break
                end += 1
            if any('name: "NameContainer"' in cur_line for cur_line in lines[start:end]):
                if best is None or len(indent) <= len(best[1]):
                    best = (start, indent)
        if best is not None:
            return best[0]
        return None
    idx = next((i for i, l in enumerate(lines) if l.strip() == want), None)
    if idx is None:
        return None
    start = idx
    while start > 0 and not lines[start].lstrip().startswith('-   class:'):
        start -= 1
    return start


def _insert_mastery(lines, notes, project="wargaming"):
    """Insert mastery vars + badge (per-project values). Returns (lines, changes)."""
    changes = 0
    is_lesta = (project or "wargaming").lower() == "lesta"
    if any('name: "MasteryBadge"' in ln for ln in lines):
        return lines, changes
    mvars = MASTERY_VARS_LESTA if is_lesta else MASTERY_VARS
    mblock = MASTERY_BLOCK_LESTA if is_lesta else MASTERY_BLOCK
    # Lesta badge goes right before the TankStats column (same parent);
    # WG badge goes right after the VehicleInfo item.
    anchor_name = 'name: "TankStats"' if is_lesta else 'name: "%s"' % MASTERY_ANCHOR
    var_anchor = next((i for i, l in enumerate(lines)
                       if MASTERY_VARS_ANCHOR in l and l.strip().startswith('- [')), None)
    badge_idx = next((i for i, l in enumerate(lines)
                      if l.strip() == anchor_name), None)
    if var_anchor is None or badge_idx is None:
        notes.append("mastery anchors not found, badge not inserted")
        return lines, changes
    vind = lines[var_anchor][:len(lines[var_anchor]) - len(lines[var_anchor].lstrip())]
    lines[var_anchor + 1:var_anchor + 1] = [vind + l if l.strip() else l
                                            for l in mvars]
    changes += 1
    notes.append("mastery vars inserted")
    badge_idx = next(i for i, l in enumerate(lines)
                     if l.strip() == anchor_name)
    start = badge_idx
    while start > 0 and not lines[start].lstrip().startswith('-'):
        start -= 1
    indent = lines[start][:len(lines[start]) - len(lines[start].lstrip())]
    if is_lesta:
        at = start
    else:
        end = start + 1
        while end < len(lines):
            cur_line = lines[end]
            if cur_line.strip().startswith('-') and \
                    (len(cur_line) - len(cur_line.lstrip()) <= len(indent)):
                break
            end += 1
        at = end
    lines[at:at] = [indent + l if l.strip() else l for l in mblock]
    changes += 1
    notes.append("MasteryBadge inserted")
    return lines, changes


def modify_tankstats_text(text, filename="", project="wargaming"):
    """Insert the stats column plus the mastery badge.

    Returns (new_text, changes, notes).
    """
    notes = []
    changes = 0
    is_lesta = (project or "wargaming").lower() == "lesta"
    sep = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(sep)
    had_trailing_nl = text.endswith("\n")
    if had_trailing_nl and lines and lines[-1] == "":
        lines.pop()

    lines, header_changed = normalize_text_header(lines, "yaml", [])
    if header_changed:
        changes += 1
        notes.append("header added")

    block = tankstats_block_for_project(project)
    block_name = 'name: "TankStats"' if is_lesta else 'name: "StatisticsHolder"'
    if not any(block_name in ln for ln in lines):
        start = _find_stats_anchor(lines, project)
        if start is None:
            notes.append("%s anchor not found, stats not inserted" % TANKSTATS_ANCHOR)
        else:
            indent = lines[start][:len(lines[start]) - len(lines[start].lstrip())]
            lines[start:start] = [indent + l if l.strip() else l for l in block]
            changes += 1
            notes.append("TankStats column inserted")

    lines, mastery_changes = _insert_mastery(lines, notes, project)
    changes += mastery_changes

    new_text = sep.join(lines) + (sep if had_trailing_nl else "")
    return new_text, changes, notes


def describe_tankstats_patch(filename, changes):
    return f"{filename}: {changes} edit(s)"
