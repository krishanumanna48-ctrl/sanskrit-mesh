import re

from sanskrit_mesh.core import tables
from sanskrit_mesh.core import regions
from sanskrit_mesh.core.linguistics.matrices import detect_language, get_matrix, LANGUAGE_MATRICES
from sanskrit_mesh.core.linguistics.scripts import scan_and_escape, unescape


_WORD_BOUNDARY_CACHE = {}


def _build_pattern(stopword):
    if stopword in _WORD_BOUNDARY_CACHE:
        return _WORD_BOUNDARY_CACHE[stopword]
    if "'" in stopword or stopword.isascii() and not stopword.isalpha():
        pat = re.compile(re.escape(stopword))
    else:
        pat = re.compile(r"(?<!\w)" + re.escape(stopword) + r"(?!\w)")
    _WORD_BOUNDARY_CACHE[stopword] = pat
    return pat


class EntropyLayer:
    def __init__(self):
        self._merged_inverse = None

    def _merged_inverse_map(self):
        if self._merged_inverse is not None:
            return self._merged_inverse
        # Build an inverse map: glyph -> original word
        merged = {}
        for lang, matrix in LANGUAGE_MATRICES.items():
            stopwords = matrix.get("stopwords", {})
            # stopwords mapping is word -> glyph; invert to glyph -> word
            for word, glyph in stopwords.items():
                merged[glyph] = word
        self._merged_inverse = merged
        return merged

    def encode(self, text):
        if not isinstance(text, str) or not text:
            return text
        text, escaped = scan_and_escape(text)
        lang = detect_language(text)
        matrix = get_matrix(lang)
        stopwords = matrix.get("stopwords", {})
        if not stopwords:
            return text
        pieces = regions.split_protected(text)
        out = []
        for kind, chunk in pieces:
            if kind == "protected":
                out.append(chunk)
                continue
            out.append(self._encode_chunk(chunk, stopwords))
        return "".join(out)

    def _encode_chunk(self, chunk, stopwords):
        ordered = sorted(stopwords.keys(), key=len, reverse=True)
        result = chunk
        for word in ordered:
            glyph = stopwords[word]
            pat = _build_pattern(word)
            result = pat.sub(glyph, result)
        return result

    def decode(self, text):
        if not isinstance(text, str) or not text:
            return text
        inverse = self._merged_inverse_map()
        if not inverse:
            return unescape(text)
        pieces = regions.split_protected(text)
        out = []
        for kind, chunk in pieces:
            if kind == "protected":
                out.append(chunk)
                continue
            out.append(self._decode_chunk(chunk, inverse))
        result = "".join(out)
        return unescape(result)

    def _decode_chunk(self, chunk, inverse):
        ordered_glyphs = sorted(inverse.keys(), key=len, reverse=True)
        result = chunk
        for glyph in ordered_glyphs:
            word = inverse[glyph]
            result = result.replace(glyph, word)
        return result
