"""Unified generator stamp for all mods.

Style: #HuntezPatch - Generated: 19.01.2026 /// 00:21 [GMT+03]
  - yaml:  #HuntezPatch - Generated: ...
  - actions: //HuntezPatch - Generated: ...
  - xml: <!-- HuntezPatch - Generated: ... -->

Rule (keeps re-runs at 0 changes): a unified stamp, once present, is never
refreshed. Legacy per-mod headers are replaced by the unified one a single
time (that run counts the change).
"""
from datetime import datetime

YAML_PREFIX = "#HuntezPatch - Generated:"
ACTIONS_PREFIX = "//HuntezPatch - Generated:"
XML_PREFIX = "HuntezPatch - Generated:"

# Legacy first-lines: recognized ONLY to be stripped and replaced by the
# unified stamp. They are never written into files anymore.
LEGACY_YAML = frozenset({
    "# AutoRankOFF",
    "# Generated: Huntez_GenMods",
    "# RandomTankSelector",
    "# HiddenTanks-Generator",
    "# v 1.0.0",
    "# Generated code",
})
LEGACY_ACTIONS = frozenset({
    "// RandomTankSelector",
    "// Generated: Huntez_GenMods",
})


def gen_moment():
    """Local time as 'DD.MM.YYYY /// HH:MM [GMT+HH[:MM]]'."""
    now = datetime.now().astimezone()
    base = now.strftime("%d.%m.%Y /// %H:%M")
    off = now.utcoffset()
    secs = int(off.total_seconds()) if off is not None else 0
    sign = "+" if secs >= 0 else "-"
    hours, rem = divmod(abs(secs), 3600)
    minutes = rem // 60
    tz = "GMT%s%02d" % (sign, hours)
    if minutes:
        tz += ":%02d" % minutes
    return "%s [%s]" % (base, tz)


def yaml_stamp():
    return "%s %s" % (YAML_PREFIX, gen_moment())


def actions_stamp():
    return "%s %s" % (ACTIONS_PREFIX, gen_moment())


def xml_stamp():
    return "<!-- %s %s -->" % (XML_PREFIX, gen_moment())


def _is_unified(line, style):
    s = line.strip()
    if style == "yaml":
        return s.startswith(YAML_PREFIX)
    if style == "actions":
        return s.startswith(ACTIONS_PREFIX)
    return s.startswith("<!--") and XML_PREFIX in s


def _is_legacy(line, style):
    s = line.strip()
    if style == "yaml":
        return s in LEGACY_YAML
    if style == "actions":
        return s in LEGACY_ACTIONS
    return False


def normalize_text_header(lines, style, identity):
    """Ensure [unified stamp] + identity lines on top.

    identity: extra mod lines kept right after the stamp (may be []).
    Returns (lines, changed). A present unified stamp is kept byte-for-byte,
    so re-runs stay at 0 changes; legacy headers are replaced once.
    """
    lines = list(lines)
    if lines and _is_unified(lines[0], style):
        return lines, False
    i = 0
    while i < len(lines) and (_is_unified(lines[i], style) or _is_legacy(lines[i], style)):
        i += 1
    stamp = yaml_stamp() if style == "yaml" else actions_stamp()
    return [stamp] + list(identity) + lines[i:], True
