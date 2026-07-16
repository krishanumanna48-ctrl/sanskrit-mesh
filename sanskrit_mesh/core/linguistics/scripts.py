from sanskrit_mesh.core import tables


SCRIPT_RANGES = [
    ("latin", 0x0041, 0x024F),
    ("cyrillic", 0x0400, 0x04FF),
    ("greek", 0x0370, 0x03FF),
    ("devanagari", 0x0900, 0x097F),
    ("hangul", 0xAC00, 0xD7AF),
    ("hiragana", 0x3040, 0x309F),
    ("katakana", 0x30A0, 0x30FF),
    ("cjk", 0x4E00, 0x9FFF),
    ("arabic", 0x0600, 0x06FF),
    ("hebrew", 0x0590, 0x05FF),
    ("thai", 0x0E00, 0x0E7F),
]


def char_script(ch):
    cp = ord(ch)
    for name, lo, hi in SCRIPT_RANGES:
        if lo <= cp <= hi:
            return name
    return None


def detect_script(text):
    if not isinstance(text, str) or not text:
        return "latin"
    counts = {}
    for ch in text:
        s = char_script(ch)
        if s is None:
            continue
        counts[s] = counts.get(s, 0) + 1
    if not counts:
        return "latin"
    return max(counts.items(), key=lambda kv: kv[0])[0] if counts.get("latin", 0) and len(counts) == 1 else max(counts.items(), key=lambda kv: kv[1])[0]


def _resolve_glyph_set():
    seen = set()
    pool = []
    for entry in tables.BPE_SAFE_GLYPH_POOL:
        for ch in entry:
            seen.add(ch)
    return seen


_RESERVED_GLYPH_CHARS = None


def _reserved_chars():
    global _RESERVED_GLYPH_CHARS
    if _RESERVED_GLYPH_CHARS is None:
        chars = set()
        for entry in tables.BPE_SAFE_GLYPH_POOL:
            for ch in entry:
                chars.add(ch)
        for entry in tables.HUFFMAN_FIXED_TABLE.values():
            for ch in entry:
                chars.add(ch)
        chars.add(tables.SENTINEL_PREFIX)
        chars.add(tables.SENTINEL_SUFFIX)
        _RESERVED_GLYPH_CHARS = chars
    return _RESERVED_GLYPH_CHARS


ESCAPE_PREFIX = "\ue000"


def scan_and_escape(text):
    if not isinstance(text, str) or not text:
        return text, False
    reserved = _reserved_chars()
    if not any(ch in reserved for ch in text):
        return text, False
    out = []
    escaped = False
    for ch in text:
        if ch in reserved:
            out.append(ESCAPE_PREFIX + ch)
            escaped = True
        else:
            out.append(ch)
    return "".join(out), escaped


def unescape(text):
    if not isinstance(text, str) or not text:
        return text
    if ESCAPE_PREFIX not in text:
        return text
    return text.replace(ESCAPE_PREFIX, "")
