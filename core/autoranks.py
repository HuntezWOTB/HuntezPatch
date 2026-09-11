"""AutoRanksOFF: surgical text transforms replicating the reference mod.

Reference behaviour (OFF-GetRank_MOD original/edited pairs):
  1. Prepend header "# AutoRankOFF" / "# Generated: Huntez_GenMods".
  2. bindings ["visible", "not rankUnlockRequired"] -> ["visible", ""].
  3. conditions: drop "not rankUnlockRequired and " / " and not rankUnlockRequired".
  4. Delete arg passthrough lines: "rankUnlockRequired": "rankUnlockRequired".
  5. Delete SquadView local param: - ["bool", "rankUnlockRequired", "false", "false"].
  6. events: drop whole lines - "UnlockRank" / - "OnPromoRankInfoClicked".
  7. needsUnlock: "not isNull(dossier.rankState)" -> "isNull(dossier.rankState)".
  8. eventActions items: remove quoted elements matching rank tokens
     (UnlockRank, UnlockFirstRank, FirstRankSoundPlayed, OnPromoRankInfoClicked);
     drop the item line if only empty strings remain; drop an eventActions:
     key left with no items.
  9. ranksAvailable binding (Hangar): "not isNull(selectedTank) and ..." ->
     "isNull(selectedTank) and ..." — effectively disables ranks, so the
     "your tank has a rank" celebration never triggers.
Everything else (incl. the rankUnlockRequired binding definition itself and
the UnlockRankHint condition) is left untouched, byte-for-byte.
Idempotent: re-running an edited file yields 0 changes.
"""
import re

AUTORANKS_FILES = [
    "UI/Screens3/Lobby/Hangar/Hangar.yaml",
    "UI/Screens3/Lobby/Hangar/Squad/SquadView.yaml",
    "UI/Screens3/Lobby/Inventory/Inventory.yaml",
    "UI/Screens3/Lobby/Inventory/TankProgress/AchievementsTab.yaml",
]

RANK_TOKENS = ("UnlockRank", "UnlockFirstRank", "FirstRankSoundPlayed", "OnPromoRankInfoClicked")
HEADER = ("# AutoRankOFF", "# Generated: Huntez_GenMods")

_RE_BINDING = re.compile(r'\[\s*(["\'])visible\1\s*,\s*(["\'])not rankUnlockRequired\2\s*\]')
_RE_ARG_PASS = re.compile(r'^\s*"rankUnlockRequired"\s*:\s*"rankUnlockRequired"\s*$')
_RE_PARAM_BOOL_FALSE = re.compile(r'^\s*-\s*\["bool",\s*"rankUnlockRequired",\s*"false",\s*"false"\]\s*$')
_RE_EVENT_LINE = re.compile(r'^\s*-\s*["\'](UnlockRank|OnPromoRankInfoClicked)["\']\s*$')
_RE_ITEM_LINE = re.compile(r'^(\s*-\s*)\[(.*)\]\s*$')
_RE_EVENT_ACTIONS_KEY = re.compile(r'^\s*eventActions:\s*$')


def _split_elements(inner):
    """Split a [...] body on commas outside quotes."""
    parts, cur, quote = [], [], None
    for ch in inner:
        if quote is not None:
            cur.append(ch)
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
            cur.append(ch)
        elif ch == ',':
            parts.append(''.join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append(''.join(cur))
    return parts


def _unquote(element):
    s = element.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    return s


def _transform_item_line(line):
    """Apply token surgery to one '- [...]' line.

    Returns (new_line_or_None, removed_count). None means drop the line.
    """
    m = _RE_ITEM_LINE.match(line)
    if not m:
        return line, 0
    prefix, inner = m.group(1), m.group(2)
    elems = [_e.strip() for _e in _split_elements(inner)]
    kept = [e for e in elems if _unquote(e) not in RANK_TOKENS]
    removed = len(elems) - len(kept)
    if removed == 0:
        return line, 0
    if not kept or all(_unquote(e) == '' for e in kept):
        return None, removed
    return f"{prefix}[{', '.join(kept)}]", removed


def modify_autoranks_text(text, filename=""):
    """Apply AutoRanksOFF transforms. Returns (new_text, changes:int, notes:list[str])."""
    notes = []
    changes = 0
    lines = text.splitlines()
    had_trailing_nl = text.endswith("\n")

    # 1. Header (single logical change, skipped when already present).
    if not (len(lines) >= 2 and lines[0].strip() == HEADER[0] and lines[1].strip() == HEADER[1]):
        lines = [HEADER[0], HEADER[1]] + lines
        changes += 1
        notes.append("header added")

    out = []
    for line in lines:
        # 2. bindings: ["visible", "not rankUnlockRequired"] -> ["visible", ""]
        if "not rankUnlockRequired" in line and "visible" in line:
            new_line, n = _RE_BINDING.subn('["visible", ""]', line)
            if n:
                line = new_line
                changes += n

        # 3. conditions: drop the rank clause, keep the expression valid.
        if "rankUnlockRequired" in line and "condition" in line:
            if "not rankUnlockRequired and " in line:
                line = line.replace("not rankUnlockRequired and ", "")
                changes += 1
            if " and not rankUnlockRequired" in line:
                line = line.replace(" and not rankUnlockRequired", "")
                changes += 1
            if "not rankUnlockRequired" in line:
                line = line.replace("not rankUnlockRequired", "true")
                changes += 1

        # 4-5. Delete arg passthrough / SquadView local bool param.
        if "rankUnlockRequired" in line and (_RE_ARG_PASS.match(line) or _RE_PARAM_BOOL_FALSE.match(line)):
            changes += 1
            notes.append(f"dropped rank passthrough: {line.strip()[:80]}")
            continue

        # 6. events: drop whole lines.
        if _RE_EVENT_LINE.match(line):
            changes += 1
            notes.append(f"dropped event: {line.strip()[:80]}")
            continue

        # 7. needsUnlock inversion.
        if "needsUnlock" in line and "not isNull(dossier.rankState)" in line:
            line = line.replace("not isNull(dossier.rankState)", "isNull(dossier.rankState)")
            changes += 1

        # 9. ranksAvailable master switch (Hangar): without it the
        # "your tank has a rank" celebration still triggers.
        if "ranksAvailable" in line and "not isNull(selectedTank)" in line:
            line = line.replace("not isNull(selectedTank)", "isNull(selectedTank)")
            changes += 1

        # 8. eventActions element surgery.
        if _RE_ITEM_LINE.match(line) and any(tok in line for tok in RANK_TOKENS):
            new_line, removed = _transform_item_line(line)
            changes += removed
            if new_line is None:
                notes.append("dropped emptied event item")
                continue
            line = new_line

        out.append(line)

    # 8b. Drop eventActions: keys left with no items.
    final = []
    for idx, ln in enumerate(out):
        if _RE_EVENT_ACTIONS_KEY.match(ln):
            # Items sit at the same indent as their key ("- " is not whitespace),
            # so the first non-blank line decides: item -> keep, else drop.
            has_item = False
            for nxt in out[idx + 1:]:
                if nxt.strip() == '':
                    continue
                if re.match(r'^\s*-\s*\[', nxt):
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


def describe_autoranks_patch(filename, changes):
    return f"{filename}: {changes} edit(s)"
