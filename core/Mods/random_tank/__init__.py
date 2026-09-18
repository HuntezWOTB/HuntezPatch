"""RandomTankSelector mod package: public API re-export + dispatcher."""
from .actions_patch import modify_actions_text
from .constants import (
    ACTIONS_REL, ICON_2X_REL, ICON_BASE_REL, ICON_RELS, ICON_RES_PATH,
    RANDOMTANK_FILES, YAML_REL,
)
from .icon import make_icon_payloads, render_dice_icon
from .yaml_patch import modify_yaml_text

__all__ = [
    'RANDOMTANK_FILES', 'YAML_REL', 'ACTIONS_REL',
    'ICON_BASE_REL', 'ICON_2X_REL', 'ICON_RELS', 'ICON_RES_PATH',
    'modify_yaml_text', 'modify_actions_text', 'modify_randomtank_text',
    'make_icon_payloads', 'render_dice_icon', 'describe_randomtank_patch',
]


def modify_randomtank_text(text, filename=""):
    """Dispatch by file type. Returns (new_text, changes, notes)."""
    if filename.endswith(".actions") or filename.endswith(".actions.dvpl"):
        return modify_actions_text(text, filename)
    return modify_yaml_text(text, filename)


def describe_randomtank_patch(filename, changes):
    return f"{filename}: {changes} edit(s)"
