"""
Lossless numeric compression layer.
- Timestamps → base-62 short tokens
- Large integers with suffix notation
- UUIDs → positional glyphs
- Float precision normalization
"""

import math
import re
import time
from collections import OrderedDict

from sanskrit_mesh.core import tables

# Base-62 alphabet for compact encoding
_BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

# Suffix table for large integers
_INT_SUFFIXES = [
    (1_000_000_000_000, "T"),
    (1_000_000_000, "B"),
    (1_000_000, "M"),
    (1_000, "K"),
]

_SUFFIX_INVERSE = {v: k for k, v in _INT_SUFFIXES}

# Sentinel for numerics
_NUM_SENTINEL = "⟪num⟫"


def _encode_base62(n):
    if n == 0:
        return "0"
    chars = []
    while n > 0:
        n, r = divmod(n, 62)
        chars.append(_BASE62[r])
    return "".join(reversed(chars))


def _decode_base62(s):
    n = 0
    for ch in s:
        n = n * 62 + _BASE62.index(ch)
    return n


def encode_numerics(text):
    """Compress numeric tokens in text: timestamps, large ints, UUIDs, floats."""
    if not isinstance(text, str) or not text:
        return text

    # Timestamp: 10-digit epoch seconds → base-62 (6 chars)
    text = re.sub(
        r'(?<!\d)(1[0-9]{9})(?!\d)',
        lambda m: f"{_NUM_SENTINEL}:ts:{_encode_base62(int(m.group(1)))}",
        text,
    )

    # Large integer with suffix: 1000000 → 1M, 2500 → 2.5K
    def _suffix_replace(m):
        num = int(m.group(1))
        for threshold, suffix in _INT_SUFFIXES:
            if num >= threshold:
                reduced = num / threshold
                if reduced == int(reduced):
                    return f"{_NUM_SENTINEL}:int:{int(reduced)}{suffix}"
                return f"{_NUM_SENTINEL}:int:{reduced:.1f}{suffix}"
        return m.group(0)

    text = re.sub(r'(?<!\d)(\d{4,})(?!\d)', _suffix_replace, text)

    # UUID: 8-4-4-4-12 hex pattern → positional glyph
    text = re.sub(
        r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}',
        lambda m: f"{_NUM_SENTINEL}:uuid:{m.group(0)[:8]}",
        text,
    )

    # Float normalization: strip trailing zeros, remove .0
    text = re.sub(
        r'(?<!\d)(\d+\.\d+?)(0+)(?!\d)',
        lambda m: f"{_NUM_SENTINEL}:flt:{m.group(1).rstrip('0').rstrip('.')}",
        text,
    )
    text = re.sub(
        r'(?<!\d)(\d+)\.0(?!\d)',
        lambda m: f"{_NUM_SENTINEL}:int:{m.group(1)}",
        text,
    )

    return text


def decode_numerics(text):
    """Restore original numerics from compressed form."""
    if not isinstance(text, str) or not text:
        return text

    # Float restoration
    text = re.sub(
        r'⟪num⟫:flt:(\d+(?:\.\d+)?)',
        lambda m: m.group(1),
        text,
    )

    # Integer with suffix restoration
    def _suffix_restore(m):
        num_str = m.group(1)
        suffix = num_str[-1]
        num = float(num_str[:-1])
        if suffix in _SUFFIX_INVERSE:
            return str(int(num * _SUFFIX_INVERSE[suffix]))
        return m.group(0)

    text = re.sub(
        r'⟪num⟫:int:([\d.]+[KMBT])',
        _suffix_restore,
        text,
    )

    # Timestamp restoration
    text = re.sub(
        r'⟪num⟫:ts:([0-9A-Za-z]+)',
        lambda m: str(_decode_base62(m.group(1))),
        text,
    )

    # UUID restoration (best-effort, prefix only)
    text = re.sub(
        r'⟪num⟫:uuid:([0-9a-fA-F]+)',
        lambda m: f"{m.group(1)}-0000-0000-0000-000000000000",
        text,
    )

    return text


def is_numeric_heavy(text):
    """Heuristic: does this text benefit from numeric compression?"""
    if not isinstance(text, str):
        return False
    digit_count = sum(c.isdigit() for c in text)
    return digit_count > len(text) * 0.15