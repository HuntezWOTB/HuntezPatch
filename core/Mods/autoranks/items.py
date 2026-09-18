"""AutoRanksOFF operation: eventActions '- [...]' item surgery."""
from .constants import RANK_TOKENS, _RE_ITEM_LINE


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
