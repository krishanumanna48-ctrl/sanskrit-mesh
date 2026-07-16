import re


_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_RE = re.compile(r"`[^`\n]*`")
_MD_TABLE_PIPE = "|"


def find_protected_spans(text):
    spans = []
    for m in _FENCE_RE.finditer(text):
        spans.append((m.start(), m.end(), "fence"))
    for m in _INLINE_RE.finditer(text):
        overlaps = any(s <= m.start() < e or s < m.end() <= e for s, e, _ in spans)
        if not overlaps:
            spans.append((m.start(), m.end(), "inline"))
    spans.sort()
    return spans


def split_protected(text):
    spans = find_protected_spans(text)
    if not spans:
        return [("text", text)]
    pieces = []
    cursor = 0
    for s, e, kind in spans:
        if cursor < s:
            pieces.append(("text", text[cursor:s]))
        pieces.append(("protected", text[s:e]))
        cursor = e
    if cursor < len(text):
        pieces.append(("text", text[cursor:]))
    return pieces


def is_structural_line(line):
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith(("#", ">", "- ", "* ", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")):
        return True
    if stripped.startswith("|") and stripped.endswith("|"):
        return True
    if stripped.startswith("```"):
        return True
    return False
