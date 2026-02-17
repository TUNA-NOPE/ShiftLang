"""Language detection utilities for ShiftLang."""

# Build a set of Unicode ranges for the source language to auto-detect direction.
# For languages with distinct scripts we can detect them; otherwise we default
# to translating source→target.

# Mapping from language codes to language names (for config compatibility)
# Config stores codes like "iw" (Hebrew) but detection uses names like "hebrew"
CODE_TO_NAME = {
    # Semitic scripts
    "he": "hebrew",
    "iw": "hebrew",  # iw is legacy code for Hebrew
    "ar": "arabic",
    "fa": "persian",
    "ur": "urdu",
    "ps": "pashto",
    "syr": "syriac",
    "mid": "mandaic",
    "dv": "thaana",
    # South Asian scripts
    "hi": "hindi",
    "bn": "bengali",
    "pa": "gurmukhi",
    "gu": "gujarati",
    "or": "oriya",
    "ta": "tamil",
    "te": "telugu",
    "kn": "kannada",
    "ml": "malayalam",
    "si": "sinhala",
    "th": "thai",
    "lo": "lao",
    "bo": "tibetan",
    "my": "myanmar",
    "km": "khmer",
    "nqo": "n'ko",
    # East Asian scripts
    "ja": "japanese",
    "zh": "chinese (simplified)",
    "zh-cn": "chinese (simplified)",
    "zh-hans": "chinese (simplified)",
    "zh-tw": "chinese (traditional)",
    "zh-hant": "chinese (traditional)",
    "ko": "korean",
    # Cyrillic scripts
    "ru": "russian",
    "uk": "ukrainian",
    "bg": "bulgarian",
    "sr": "serbian",
    "be": "belarusian",
    "mk": "macedonian",
    "mn": "mongolian",
    # European scripts
    "el": "greek",
    "ka": "georgian",
    "hy": "armenian",
    # African scripts
    "ber": "tifinagh",
    "tmh": "tifinagh",
    "so": "osmanya",  # Somali uses Osmanya script sometimes
    "bax": "bamum",
    # Other scripts
    "chr": "cherokee",
    "oj": "canadian aboriginal",
    "cr": "canadian aboriginal",
    "sga": "ogham",
    "got": "runic",
    "dsr": "deseret",
    "shw": "shavian",
    "tai": "new tai lue",
    "bug": "buginese",
    "su": "sundanese",
    "btk": "batak",
    "lep": "lepcha",
    "sat": "ol chiki",
    "saz": "saurashtra",
    "krl": "kayah li",
    "rej": "rejang",
    "xlc": "lycian",
    "xcr": "carian",
    "xld": "lydian",
    # Common languages without unique scripts (still need entries for reverse lookup)
    "en": "english",
    "es": "spanish",
    "fr": "french",
    "de": "german",
    "it": "italian",
    "pt": "portuguese",
    "nl": "dutch",
    "pl": "polish",
    "tr": "turkish",
    "vi": "vietnamese",
    "id": "indonesian",
    "ms": "malay",
    "fil": "filipino",
    "tl": "filipino",
    "sw": "swahili",
    "af": "afrikaans",
    "sq": "albanian",
    "am": "amharic",
    "az": "azerbaijani",
    "eu": "basque",
    "bs": "bosnian",
    "ca": "catalan",
    "ceb": "cebuano",
    "ny": "chichewa",
    "co": "corsican",
    "hr": "croatian",
    "cs": "czech",
    "da": "danish",
    "eo": "esperanto",
    "et": "estonian",
    "fi": "finnish",
    "fy": "frisian",
    "gl": "galician",
    "ht": "haitian creole",
    "ha": "hausa",
    "haw": "hawaiian",
    "hmn": "hmong",
    "hu": "hungarian",
    "is": "icelandic",
    "ig": "igbo",
    "ga": "irish",
    "jw": "javanese",
    "kk": "kazakh",
    "rw": "kinyarwanda",
    "ku": "kurdish (kurmanji)",
    "ky": "kyrgyz",
    "la": "latin",
    "lv": "latvian",
    "lt": "lithuanian",
    "lb": "luxembourgish",
    "mg": "malagasy",
    "mt": "maltese",
    "mi": "maori",
    "mr": "marathi",
    "ne": "nepali",
    "no": "norwegian",
    "nb": "norwegian",
    "nn": "norwegian",
    "ps": "pashto",
    "sd": "sindhi",
    "sk": "slovak",
    "sl": "slovenian",
    "so": "somali",
    "st": "sesotho",
    "sn": "shona",
    "sm": "samoan",
    "gd": "scots gaelic",
    "tg": "tajik",
    "tk": "turkmen",
    "ug": "uyghur",
    "uz": "uzbek",
    "cy": "welsh",
    "xh": "xhosa",
    "yi": "yiddish",
    "yo": "yoruba",
    "zu": "zulu",
}

LANGUAGE_UNICODE_RANGES = {
    # Semitic scripts
    "hebrew": [("\u0590", "\u05ff")],
    "arabic": [("\u0600", "\u06ff"), ("\u0750", "\u077f")],
    "persian": [("\u0600", "\u06ff"), ("\u0750", "\u077f")],
    "urdu": [("\u0600", "\u06ff"), ("\u0750", "\u077f")],
    "pashto": [("\u0600", "\u06ff"), ("\u0750", "\u077f")],
    "syriac": [("\u0700", "\u074f")],
    "mandaic": [("\u0840", "\u085f")],
    "thaana": [("\u0780", "\u07bf")],
    # South Asian scripts
    "hindi": [("\u0900", "\u097f")],
    "bengali": [("\u0980", "\u09ff")],
    "gurmukhi": [("\u0a00", "\u0a7f")],
    "gujarati": [("\u0a80", "\u0aff")],
    "oriya": [("\u0b00", "\u0b7f")],
    "tamil": [("\u0b80", "\u0bff")],
    "telugu": [("\u0c00", "\u0c7f")],
    "kannada": [("\u0c80", "\u0cff")],
    "malayalam": [("\u0d00", "\u0d7f")],
    "sinhala": [("\u0d80", "\u0dff")],
    "thai": [("\u0e00", "\u0e7f")],
    "lao": [("\u0e80", "\u0eff")],
    "tibetan": [("\u0f00", "\u0fff")],
    "myanmar": [("\u1000", "\u109f")],
    "khmer": [("\u1780", "\u17ff")],
    "n'ko": [("\u07c0", "\u07ff")],
    # East Asian scripts
    "japanese": [("\u3040", "\u309f"), ("\u30a0", "\u30ff"), ("\u4e00", "\u9fff")],
    "chinese (simplified)": [("\u4e00", "\u9fff"), ("\u3400", "\u4dbf")],
    "chinese (traditional)": [("\u4e00", "\u9fff"), ("\u3400", "\u4dbf")],
    "korean": [("\uac00", "\ud7af"), ("\u1100", "\u11ff")],
    # Cyrillic scripts
    "russian": [("\u0400", "\u04ff")],
    "ukrainian": [("\u0400", "\u04ff")],
    "bulgarian": [("\u0400", "\u04ff")],
    "serbian": [("\u0400", "\u04ff")],
    "belarusian": [("\u0400", "\u04ff")],
    "macedonian": [("\u0400", "\u04ff")],
    "mongolian": [("\u1800", "\u18af")],
    # European scripts
    "greek": [("\u0370", "\u03ff")],
    "georgian": [("\u10a0", "\u10ff")],
    "armenian": [("\u0530", "\u058f")],
    "coptic": ["\u2c80", "\u2cdf"],
    "glagolitic": [("\u2c00", "\u2c5f")],
    "vai": [("\ua500", "\ua63f")],
    # African scripts
    "tifinagh": [("\u2d30", "\u2d7f")],
    "osmanya": [("\u10480", "\u104aF")],
    "bamum": [("\ua6a0", "\ua6ff")],
    # Other scripts
    "cherokee": [("\u13a0", "\u13ff")],
    "canadian aboriginal": [("\u18b0", "\u18ff")],
    "ogham": [("\u1680", "\u169f")],
    "runic": [("\u16a0", "\u16ff")],
    "deseret": [("\u10400", "\u1044F")],
    "shavian": [("\u10450", "\u1047F")],
    "new tai lue": [("\u1980", "\u19df")],
    "buginese": [("\u1a00", "\u1a1f")],
    "sundanese": [("\u1b80", "\u1bbf")],
    "batak": [("\u1bc0", "\u1bff")],
    "lepcha": ["\u1c00", "\u1c4f"],
    "ol chiki": [("\u1c50", "\u1c7f")],
    "saurashtra": [("\ua880", "\ua8df")],
    "kayah li": [("\ua900", "\ua92f")],
    "rejang": [("\ua930", "\ua95f")],
    "lycian": ["\u10280", "\u1029F"],
    "carian": ["\u102a0", "\u102dF"],
    "lydian": ["\u10910", "\u1091F"],
}


def detect_is_source_language(text, source_language):
    """
    Check if text is written in the source language's script.
    Returns True if source language script is detected, False otherwise.
    If the source language has no known script range, we always
    translate source→target (returns None for auto-detect).
    """
    src: str = source_language.lower()

    # Map language code to name (e.g., "iw" -> "hebrew")
    lang_name: str = CODE_TO_NAME.get(src, src)

    ranges = LANGUAGE_UNICODE_RANGES.get(lang_name)
    if not ranges:
        # For Latin-script languages (e.g. spanish↔english) we can't detect
        # by script — use source='auto' detection instead
        return None  # signals "unknown, use auto-detect"

    for ch in text:
        for lo, hi in ranges:
            if lo <= ch <= hi:
                return True
    return False
