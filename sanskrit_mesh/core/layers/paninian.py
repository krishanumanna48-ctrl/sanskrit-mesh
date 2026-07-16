from sanskrit_mesh.core import tables
from sanskrit_mesh.core import regions
from sanskrit_mesh.core.linguistics.scripts import unescape
import re


class PaninianLayer:
    def __init__(self, v1_only=True):
        self.dictionary = dict(tables.V1_DICTIONARY)
        self.reverse_dictionary = {v: k for k, v in self.dictionary.items()}
        if not v1_only:
            self.dictionary.update(tables.SAMASA_DICTIONARY)
            self.reverse_dictionary = {v: k for k, v in self.dictionary.items()}
        self.sorted_eng_keys = sorted(self.dictionary.keys(), key=len, reverse=True)
        self.sorted_tokens = sorted(self.reverse_dictionary.keys(), key=len, reverse=True)
        self.v1_only = v1_only

    def compile_text(self, text):
        if not isinstance(text, str) or not text:
            return text
        compiled = text
        for eng in self.sorted_eng_keys:
            if eng in compiled:
                compiled = compiled.replace(eng, "|" + self.dictionary[eng] + "|")
        return compiled.strip()

    def decompile_text(self, text):
        if not isinstance(text, str) or not text:
            return text
        # Remove any escape prefixes added by the entropy layer so tokens
        # like "|AgA|" are restored to their expected form before
        # performing dictionary token replacement.
        decompiled = unescape(text)
        for san in self.sorted_tokens:
            if "|" + san + "|" in decompiled:
                decompiled = decompiled.replace("|" + san + "|", self.reverse_dictionary[san])
        return decompiled

    def apply_sandhi(self, text):
        if not isinstance(text, str) or not text:
            return text
        pieces = regions.split_protected(text)
        out = []
        sentinel = "⟠"
        vowel_pat = re.compile(r"([aeiouAEIOU])\s+([aeiouAEIOU])")
        for kind, chunk in pieces:
            if kind == "protected":
                out.append(chunk)
                continue
            result = vowel_pat.sub(r"\1" + sentinel + r"\2", chunk)
            # Add reversible connector rewrites that preserve the original words.
            result = result.replace(" and ", f" {sentinel}and{sentinel} ")
            result = result.replace(" of ", f" {sentinel}of{sentinel} ")
            out.append(result)
        return "".join(out)

    def reverse_sandhi(self, text):
        if not isinstance(text, str) or not text:
            return text
        result = text
        result = result.replace("⟠and⟠", " and ")
        result = result.replace("⟠of⟠", " of ")
        result = result.replace("⟠", " ")
        return re.sub(r"\s+", " ", result).strip()

    def apply_karaka(self, text):
        if not isinstance(text, str) or not text:
            return text
        pieces = regions.split_protected(text)
        out = []
        for kind, chunk in pieces:
            if kind == "protected":
                out.append(chunk)
                continue
            result = chunk
            for prep in sorted(tables.KARAKA_SUFFIXES.keys(), key=len, reverse=True):
                suffix = tables.KARAKA_SUFFIXES[prep]
                result = result.replace(" " + prep + " ", " " + suffix + " ")
            for phrase, token in tables.ENGLISH_AGGLOUTINATION_PHRASES.items():
                if phrase in result:
                    result = result.replace(phrase, token)
            result = self._replace_exact_phrases(result, tables.SAMASA_DICTIONARY)
            result = self._replace_exact_phrases(result, self._build_multilingual_phrase_map())
            out.append(result)
        return "".join(out)

    def reverse_karaka(self, text):
        if not isinstance(text, str) or not text:
            return text
        result = text
        for suffix, prep in tables.KARAKA_INVERSE.items():
            result = result.replace(" " + suffix + " ", " " + prep + " ")
        inverse_phrases = {v: k for k, v in tables.ENGLISH_AGGLOUTINATION_PHRASES.items()}
        for token, phrase in sorted(inverse_phrases.items(), key=lambda item: len(item[0]), reverse=True):
            result = result.replace(token, phrase)
        result = self._restore_exact_phrases(result, tables.SAMASA_DICTIONARY)
        result = self._restore_exact_phrases(result, self._build_multilingual_phrase_map())
        return result

    def _build_multilingual_phrase_map(self):
        mapping = {}
        for lang, phrase_map in tables.MULTILINGUAL_PHRASE_MAPS.items():
            for phrase, replacement in phrase_map.items():
                mapping[phrase] = replacement
        return mapping

    def _replace_exact_phrases(self, text, phrase_map):
        result = text
        for phrase, replacement in sorted(phrase_map.items(), key=lambda item: len(item[0]), reverse=True):
            if phrase in result:
                token = f"⟦PHRASE_{len(phrase)}_{hash(phrase) % 1000}⟧"
                result = result.replace(phrase, token, 1)
        return result

    def _restore_exact_phrases(self, text, phrase_map):
        result = text
        for phrase, replacement in sorted(phrase_map.items(), key=lambda item: len(item[0]), reverse=True):
            token = f"⟦PHRASE_{len(phrase)}_{hash(phrase) % 1000}⟧"
            result = result.replace(token, phrase, 1)
        return result

    def encode(self, text):
        if not isinstance(text, str) or not text:
            return text
        result = self.compile_text(text)
        if self.v1_only:
            return result
        result = self.apply_sandhi(result)
        result = self.apply_karaka(result)
        return result

    def decode(self, text):
        if not isinstance(text, str) or not text:
            return text
        if not self.v1_only:
            text = self.reverse_karaka(text)
            text = self.reverse_sandhi(text)
        return self.decompile_text(text)
