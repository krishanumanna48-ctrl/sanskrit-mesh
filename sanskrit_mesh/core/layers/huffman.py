import json

from sanskrit_mesh.core import tables
from sanskrit_mesh.core.linguistics.scripts import scan_and_escape, unescape


class HuffmanLayer:
    def __init__(self, mode="fixed"):
        if mode not in ("fixed", "dynamic", "off"):
            mode = "fixed"
        self.mode = mode
        self.fixed_table = tables.HUFFMAN_FIXED_TABLE
        self.fixed_inverse = tables.HUFFMAN_FIXED_INVERSE
        self._fixed_sorted = sorted(self.fixed_table.keys(), key=len, reverse=True)
        self._fixed_inverse_sorted = sorted(self.fixed_inverse.keys(), key=len, reverse=True)

    def encode(self, text):
        if not isinstance(text, str) or not text:
            return text
        if self.mode == "off":
            return text
        # Guard: skip Huffman if text contains V1 Paninian tokens (|...|)
        if '|' in text:
            return text
        text, escaped = scan_and_escape(text)
        if self.mode == "fixed":
            return self._apply_fixed(text)
        return self._apply_dynamic(text)

    def decode(self, text, envelope=None):
        if not isinstance(text, str) or not text:
            return text
        if self.mode == "off":
            return unescape(text)
        if self.mode == "dynamic" and envelope is not None:
            result = self._reverse_dynamic(text, envelope)
        else:
            result = self._reverse_fixed(text)
        return unescape(result)

    def _apply_fixed(self, text):
        result = text
        for chunk in self._fixed_sorted:
            if chunk in result:
                result = result.replace(chunk, self.fixed_table[chunk])
        return result

    def _reverse_fixed(self, text):
        result = text
        for glyph in self._fixed_inverse_sorted:
            if glyph in result:
                result = result.replace(glyph, self.fixed_inverse[glyph])
        return result

    def _apply_dynamic(self, text):
        frequencies = {}
        i = 0
        candidates = []
        window_sizes = (6, 5, 4, 3)
        for size in window_sizes:
            if len(text) < size:
                continue
            for j in range(len(text) - size + 1):
                chunk = text[j:j + size]
                if any(ch in chunk for ch in (' ', '"', "'")):
                    continue
                if chunk.isascii() and chunk.isalpha():
                    continue
                count = text.count(chunk)
                if count >= 2:
                    gain = (len(chunk) - 1) * count
                    frequencies[chunk] = gain
        ranked = sorted(frequencies.items(), key=lambda kv: kv[1], reverse=True)
        pool = [g for g in tables.BPE_SAFE_GLYPH_POOL if len(g) == 1]
        used = set(self.fixed_inverse.keys())
        available = [g for g in pool if g not in used][:64]
        mapping = {}
        for chunk, _ in ranked:
            if not available:
                break
            glyph = available.pop(0)
            mapping[chunk] = glyph
        if not mapping:
            return text
        result = text
        for chunk in sorted(mapping.keys(), key=len, reverse=True):
            result = result.replace(chunk, mapping[chunk])
        envelope = json.dumps(mapping, ensure_ascii=False, separators=(",", ":"))
        return tables.ENVELOPE_KEY + envelope + tables.ENVELOPE_KEY + result

    def _reverse_dynamic(self, text, envelope):
        mapping = envelope if isinstance(envelope, dict) else json.loads(envelope)
        result = text
        for chunk in sorted(mapping.keys(), key=len, reverse=True):
            glyph = mapping[chunk]
            result = result.replace(glyph, chunk)
        return result

    def strip_envelope(self, text):
        if not isinstance(text, str):
            return text, None
        if not text.startswith(tables.ENVELOPE_KEY):
            return text, None
        start = len(tables.ENVELOPE_KEY)
        end = text.find(tables.ENVELOPE_KEY, start)
        if end == -1:
            return text, None
        envelope_raw = text[start:end]
        body = text[end + len(tables.ENVELOPE_KEY):]
        try:
            envelope = json.loads(envelope_raw)
        except (ValueError, TypeError):
            return text, None
        return body, envelope
