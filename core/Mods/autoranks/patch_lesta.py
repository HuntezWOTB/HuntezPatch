"""AutoRanksOFF for Tanks Blitz (Lesta): own patch structure (v5).

Design goal (WG parity — on WoT Blitz manual acquisition works, only
the auto-grant factor is cut): the Rank TAB renders like vanilla, the
GET RANK button works, but NOTHING grants a rank by itself and NO rank
toast ever shows.

Why a separate structure: the Lesta client has NO ``rankUnlockRequired``
gating at all (verified: zero hits in the whole Data/UI tree).

Proven auto-grant chain: NotEliteTankPanelInitialization.animation fires
Event("UnlockFirstRank") on EVERY elite-tank tab open (`if (isElite)`)
(plus TankRankInitialization.animation when firstRankUnlock) ->
AchievementsTab forwarder -> Inventory forwarder -> native dossier
update. v4 cuts the AUTO TRIGGER (the two animation lines) and leaves
every manual button/chain byte-identical.

What v4 changes, file by file:

  * Hangar.yaml — ``ranksAvailable`` -> ``false`` ONLY here. Kills the
    hangar counters/teaser ("У твоего танка появился ранг!") + sounds.
    The depot Rank TAB (own definition in Inventory.yaml) STAYS visible.
  * Inventory.yaml / AchievementsTab.yaml — header stamp + remove ONLY
    the promo popup plumbing (OnPromoRankInfoClicked). needsUnlock,
    showRank, ranksAvailable, currentTankRank, avaibleRank aside (FX
    off), and every Unlock*/Upgrade button + forwarder stay
    byte-identical: the screen renders like vanilla, GET RANK works.
  * AchievementsTab.actions — fanfare stripped from AnimateRankUnlock
    (sound/flash/fade/waits), state transition kept.
  * *Initialization.animation (x2) — the auto Event("UnlockFirstRank")
    lines removed. Manual clicks are the only remaining grant source.
  * TankRankAvailableNotification.yaml / TankRanksUnlockedNotification.yaml
    — root `visible: false`. Pushed by native code; rendering killed.
  * SquadView.yaml — header stamp only (zero rank tokens in Lesta).

Result: working screen, working GET RANK button, no auto-grant, no toast.

Idempotent: re-running a patched file yields 0 changes.
"""
import re

from .constants import (
    _LESTA_AUTOEVENT_RES,
    _LESTA_FANFARE_RES,
    _RE_AVAIBLERANK_LINE,
    _RE_EVENT_ACTIONS_KEY,
    _RE_ITEM_LINE,
    _RE_RANKS_AVAILABLE_LINE,
    LESTA_PROMO_TOKEN,
)
from ..headers import normalize_text_header
from .items import _split_elements, _unquote


def _strip_promo_item(line):
    """Remove ONLY the promo token from one '- [...]' item line.

    Returns (new_line_or_None, removed_count). None means drop the line.
    Manual tokens (UnlockRank / UnlockFirstRank / UnlockNextRank) are
    never touched here.
    """
    m = _RE_ITEM_LINE.match(line)
    if not m:
        return line, 0
    prefix, inner = m.group(1), m.group(2)
    elems = [_e.strip() for _e in _split_elements(inner)]
    kept = [e for e in elems if _unquote(e) != LESTA_PROMO_TOKEN]
    removed = len(elems) - len(kept)
    if removed == 0:
        return line, 0
    if not kept or all(_unquote(e) == "" for e in kept):
        return None, removed
    return f"{prefix}[{', '.join(kept)}]", removed


def _is_hangar_yaml(filename):
    return (filename or "").replace("\\", "/").endswith("Hangar/Hangar.yaml")


def modify_autoranks_text_lesta(text, filename=""):
    """Apply the Lesta v4 yaml transforms. Returns (new_text, changes, notes).

    Screen renders like vanilla; only the promo popup is cut.
    Manual chains stay byte-identical.
    """
    notes = []
    changes = 0
    lines = text.splitlines()
    had_trailing_nl = text.endswith("\n")

    lines, header_changed = normalize_text_header(lines, "yaml", [])
    if header_changed:
        changes += 1
        notes.append("header added")

    hangar = _is_hangar_yaml(filename)
    out = []
    for line in lines:
        # Hangar-only master switch -> false (teaser/counters off, tab kept).
        if hangar:
            m = _RE_RANKS_AVAILABLE_LINE.match(line)
            if m and ', "false"]' not in line:
                line = m.group(1) + "false" + m.group(2)
                changes += 1
                notes.append("hangar ranksAvailable forced false (tab kept)")

        # Depot lightning FX master -> false (pure fanfare, no function).
        m2 = _RE_AVAIBLERANK_LINE.match(line)
        if m2 and ', "false"]' not in line:
            line = m2.group(1) + "false" + m2.group(2)
            changes += 1
            notes.append("avaibleRank forced false (fanfare FX off)")

        # Promo event declaration: exact line only (manual decls untouched).
        if line.strip() == '- "%s"' % LESTA_PROMO_TOKEN:
            changes += 1
            notes.append("dropped event: - \"%s\"" % LESTA_PROMO_TOKEN)
            continue

        # Promo element surgery (manual tokens untouched — GET RANK works).
        if _RE_ITEM_LINE.match(line) and LESTA_PROMO_TOKEN in line:
            new_line, removed = _strip_promo_item(line)
            changes += removed
            if new_line is None:
                notes.append("dropped emptied promo event item")
                continue
            line = new_line

        out.append(line)

    # Drop eventActions: keys left with no items.
    final = []
    for idx, ln in enumerate(out):
        if _RE_EVENT_ACTIONS_KEY.match(ln):
            has_item = False
            for nxt in out[idx + 1:]:
                if nxt.strip() == "":
                    continue
                if re.match(r"^\s*-\s*\[", nxt):
                    has_item = True
                break
            if not has_item:
                changes += 1
                notes.append("dropped emptied eventActions block")
                continue
        final.append(ln)

    new_text = "\n".join(final)
    if had_trailing_nl:
        new_text += "\n"
    return new_text, changes, notes


def modify_autoranks_actions_lesta(text, filename=""):
    """Apply the Lesta v4 .actions transform (ceremony fanfare only).

    Removes the celebration sound / flash / fade + pacing waits from
    ``AnimateRankUnlock``; the state transition lines stay so the tab
    keeps rendering correctly. Returns (new_text, changes, notes).
    """
    notes = []
    changes = 0
    lines = text.splitlines()
    had_trailing_nl = text.endswith("\n")

    lines, header_changed = normalize_text_header(lines, "actions", [])
    if header_changed:
        changes += 1
        notes.append("header added")

    out = []
    for line in lines:
        if any(rx.match(line) for rx in _LESTA_FANFARE_RES):
            changes += 1
            notes.append("dropped ceremony fanfare: %s" % line.strip()[:60])
            continue
        out.append(line)

    new_text = "\n".join(out)
    if had_trailing_nl:
        new_text += "\n"
    return new_text, changes, notes


def modify_autoranks_animation_lesta(text, filename=""):
    """Apply the Lesta .animation transform (auto-grant trigger only).

    Removes the self-fired Event("UnlockFirstRank") statements from the
    init animations. Everything else (if-structure, visual setup) stays,
    so the files keep loading exactly like vanilla. The GET RANK button
    chain is untouched and remains the only grant source.
    Returns (new_text, changes, notes).
    """
    notes = []
    changes = 0
    lines = text.splitlines()
    had_trailing_nl = text.endswith("\n")

    lines, header_changed = normalize_text_header(lines, "actions", [])
    if header_changed:
        changes += 1
        notes.append("header added")

    out = []
    for line in lines:
        if any(rx.match(line) for rx in _LESTA_AUTOEVENT_RES):
            changes += 1
            notes.append("dropped auto Event: %s" % line.strip()[:60])
            continue
        out.append(line)

    new_text = "\n".join(out)
    if had_trailing_nl:
        new_text += "\n"
    return new_text, changes, notes


def modify_autoranks_notification_lesta(text, filename=""):
    """Apply the Lesta notification transform (toast killer).

    Inserts root-level `visible: false` right after the root
    `input: false` line, so the natively-pushed popup renders invisible
    (zero-size, no button, no text) — the same trick the WG reference
    uses on UnlockRankHint. Everything else stays byte-identical.
    Returns (new_text, changes, notes).
    """
    notes = []
    changes = 0
    lines = text.splitlines()
    had_trailing_nl = text.endswith("\n")

    lines, header_changed = normalize_text_header(lines, "yaml", [])
    if header_changed:
        changes += 1
        notes.append("header added")

    out = []
    inserted = False
    for idx, line in enumerate(lines):
        out.append(line)
        if inserted:
            continue
        m = re.match(r'^(\s*)input:\s*false\s*$', line)
        if m:
            # Skip if already hidden (idempotency): next non-blank line
            # is `visible: false` at the same indent.
            nxt = idx + 1
            while nxt < len(lines) and lines[nxt].strip() == "":
                nxt += 1
            if nxt < len(lines) and re.match(
                    r'^%svisible:\s*false\s*$' % re.escape(m.group(1)), lines[nxt]):
                inserted = True  # already applied — do not duplicate
                continue
            out.append("%svisible: false" % m.group(1))
            changes += 1
            notes.append("notification hidden (visible: false)")
            inserted = True

    new_text = "\n".join(out)
    if had_trailing_nl:
        new_text += "\n"
    return new_text, changes, notes
