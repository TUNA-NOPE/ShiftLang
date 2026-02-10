import os
import sys
import json
import time
import platform
import keyboard
import pyperclip
from deep_translator import GoogleTranslator
from openrouter_translator import OpenRouterTranslator

# ──────────────────────── Config ───────────────────────────
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
OS_NAME = platform.system()  # 'Windows' | 'Darwin' | 'Linux'

# Default hotkeys per OS
_DEFAULT_HOTKEYS = {
    "Windows": "ctrl+shift+q",
    "Darwin": "cmd+shift+g",
    "Linux": "alt+shift+g",
}


def load_config():
    """Load user preferences from config.json, with sensible defaults."""
    defaults = {
        "hotkey": _DEFAULT_HOTKEYS.get(OS_NAME, "ctrl+shift+q"),
        "auto_start": False,
        "source_language": "hebrew",
        "target_language": "english",
        "translation_provider": "google",  # "google" or "openrouter"
        "openrouter_api_key": "",  # Optional API key for OpenRouter
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                cfg = json.load(f)
            defaults.update(cfg)
        except Exception:
            pass
    return defaults


config = load_config()
print(f"DEBUG: Loaded config: {config}")
print(f"DEBUG: Hotkey to register: {config['hotkey']}")

# ──────────────────────── Translators (cached) ─────────────
# Two translators: source→target and target→source for bidirectional translation
# Select translator based on config
def _create_translators():
    """Create translator instances based on configured provider."""
    provider = config.get("translation_provider", "google").lower()

    if provider == "openrouter":
        api_key = config.get("openrouter_api_key", "")
        model = config.get("openrouter_model", "openrouter/free")
        forward = OpenRouterTranslator(
            source=config["source_language"],
            target=config["target_language"],
            api_key=api_key,
            model=model
        )
        reverse = OpenRouterTranslator(
            source=config["target_language"],
            target=config["source_language"],
            api_key=api_key,
            model=model
        )
        print(f"Using OpenRouter AI translator (model: {model})")
    else:  # default to google
        forward = GoogleTranslator(
            source=config["source_language"],
            target=config["target_language"],
        )
        reverse = GoogleTranslator(
            source=config["target_language"],
            target=config["source_language"],
        )
        print(f"Using Google Translator")

    return forward, reverse

_translator_forward, _translator_reverse = _create_translators()

# ──────────────────────── Language Detection Helper ────────
# Build a set of Unicode ranges for the source language to auto-detect direction.
# For languages with distinct scripts we can detect them; otherwise we default
# to translating source→target.

_LANGUAGE_UNICODE_RANGES = {
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


def _detect_is_source_language(text):
    """
    Check if text is written in the source language's script.
    Returns True if source language script is detected, False otherwise.
    If the source language has no known script range, we always
    translate source→target (returns False).
    """
    src = config["source_language"].lower()
    ranges = _LANGUAGE_UNICODE_RANGES.get(src)
    if not ranges:
        # For Latin-script languages (e.g. spanish↔english) we can't detect
        # by script — use source='auto' detection instead
        return None  # signals "unknown, use auto-detect"

    for ch in text:
        for lo, hi in ranges:
            if lo <= ch <= hi:
                return True
    return False


# ──────────────────────── Clipboard (cross-platform) ──────
if OS_NAME == "Windows":
    import ctypes

    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002

    _exclude_format_id = ctypes.windll.user32.RegisterClipboardFormatW(
        "ExcludeClipboardContentFromMonitorProcessing"
    )
    _can_include_format_id = ctypes.windll.user32.RegisterClipboardFormatW(
        "CanIncludeInClipboardHistory"
    )

    _ZERO_DWORD = (ctypes.c_byte * 4)(0, 0, 0, 0)
    _user32 = ctypes.windll.user32
    _kernel32 = ctypes.windll.kernel32

    def _set_clipboard_exclusion_flag(format_id):
        h_mem = _kernel32.GlobalAlloc(GMEM_MOVEABLE, 4)
        if h_mem:
            p_mem = _kernel32.GlobalLock(h_mem)
            ctypes.memmove(p_mem, _ZERO_DWORD, 4)
            _kernel32.GlobalUnlock(h_mem)
            _user32.SetClipboardData(format_id, h_mem)

    def _set_clipboard_text(text):
        text_bytes = text.encode("utf-16le") + b"\x00\x00"
        h_mem = _kernel32.GlobalAlloc(GMEM_MOVEABLE, len(text_bytes))
        if h_mem:
            p_mem = _kernel32.GlobalLock(h_mem)
            ctypes.memmove(p_mem, text_bytes, len(text_bytes))
            _kernel32.GlobalUnlock(h_mem)
            _user32.SetClipboardData(CF_UNICODETEXT, h_mem)

    def copy_to_clipboard_no_history(text):
        try:
            if not _user32.OpenClipboard(None):
                return False
            _user32.EmptyClipboard()
            _set_clipboard_text(text)
            _set_clipboard_exclusion_flag(_exclude_format_id)
            _set_clipboard_exclusion_flag(_can_include_format_id)
            _user32.CloseClipboard()
            return True
        except Exception as e:
            print(f"Clipboard error: {e}")
            try:
                _user32.CloseClipboard()
            except Exception:
                pass
            return False

    def exclude_current_clipboard_from_history():
        try:
            if not _user32.OpenClipboard(None):
                return
            h_data = _user32.GetClipboardData(CF_UNICODETEXT)
            if not h_data:
                _user32.CloseClipboard()
                return
            p_data = _kernel32.GlobalLock(h_data)
            text = ctypes.wstring_at(p_data)
            _kernel32.GlobalUnlock(h_data)
            _user32.EmptyClipboard()
            _set_clipboard_text(text)
            _set_clipboard_exclusion_flag(_exclude_format_id)
            _set_clipboard_exclusion_flag(_can_include_format_id)
            _user32.CloseClipboard()
        except Exception as e:
            print(f"Clipboard exclusion error: {e}")
            try:
                _user32.CloseClipboard()
            except Exception:
                pass

else:
    # macOS / Linux — use pyperclip (no history-exclusion API available)
    def copy_to_clipboard_no_history(text):
        try:
            pyperclip.copy(text)
            return True
        except Exception as e:
            print(f"Clipboard error: {e}")
            return False

    def exclude_current_clipboard_from_history():
        pass  # Not available on macOS/Linux


# ──────────────────────── Copy / Paste keys per OS ─────────
if OS_NAME == "Darwin":
    _COPY_KEYS = "command+c"
    _PASTE_KEYS = "command+v"
else:
    _COPY_KEYS = "ctrl+c"
    _PASTE_KEYS = "ctrl+v"


# ──────────────────────── Translation Logic ────────────────
_is_translating = False


def _get_hotkey_modifier_keys():
    """Extract modifier key names from the configured hotkey for release-wait."""
    parts = config["hotkey"].replace("+", " ").split()
    modifiers = {"ctrl", "shift", "alt", "cmd", "command", "option", "meta", "win"}
    return [p for p in parts if p.lower() in modifiers]


def translate_text():
    global _is_translating

    if _is_translating:
        return

    _is_translating = True
    try:
        # 1. Wait for hotkey keys to be released
        mod_keys = _get_hotkey_modifier_keys()
        for _ in range(20):
            if not any(keyboard.is_pressed(key) for key in mod_keys):
                break
            time.sleep(0.05)

        # 2. Clear clipboard, then copy selected text
        pyperclip.copy("")
        time.sleep(0.05)

        keyboard.press_and_release(_COPY_KEYS)

        # 3. Read clipboard with retry
        text_to_translate = ""
        for attempt in range(10):
            time.sleep(0.1)
            text_to_translate = pyperclip.paste()
            if text_to_translate.strip():
                break

        if not text_to_translate.strip():
            print("No text selected or clipboard empty.")
            return

        # 4. Exclude copied text from clipboard history (Windows only)
        exclude_current_clipboard_from_history()

        print(f"Original: {text_to_translate}")

        # 5. Detect direction & translate
        provider = config.get("translation_provider", "google").lower()
        is_source = _detect_is_source_language(text_to_translate)

        if provider == "openrouter":
            # OpenRouter: Use LLM's intelligence to detect language automatically
            # Try forward translation first
            translated = _translator_forward.translate(text_to_translate)
            # If result is same as input, try reverse
            if translated.strip().lower() == text_to_translate.strip().lower():
                translated = _translator_reverse.translate(text_to_translate)
        else:
            # Google Translator: Use script-based detection
            if is_source is None:
                # Both languages use Latin script — use auto-detect
                # Try translating with source='auto'; if detected as target lang,
                # translate into source lang, and vice versa.
                auto_translator = GoogleTranslator(
                    source="auto", target=config["target_language"]
                )
                translated = auto_translator.translate(text_to_translate)
                # If auto resulted in the same text, try the reverse direction
                if (
                    translated
                    and translated.strip().lower() == text_to_translate.strip().lower()
                ):
                    auto_translator = GoogleTranslator(
                        source="auto", target=config["source_language"]
                    )
                    translated = auto_translator.translate(text_to_translate)
            elif is_source:
                # Text is in source language → translate to target
                translated = _translator_forward.translate(text_to_translate)
            else:
                # Text is in target language → translate to source
                translated = _translator_reverse.translate(text_to_translate)

        print(f"Translated: {translated}")

        # 6. Paste translated text
        if copy_to_clipboard_no_history(translated):
            keyboard.press_and_release(_PASTE_KEYS)
            time.sleep(0.1)
        else:
            print("Failed to copy to clipboard.")

    except Exception as e:
        print(f"Translation error: {e}")
    finally:
        _is_translating = False


# ──────────────────────── Main ─────────────────────────────
def main():
    hotkey = config["hotkey"]
    src = config["source_language"]
    tgt = config["target_language"]
    print(f"ShiftLang running — {src} ↔ {tgt}")
    print(f"Press {hotkey} to translate selected text.")
    print(f"OS: {OS_NAME}")
    keyboard.add_hotkey(hotkey, translate_text)
    keyboard.wait()


if __name__ == "__main__":
    main()
