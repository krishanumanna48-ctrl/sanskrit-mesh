import unicodedata

from sanskrit_mesh.core import tables


_TIKTOKEN = None
_TIKTOKEN_TRIED = False


def _get_tiktoken():
    global _TIKTOKEN, _TIKTOKEN_TRIED
    if _TIKTOKEN_TRIED:
        return _TIKTOKEN
    _TIKTOKEN_TRIED = True
    try:
        import tiktoken
        _TIKTOKEN = tiktoken.get_encoding("cl100k_base")
    except Exception:
        _TIKTOKEN = None
    return _TIKTOKEN


def estimate_tokens(text):
    if not isinstance(text, str):
        return 0
    if not text:
        return 0
    enc = _get_tiktoken()
    if enc is not None:
        try:
            return len(enc.encode(text))
        except Exception:
            pass
    return _heuristic_estimate(text)


def _heuristic_estimate(text):
    count = 0
    i = 0
    n = len(text)
    ascii_word = 0
    while i < n:
        ch = text[i]
        cp = ord(ch)
        if cp < 0x80:
            if ch.isalnum() or ch == "_":
                ascii_word += 1
            else:
                if ascii_word:
                    count += max(1, (ascii_word + 3) // 4)
                    ascii_word = 0
                if ch in (" ", "\t"):
                    pass
                else:
                    count += 1
            i += 1
            continue
        if 0x3040 <= cp <= 0x9FFF or 0xAC00 <= cp <= 0xD7AF:
            count += 2
            i += 1
            continue
        if 0x4E00 <= cp <= 0x9FFF:
            count += 2
            i += 1
            continue
        count += 1
        i += 1
    if ascii_word:
        count += max(1, (ascii_word + 3) // 4)
    return max(1, count)


class TokenMetrics:
    def __init__(self, use_exact=True):
        self.use_exact = use_exact and _get_tiktoken() is not None

    def count(self, text):
        if self.use_exact:
            return estimate_tokens(text)
        return _heuristic_estimate(text)

    def report(self, original, compressed):
        if isinstance(original, str):
            orig_str = original
        else:
            import json
            orig_str = json.dumps(original, ensure_ascii=False, separators=(",", ":"))
        if isinstance(compressed, str):
            comp_str = compressed
        else:
            import json
            comp_str = json.dumps(compressed, ensure_ascii=False, separators=(",", ":"))

        orig_tokens = self.count(orig_str)
        comp_tokens = self.count(comp_str)
        orig_chars = len(orig_str)
        comp_chars = len(comp_str)
        tokens_saved = orig_tokens - comp_tokens
        chars_saved = orig_chars - comp_chars
        token_pct = round((tokens_saved / orig_tokens) * 100, 2) if orig_tokens > 0 else 0.0
        char_pct = round((chars_saved / orig_chars) * 100, 2) if orig_chars > 0 else 0.0
        cost_per_million = round((tokens_saved / 1_000_000) * tables.GPT4O_PRICE_PER_MILLION, 6)

        return {
            "original_chars": orig_chars,
            "compressed_chars": comp_chars,
            "chars_saved": chars_saved,
            "char_compression_pct": char_pct,
            "original_tokens": orig_tokens,
            "compressed_tokens": comp_tokens,
            "tokens_saved": tokens_saved,
            "token_compression_pct": token_pct,
            "estimated_cost_saved_usd_gpt4o": cost_per_million,
            "monthly_savings_100k_calls_usd": round(cost_per_million * 100_000, 2),
            "tokenizer": "tiktoken/cl100k_base" if self.use_exact else "heuristic-estimate",
        }
