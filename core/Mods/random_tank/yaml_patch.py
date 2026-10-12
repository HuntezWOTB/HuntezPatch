"""RandomTankSelector operation: insert the button into TanksPanel.yaml."""
from ..headers import normalize_text_header
from .constants import (
    YAML_BUTTON_BLOCK, ENABLED_EXPR, READY_GUARD,
    _RE_YAML_CLASS, _RE_YAML_FILTER_NAME,
)

OLD_ENABLED_LINE = '"enabled": "tanks.Size() > 1"'


def modify_yaml_text(text, filename=""):
    """Insert the random-tank button. Returns (new_text, changes, notes)."""
    notes = []
    changes = 0
    lines = text.splitlines()
    had_trailing_nl = text.endswith("\n")

    lines, header_changed = normalize_text_header(lines, "yaml", [])
    if header_changed:
        changes += 1
        notes.append("header added")

    if any('name: "RandomTankButtonHolder"' in ln for ln in lines):
        # Upgrade path v1.01 -> v1.02: old installs only check
        # tanks.Size() > 1, so the dice stays clickable while READY.
        # Replace with the ready-guard expression (idempotent).
        if READY_GUARD not in text and any(OLD_ENABLED_LINE in ln for ln in lines):
            lines = [ln.replace(OLD_ENABLED_LINE, '"enabled": "' + ENABLED_EXPR + '"')
                     for ln in lines]
            changes += 1
            notes.append("RandomTankButton enabled upgraded with ready-guard")
        new_text = "\n".join(lines) + ("\n" if had_trailing_nl else "")
        return new_text, changes, notes

    anchor_idx = None
    for i, ln in enumerate(lines):
        if _RE_YAML_CLASS.match(ln):
            for j in range(i + 1, min(i + 4, len(lines))):
                if _RE_YAML_FILTER_NAME.match(lines[j]):
                    anchor_idx = i
                    break
                if lines[j].strip() == '' or _RE_YAML_CLASS.match(lines[j]):
                    break
            if anchor_idx is not None:
                break

    if anchor_idx is None:
        notes.append("Filter anchor not found, button not inserted")
        new_text = "\n".join(lines) + ("\n" if had_trailing_nl else "")
        return new_text, changes, notes

    block = YAML_BUTTON_BLOCK.rstrip("\n").split("\n")
    lines[anchor_idx:anchor_idx] = block
    changes += 1
    notes.append("RandomTankButtonHolder inserted")
    new_text = "\n".join(lines) + ("\n" if had_trailing_nl else "")
    return new_text, changes, notes
