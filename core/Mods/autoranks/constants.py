"""AutoRanksOFF constants: target files, rank tokens, header, patterns.

WoT Blitz (Wargaming) and Tanks Blitz (Lesta) use separate structures:
Lesta has no ``rankUnlockRequired`` gating at all. Lesta v3 keeps the
Rank TAB visible but makes rank unobtainable (WG parity): every UI event
path to the native grant is cut, the auto-fire is killed, the fanfare is
stripped. See patch.py (WG) and patch_lesta.py (Lesta).
"""
import re

AUTORANKS_FILES = [
    "UI/Screens3/Lobby/Hangar/Hangar.yaml",
    "UI/Screens3/Lobby/Hangar/Squad/SquadView.yaml",
    "UI/Screens3/Lobby/Inventory/Inventory.yaml",
    "UI/Screens3/Lobby/Inventory/TankProgress/AchievementsTab.yaml",
]

# WG (Wargaming) file list — identical paths, kept as an alias so the
# orchestrator can pick the structure per project.
AUTORANKS_FILES_WG = list(AUTORANKS_FILES)

# Lesta file list (v5): 4 yaml + ceremony script + 2 init animations
# + 2 rank notification popups.
# Rationale (Tanks Blitz client has no rankUnlockRequired gating at all):
#   * Hangar.yaml — ranksAvailable -> false kills ONLY the hangar
#     counters/teaser + its sounds. The depot Rank TAB lives in
#     Inventory.yaml (own definition) and stays.
#   * AchievementsTab.yaml / Inventory.yaml — remove ONLY the promo popup
#     plumbing (OnPromoRankInfoClicked). needsUnlock/showRank, avaibleRank
#     aside (FX off), and every manual button
#     (UnlockFirstRank / UnlockRank / UnlockNextRank + forwarders) stay
#     byte-identical: the screen renders like vanilla, the GET RANK button
#     works. currentTankRank stays truthful.
#   * AchievementsTab.actions — strip the fanfare (sound/flash/fade) from
#     the AnimateRankUnlock ceremony, keep the state transition.
#   * *Initialization.animation (NotEliteTankPanel + TankRank) — remove the
#     auto-fired Event("UnlockFirstRank") lines. These two lines ARE the
#     auto-grant. With them gone, the grant happens only on button click.
#   * TankRankAvailableNotification.yaml / TankRanksUnlockedNotification.yaml
#     (UI/Screens/.../Popups) — root `visible: false`. These toasts are
#     pushed by NATIVE code (nothing in yaml references them), so the event
#     path cannot be cut — instead the popup renders invisible (zero-size,
#     no button, no text), like the WG reference hides UnlockRankHint.
AUTORANKS_FILES_LESTA = [
    "UI/Screens3/Lobby/Hangar/Hangar.yaml",
    "UI/Screens3/Lobby/Hangar/Squad/SquadView.yaml",
    "UI/Screens3/Lobby/Inventory/Inventory.yaml",
    "UI/Screens3/Lobby/Inventory/TankProgress/AchievementsTab.yaml",
    "UI/Screens3/Lobby/Inventory/TankProgress/AchievementsTab.actions",
    "UI/Screens3/Lobby/Inventory/TankProgress/NotEliteTankPanelInitialization.animation",
    "UI/Screens3/Lobby/Inventory/TankProgress/TankRankInitialization.animation",
    "UI/Screens/Lobby/Notifications/Popups/TankRankAvailableNotification.yaml",
    "UI/Screens/Lobby/Notifications/Popups/TankRanksUnlockedNotification.yaml",
]

RANK_TOKENS = ("UnlockRank", "UnlockFirstRank", "FirstRankSoundPlayed", "OnPromoRankInfoClicked")

# Lesta v4: manual tokens (UnlockRank / UnlockFirstRank / UnlockNextRank)
# are INTENTIONALLY kept — the GET RANK button must work (WG parity: on
# WoT Blitz manual acquisition works, only the auto-grant factor is cut).
# Only the promo popup is stripped from yaml. (FirstRankSoundPlayed is
# absent from the Lesta client entirely — verified by full Data/UI grep.)
RANK_TOKENS_LESTA = RANK_TOKENS + ("UnlockNextRank",)

# Lesta v4: the ONLY yaml token removed (promo popup, zero acquisition
# function). Manual tokens never enter the strip set.
LESTA_PROMO_TOKEN = "OnPromoRankInfoClicked"

# Lesta animation auto-fire: exactly these statements grant the rank
# without any click (tab open -> init -> event -> forwarders -> native).
# Both init animations fire Event("UnlockFirstRank") on their own.
_LESTA_AUTOEVENT_RES = tuple(re.compile(p) for p in (
    r'^\s*Event\(\s*"UnlockFirstRank"\s*\)\s*;\s*$',
))

# Lesta ceremony fanfare lines (AchievementsTab.actions): sound, flash,
# fade and their pacing Waits. The state-transition lines
# (ChangeData(showRank, true) / ChangeData(needsUnlock, false)) stay.
_LESTA_FANFARE_RES = tuple(re.compile(p) for p in (
    r'^\s*PlaySound\(\s*"play_ui_rank_prgrs_info_flash"\s*\)\s*;\s*$',
    r'^\s*DirectEvent\(\s*"PlayUnlockEffect".*\)\s*;\s*$',
    r'^\s*Opacity\(\s*(path\s*=\s*)?"\*\*/NoRankWrapper".*\)\s*;\s*$',
    r'^\s*Wait\(\s*0\.5\s*\)\s*;\s*$',
))

_RE_BINDING = re.compile(r'\[\s*(["\'])visible\1\s*,\s*(["\'])not rankUnlockRequired\2\s*\]')
_RE_ARG_PASS = re.compile(r'^\s*"rankUnlockRequired"\s*:\s*"rankUnlockRequired"\s*$')
_RE_PARAM_BOOL_FALSE = re.compile(r'^\s*-\s*\["bool",\s*"rankUnlockRequired",\s*"false",\s*"false"\]\s*$')
_RE_EVENT_LINE = re.compile(r'^\s*-\s*["\'](UnlockRank|OnPromoRankInfoClicked)["\']\s*$')
_RE_ITEM_LINE = re.compile(r'^(\s*-\s*)\[(.*)\]\s*$')
_RE_EVENT_ACTIONS_KEY = re.compile(r'^\s*eventActions:\s*$')

# Lesta v3: ``ranksAvailable`` is forced to false ONLY in Hangar.yaml
# (hangar teaser/counters off; the depot Rank TAB uses its own
# definition in Inventory.yaml and stays visible). ``avaibleRank``
# (client typo, depot lightning FX only) is forced to false — pure
# fanfare, zero acquisition function.
_RE_RANKS_AVAILABLE_LINE = re.compile(
    r'^(\s*-\s*\["bool",\s*"ranksAvailable",\s*").*("\]\s*)$'
)
_RE_AVAIBLERANK_LINE = re.compile(
    r'^(\s*-\s*\["bool",\s*"avaibleRank",\s*").*("\]\s*)$'
)


def autoranks_files_for_project(project="wargaming"):
    """File list for the given project (WG vs Lesta split)."""
    if (project or "wargaming").lower() == "lesta":
        return list(AUTORANKS_FILES_LESTA)
    return list(AUTORANKS_FILES_WG)


def rank_tokens_for_project(project="wargaming"):
    """eventActions tokens for the given project."""
    if (project or "wargaming").lower() == "lesta":
        return RANK_TOKENS_LESTA
    return RANK_TOKENS
