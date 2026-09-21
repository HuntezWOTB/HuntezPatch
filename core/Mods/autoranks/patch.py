"""AutoRanksOFF operation: surgical text transforms (ported, cleaned).

Reference behaviour (OFF-GetRank_MOD original/edited pairs):
  1. Prepend the unified header (see core.Mods.headers).
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
   10. GameModeAbilities (Hangar only): append "and not trainingVisible" to the
      "tankAbilitiesVisible and not isInSquad" condition, so the small
      "Способности" popup no longer shows in the training room.
Everything else (incl. the rankUnlockRequired binding definition itself and
the UnlockRankHint condition) is left untouched, byte-for-byte.
Idempotent: re-running an edited file yields 0 changes.
"""
import re

from .constants import (
    RANK_TOKENS,
    _RE_ARG_PASS, _RE_BINDING, _RE_EVENT_ACTIONS_KEY, _RE_EVENT_LINE,
    _RE_ITEM_LINE, _RE_PARAM_BOOL_FALSE,
)
from ..headers import normalize_text_header
from .items import _transform_item_line


def modify_autoranks_text(text, filename=""):
    """Apply AutoRanksOFF transforms. Returns (new_text, changes:int, notes:list[str])."""
    notes = []
    changes = 0
    lines = text.splitlines()
    had_trailing_nl = text.endswith("\n")

    # 1. Unified header (single logical change, kept byte-for-byte afterwards).
    lines, header_changed = normalize_text_header(lines, "yaml", [])
    if header_changed:
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

        # 2b. GameModeAbilities ("Способности"): hide in training room.
        # Hangar.yaml defines trainingVisible (prebattleType == TRAINING);
        # vanilla condition shows abilities there, which is wrong for that mode.
        if "Hangar.yaml" in filename and "tankAbilitiesVisible" in line and "not isInSquad" in line \
                and "condition" in line and "not trainingVisible" not in line:
            line = line.replace("tankAbilitiesVisible and not isInSquad",
                                "tankAbilitiesVisible and not isInSquad and not trainingVisible")
            changes += 1

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
