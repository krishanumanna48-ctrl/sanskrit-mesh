"""
Auto-Learning Engine for Sanskrit-Mesh V2.

Monitors real payload traffic, detects frequently repeated phrases,
auto-assigns short BPE-safe tokens, and grows the dictionary autonomously.

Two components:
  PhraseLearner  — monitors text, tracks n-gram frequencies, scores candidates
  AutoDictionary — integrates with HyperCompiler, persists learned patterns
"""

import json
import os
import re
import threading
from collections import Counter, defaultdict
from pathlib import Path

from sanskrit_mesh.core import tables
from sanskrit_mesh.core.token_metrics import estimate_tokens


class PhraseLearner:
    """
    Monitors text values flowing through the compiler and identifies
    high-value phrases that should be dictionary entries.

    Strategy:
    - Tokenize text into words
    - Track n-gram frequencies (length 2-6)
    - Score each candidate by: frequency × token_savings_per_occurrence
    - Only promote phrases that save net tokens (accounting for delimiter overhead)
    """

    def __init__(self, min_frequency=3, min_savings=2, max_phrases=500):
        self.min_frequency = min_frequency
        self.min_savings = min_savings       # minimum token savings per occurrence
        self.max_phrases = max_phrases
        self._lock = threading.RLock()
        # n-gram frequency: {phrase_text: count}
        self._ngram_counts = Counter()
        self._total_payloads = 0
        self._total_phrases_seen = 0
        # Learned dictionary: {phrase: token}
        self._learned = {}
        self._learned_reverse = {}
        # Glyph pool tracking — which BPE-safe glyphs are already used
        self._used_glyphs = set()
        self._glyph_pool_iter = iter(self._seed_glyph_pool())

    def _seed_glyph_pool(self):
        """Return iterator over glyphs not in V1 dictionary or Huffman table."""
        used = set()
        for v in tables.V1_DICTIONARY.values():
            used.add("|" + v + "|")
        for v in tables.HUFFMAN_FIXED_TABLE.values():
            used.add(v)
        for g in tables.BPE_SAFE_GLYPH_POOL:
            if g not in used and len(g) >= 1:
                yield "|" + g + "|"

    def _ensure_glyph(self):
        """Get the next available glyph from the pool."""
        if self._glyph_pool_iter is None:
            return None
        try:
            glyph = next(self._glyph_pool_iter)
            self._used_glyphs.add(glyph)
            return glyph
        except StopIteration:
            self._glyph_pool_iter = None
            return None

    def ingest_text(self, text):
        """Analyze a text string for frequent phrases. Thread-safe."""
        if not isinstance(text, str) or len(text) < 10:
            return
        with self._lock:
            self._total_payloads += 1
            words = self._tokenize(text)
            if len(words) < 3:
                return
            # Extract n-grams (length 2 to min(6, len(words)))
            max_n = min(6, len(words))
            for n in range(2, max_n + 1):
                for i in range(len(words) - n + 1):
                    phrase = " ".join(words[i:i + n])
                    # Skip if phrase is already in V1 dictionary
                    if phrase in tables.V1_DICTIONARY:
                        continue
                    # Skip if we already learned this
                    if phrase in self._learned:
                        continue
                    # Skip very short or very long phrases
                    if len(phrase) < 8 or len(phrase) > 120:
                        continue
                    self._ngram_counts[phrase] += 1
                    self._total_phrases_seen += 1

    def _tokenize(self, text):
        """Split text into words, preserving punctuation as separate tokens."""
        # Simple tokenization: split on whitespace, keep punctuation attached
        tokens = []
        for word in text.split():
            # Strip common punctuation for matching but keep for length calc
            cleaned = word.strip(".,!?;:\"'()[]{}")
            if cleaned:
                tokens.append(cleaned)
        return tokens

    def score_candidates(self, top_n=20):
        """Score all tracked n-grams and return the top candidates sorted by net savings."""
        with self._lock:
            scored = []
            for phrase, count in self._ngram_counts.most_common():
                if count < self.min_frequency:
                    continue
                if len(scored) >= self.max_phrases:
                    break
                # Estimate token savings
                orig_tokens = estimate_tokens(phrase)
                # Token overhead: pipe delimiters "|phrase|" = 2 chars ≈ 0.5 tokens
                # Plus the glyph itself is 1 token
                compressed_tokens = 1  # single BPE-safe glyph = 1 token
                savings_per = orig_tokens - compressed_tokens
                if savings_per < self.min_savings:
                    continue
                net_savings = savings_per * count
                scored.append((net_savings, savings_per, count, phrase))

            scored.sort(key=lambda x: x[0], reverse=True)
            return scored[:top_n]

    def promote_candidates(self, top_n=10):
        """Promote the best candidates to the learned dictionary."""
        candidates = self.score_candidates(top_n=top_n)
        promoted = []
        with self._lock:
            for net_savings, savings_per, count, phrase in candidates:
                if phrase in self._learned:
                    continue
                glyph = self._ensure_glyph()
                if glyph is None:
                    break
                self._learned[phrase] = glyph
                self._learned_reverse[glyph] = phrase
                # Remove from n-gram tracker
                del self._ngram_counts[phrase]
                promoted.append((phrase, glyph, net_savings))
        return promoted

    def get_stats(self):
        """Return learner statistics."""
        with self._lock:
            return {
                "total_payloads_seen": self._total_payloads,
                "total_phrases_tracked": self._total_phrases_seen,
                "unique_ngrams_tracked": len(self._ngram_counts),
                "learned_entries": len(self._learned),
                "available_glyphs": sum(1 for _ in self._seed_glyph_pool()) - len(self._used_glyphs),
            }

    @property
    def dictionary(self):
        with self._lock:
            return dict(self._learned)

    @dictionary.setter
    def dictionary(self, value):
        with self._lock:
            self._learned = dict(value)
            self._learned_reverse = {v: k for k, v in self._learned.items()}

    def persist(self, path="learned_dict.json"):
        """Save learned dictionary to a JSON file."""
        data = {
            "version": "2.0.0",
            "type": "auto-learned-dictionary",
            "entries": self.dictionary,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def restore(self, path="learned_dict.json"):
        """Load learned dictionary from a JSON file."""
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "entries" in data:
                self.dictionary = data["entries"]
                return len(data["entries"])
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return 0

    def reset(self):
        """Reset all tracking data (keeps learned dictionary)."""
        with self._lock:
            self._ngram_counts.clear()
            self._total_payloads = 0
            self._total_phrases_seen = 0


class AutoDictionary:
    """
    Auto-growing dictionary that integrates with the HyperCompiler.

    Usage:
        from sanskrit_mesh.learning import AutoDictionary
        auto_dict = AutoDictionary()
        
        # After every payload:
        auto_dict.ingest(original_text, compressed_text)
        
        # Periodically:
        auto_dict.learn()  # promotes best candidates
        
        # Before the compiler runs:
        auto_dict.apply(compiler)  # injects learned entries into Paninian layer
    """

    def __init__(self, min_frequency=3, min_savings=2, persist_path="learned_dict.json"):
        self.learner = PhraseLearner(
            min_frequency=min_frequency,
            min_savings=min_savings,
        )
        self.persist_path = persist_path
        self._restored = self.learner.restore(persist_path)

    def ingest(self, original_text, compressed_text=None):
        """Feed a text payload to the learner (before compression is ideal)."""
        if isinstance(original_text, str):
            self.learner.ingest_text(original_text)
        elif isinstance(original_text, dict):
            self._ingest_dict(original_text)

    def _ingest_dict(self, d, depth=0):
        """Recursively extract string values from a dict/list."""
        if depth > 10:
            return
        if isinstance(d, dict):
            for v in d.values():
                self._ingest_dict(v, depth + 1)
        elif isinstance(d, list):
            for item in d:
                self._ingest_dict(item, depth + 1)
        elif isinstance(d, str) and len(d) > 10:
            self.learner.ingest_text(d)

    def learn(self, top_n=10):
        """Promote the best candidate phrases to the learned dictionary."""
        promoted = self.learner.promote_candidates(top_n=top_n)
        if promoted:
            self.learner.persist(self.persist_path)
        return promoted

    def apply(self, hyper_compiler):
        """Inject learned entries into a HyperCompiler's Paninian layer.
        
        This adds auto-learned phrases to both the V1 and full Paninian dictionaries
        so they get compressed on subsequent payloads.
        """
        if not hasattr(hyper_compiler, '_v1_paninian'):
            return
        learned = self.learner.dictionary
        if not learned:
            return
        
        # Inject into v1 paninian (always active)
        for phrase, glyph in learned.items():
            if phrase not in hyper_compiler._v1_paninian.dictionary:
                hyper_compiler._v1_paninian.dictionary[phrase] = glyph.strip("|")
                hyper_compiler._v1_paninian.reverse_dictionary[glyph.strip("|")] = phrase
        
        # Also inject into full paninian
        if hasattr(hyper_compiler, '_full_paninian'):
            for phrase, glyph in learned.items():
                if phrase not in hyper_compiler._full_paninian.dictionary:
                    hyper_compiler._full_paninian.dictionary[phrase] = glyph.strip("|")
                    hyper_compiler._full_paninian.reverse_dictionary[glyph.strip("|")] = phrase
        
        # Rebuild sorted keys
        hyper_compiler._v1_paninian.sorted_eng_keys = sorted(
            hyper_compiler._v1_paninian.dictionary.keys(), key=len, reverse=True
        )
        hyper_compiler._v1_paninian.sorted_tokens = sorted(
            hyper_compiler._v1_paninian.reverse_dictionary.keys(), key=len, reverse=True
        )
        if hasattr(hyper_compiler, '_full_paninian'):
            hyper_compiler._full_paninian.sorted_eng_keys = sorted(
                hyper_compiler._full_paninian.dictionary.keys(), key=len, reverse=True
            )
            hyper_compiler._full_paninian.sorted_tokens = sorted(
                hyper_compiler._full_paninian.reverse_dictionary.keys(), key=len, reverse=True
            )

    def get_stats(self):
        stats = self.learner.get_stats()
        stats["persist_path"] = self.persist_path
        stats["restored_entries"] = self._restored
        return stats