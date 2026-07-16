from sanskrit_mesh.core import tables


def _g(idx):
    if idx >= len(tables.BPE_SAFE_GLYPH_POOL):
        idx = len(tables.BPE_SAFE_GLYPH_POOL) - 1
    return tables.BPE_SAFE_GLYPH_POOL[idx]


_CURSOR = [50]


def _next_glyph():
    if _CURSOR[0] >= len(tables.BPE_SAFE_GLYPH_POOL):
        return tables.BPE_SAFE_GLYPH_POOL[-1]
    g = tables.BPE_SAFE_GLYPH_POOL[_CURSOR[0]]
    _CURSOR[0] += 1
    return g


def _build_stopwords(words):
    out = {}
    for w in words:
        out[w] = _next_glyph()
    return out


_LANGUAGE_WORDS = {
    "es": ["el", "la", "los", "las", "un", "una", "unos", "unas", "es", "son",
           "está", "están", "fue", "fueron", "ha", "han", "de", "del", "y", "o",
           "que", "en", "por", "para"],
    "fr": ["le", "la", "les", "un", "une", "des", "est", "sont", "était", "étaient",
           "a", "ont", "de", "du", "et", "ou", "que", "dans", "pour", "par", "sur"],
    "de": ["der", "die", "das", "den", "dem", "des", "ein", "eine", "einer", "eines",
           "ist", "sind", "war", "waren", "hat", "haben", "und", "oder", "in", "von",
           "mit", "für", "auf"],
    "it": ["il", "lo", "la", "i", "gli", "le", "un", "una", "è", "sono",
           "era", "erano", "ha", "hanno", "di", "del", "e", "o", "che", "in",
           "per", "con", "su"],
    "pt": ["o", "a", "os", "as", "um", "uma", "uns", "umas", "é", "são",
           "está", "estão", "foi", "foram", "tem", "têm", "de", "do", "da", "e",
           "ou", "que", "em", "para", "por", "com"],
    "hi": ["और", "का", "के", "की", "में", "से", "है", "हैं", "था", "थे",
           "थी", "ने", "को", "पर", "इस", "उस", "एक"],
    "sa": ["च", "वा", "इति", "एव", "अपि", "हि"],
    "zh": ["的", "是", "了", "在", "和", "也", "都", "就", "这", "那",
           "你", "我", "他", "她", "它"],
    "ja": ["は", "が", "を", "に", "で", "と", "も", "の", "だ", "です",
           "ます", "いる"],
    "ar": ["ال", "و", "في", "من", "على", "إلى", "عن", "أن", "إن", "هذا",
           "هذه", "كان", "كانت", "هو", "هي"],
}


LANGUAGE_MATRICES = {
    "en": {
        "name": "english",
        "script": "latin",
        "stopwords": dict(tables.ENGLISH_STOPWORD_MAP),
        "agglutination": tables.ENGLISH_AGGLOUTINATION_PHRASES,
        "particles": {},
    },
}

for _lang, _words in _LANGUAGE_WORDS.items():
    _mat_stop = _build_stopwords(list(_words))
    _script = {
        "es": "latin", "fr": "latin", "de": "latin", "it": "latin", "pt": "latin",
        "hi": "devanagari", "sa": "devanagari", "zh": "cjk", "ja": "hiragana",
        "ar": "arabic",
    }.get(_lang, "latin")
    LANGUAGE_MATRICES[_lang] = {
        "name": {"es": "spanish", "fr": "french", "de": "german", "it": "italian",
                 "pt": "portuguese", "hi": "hindi", "sa": "sanskrit", "zh": "mandarin",
                 "ja": "japanese", "ar": "arabic"}[_lang],
        "script": _script,
        "stopwords": _mat_stop,
        "agglutination": {},
        "particles": {},
    }


SCRIPT_TO_LANG = {
    "latin": "en",
    "devanagari": "hi",
    "cjk": "zh",
    "hiragana": "ja",
    "katakana": "ja",
    "arabic": "ar",
    "hebrew": "en",
    "thai": "en",
    "hangul": "en",
    "cyrillic": "en",
    "greek": "en",
}


_LATIN_HINTS = {
    "es": ["ñ", "á", "é", "í", "ó", "ú", "ü"],
    "fr": ["ç", "œ", "é", "è", "ê", "ë", "à", "â", "û", "î", "ô"],
    "de": ["ß", "ä", "ö", "ü", "Ä", "Ö", "Ü"],
    "it": ["à", "è", "é", "ì", "ò", "ù"],
    "pt": ["ã", "õ", "ç", "á", "é", "í", "ó", "ú"],
}


def _refine_latin(text, default="en"):
    lowered = text.lower()
    scores = {}
    for lang, hints in _LATIN_HINTS.items():
        s = 0
        for ch in hints:
            s += lowered.count(ch)
        if s:
            scores[lang] = s
    if not scores:
        return default
    return max(scores.items(), key=lambda kv: kv[1])[0]


def detect_language(text, default="en"):
    if not isinstance(text, str) or not text:
        return default
    from sanskrit_mesh.core.linguistics.scripts import detect_script
    script = detect_script(text)
    lang = SCRIPT_TO_LANG.get(script, default)
    if script == "latin":
        lang = _refine_latin(text, default=default)
    return lang


def get_matrix(lang):
    return LANGUAGE_MATRICES.get(lang, LANGUAGE_MATRICES["en"])
