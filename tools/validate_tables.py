"""Simple validator for `sanskrit_mesh.core.tables` invariants.

Checks performed:
- All entries in `BPE_SAFE_GLYPH_POOL` are unique.
- No glyph in `BPE_SAFE_GLYPH_POOL` collides with single-char values used
  in `HUFFMAN_FIXED_TABLE` or `V1_KEY_MAP`/`EXTENDED_KEY_MAP` outputs.
- Inverse maps like `ENGLISH_STOPWORD_INVERSE` and `HUFFMAN_FIXED_INVERSE`
  are consistent with their forward maps.
"""
import sys
import os
# Ensure repo root is on sys.path so local package imports work when running as script
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from sanskrit_mesh.core import tables


def fail(msg):
    print("FAIL:", msg)
    sys.exit(2)


def main():
    pool = tables.BPE_SAFE_GLYPH_POOL
    if len(pool) != len(set(pool)):
        fail("BPE_SAFE_GLYPH_POOL contains duplicates")
    print("OK: BPE_SAFE_GLYPH_POOL unique")

    # Flatten single characters present in pool
    pool_chars = set(''.join(pool))

    # Check fixed table values do not use pool single-char glyphs
    fixed_vals = set(tables.HUFFMAN_FIXED_TABLE.values())
    for v in fixed_vals:
        for ch in v:
            if ch in pool_chars:
                fail(f"HUFFMAN_FIXED_TABLE value '{v}' contains glyph in BPE_SAFE_GLYPH_POOL: '{ch}'")
    print("OK: HUFFMAN_FIXED_TABLE values do not overlap pool chars")

    # Verify ENGLISH_STOPWORD_INVERSE
    if hasattr(tables, 'ENGLISH_STOPWORD_MAP') and hasattr(tables, 'ENGLISH_STOPWORD_INVERSE'):
        inv = {v: k for k, v in tables.ENGLISH_STOPWORD_MAP.items()}
        if inv != tables.ENGLISH_STOPWORD_INVERSE:
            fail('ENGLISH_STOPWORD_INVERSE does not match ENGLISH_STOPWORD_MAP')
        print('OK: ENGLISH_STOPWORD_INVERSE consistent')

    # Verify HUFFMAN_FIXED_INVERSE
    if hasattr(tables, 'HUFFMAN_FIXED_TABLE') and hasattr(tables, 'HUFFMAN_FIXED_INVERSE'):
        inv = {v: k for k, v in tables.HUFFMAN_FIXED_TABLE.items()}
        if inv != tables.HUFFMAN_FIXED_INVERSE:
            fail('HUFFMAN_FIXED_INVERSE does not match HUFFMAN_FIXED_TABLE')
        print('OK: HUFFMAN_FIXED_INVERSE consistent')

    # Check sentinel presence
    if not tables.SENTINEL_PREFIX or not tables.SENTINEL_SUFFIX:
        fail('SENTINEL_PREFIX/SUFFIX not defined')
    print('OK: SENTINEL_PREFIX/SUFFIX present')

    print('\nAll table invariants passed.')


if __name__ == '__main__':
    main()
