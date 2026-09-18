"""RandomTankSelector operation: insert the action into TanksPanel.actions."""
from ..headers import normalize_text_header
from .constants import ACTION_BLOCK, _RE_ACTION_NEXT, _RE_ACTION_SELF


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
