"""RandomTankSelector operation: insert the action into TanksPanel.actions."""
from ..headers import normalize_text_header
from .constants import ACTION_BLOCK, READY_GUARD, _RE_ACTION_NEXT, _RE_ACTION_SELF


def _replace_existing_action(lines):
    """Replace an existing v1.01 SELECT_RANDOM_TANK block with the guarded one.

    Returns (lines, replaced: bool). Brace-matched so the whole old block
    is swapped, not just prepended to.
    """
    start = next((i for i, ln in enumerate(lines) if _RE_ACTION_SELF.match(ln)), None)
    if start is None:
        return lines, False
    depth = 0
    end = None
    for i in range(start, len(lines)):
        depth += lines[i].count("{") - lines[i].count("}")
        if i > start and depth <= 0:
            end = i
            break
    if end is None:
        return lines, False
    block = ACTION_BLOCK.rstrip("\n").split("\n")
    return lines[:start] + block + lines[end + 1:], True


def modify_actions_text(text, filename=""):
    """Insert the SELECT_RANDOM_TANK action. Returns (new_text, changes, notes)."""
    notes = []
    changes = 0
    lines = text.splitlines()
    had_trailing_nl = text.endswith("\n")

    lines, header_changed = normalize_text_header(lines, "actions", [])
    if header_changed:
        changes += 1
        notes.append("header added")

    if any(_RE_ACTION_SELF.match(ln) for ln in lines):
        # Upgrade path v1.01 -> v1.02: old action has no ready-guard and
        # would still switch tanks while READY. Swap it (idempotent).
        if READY_GUARD not in text:
            lines, replaced = _replace_existing_action(lines)
            if replaced:
                changes += 1
                notes.append("SELECT_RANDOM_TANK upgraded with ready-guard")
        new_text = "\n".join(lines) + ("\n" if had_trailing_nl else "")
        return new_text, changes, notes

    anchor_idx = None
    for i, ln in enumerate(lines):
        if _RE_ACTION_NEXT.match(ln):
            anchor_idx = i
            break

    if anchor_idx is None:
        notes.append("SELECT_NEXT_TANK anchor not found, action not inserted")
        new_text = "\n".join(lines) + ("\n" if had_trailing_nl else "")
        return new_text, changes, notes

    block = ACTION_BLOCK.rstrip("\n").split("\n")
    lines[anchor_idx:anchor_idx] = block + [""]
    changes += 1
    notes.append("SELECT_RANDOM_TANK inserted")
    new_text = "\n".join(lines) + ("\n" if had_trailing_nl else "")
    return new_text, changes, notes
