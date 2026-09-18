"""AutoRanksOFF constants: target files, rank tokens, header, patterns."""
import re

AUTORANKS_FILES = [
    "UI/Screens3/Lobby/Hangar/Hangar.yaml",
    "UI/Screens3/Lobby/Hangar/Squad/SquadView.yaml",
    "UI/Screens3/Lobby/Inventory/Inventory.yaml",
    "UI/Screens3/Lobby/Inventory/TankProgress/AchievementsTab.yaml",
]

RANK_TOKENS = ("UnlockRank", "UnlockFirstRank", "FirstRankSoundPlayed", "OnPromoRankInfoClicked")

_RE_BINDING = re.compile(r'\[\s*(["\'])visible\1\s*,\s*(["\'])not rankUnlockRequired\2\s*\]')
_RE_ARG_PASS = re.compile(r'^\s*"rankUnlockRequired"\s*:\s*"rankUnlockRequired"\s*$')
_RE_PARAM_BOOL_FALSE = re.compile(r'^\s*-\s*\["bool",\s*"rankUnlockRequired",\s*"false",\s*"false"\]\s*$')
_RE_EVENT_LINE = re.compile(r'^\s*-\s*["\'](UnlockRank|OnPromoRankInfoClicked)["\']\s*$')
_RE_ITEM_LINE = re.compile(r'^(\s*-\s*)\[(.*)\]\s*$')
_RE_EVENT_ACTIONS_KEY = re.compile(r'^\s*eventActions:\s*$')
