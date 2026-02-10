import os
import sys
import json
import time
import platform
import keyboard
import pyperclip
from deep_translator import GoogleTranslator

# ──────────────────────── Config ───────────────────────────
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
OS_NAME = platform.system()  # 'Windows' | 'Darwin' | 'Linux'

# Default hotkeys per OS
_DEFAULT_HOTKEYS = {
    "Windows": "ctrl+shift+q",
    "Darwin":  "cmd+shift+g",
    "Linux":   "alt+shift+g",
}


def load_config():
    """Load user preferences from config.json, with sensible defaults."""
    defaults = {
        "hotkey": _DEFAULT_HOTKEYS.get(OS_NAME, "ctrl+shift+q"),
        "auto_start": False,
        "source_language": "hebrew",
        "target_language": "english",
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
_translator_forward = GoogleTranslator(
    source=config["source_language"],
    target=config["target_language"],
)
_translator_reverse = GoogleTranslator(
    source=config["target_language"],
    target=config["source_language"],
)

# ──────────────────────── Language Detection Helper ────────
# Build a set of Unicode ranges for the source language to auto-detect direction.
# For languages with distinct scripts we can detect them; otherwise we default
# to translating source→target.

_LANGUAGE_UNICODE_RANGES = {
    "hebrew":     [("\u0590", "\u05FF")],
    "arabic":     [("\u0600", "\u06FF"), ("\u0750", "\u077F")],
    "persian":    [("\u0600", "\u06FF"), ("\u0750", "\u077F")],
    "urdu":       [("\u0600", "\u06FF"), ("\u0750", "\u077F")],
    "hindi":      [("\u0900", "\u097F")],
    "bengali":    [("\u0980", "\u09FF")],
    "thai":       [("\u0E00", "\u0E7F")],
    "korean":     [("\uAC00", "\uD7AF"), ("\u1100", "\u11FF")],
    "japanese":   [("\u3040", "\u309F"), ("\u30A0", "\u30FF"), ("\u4E00", "\u9FFF")],
    "chinese (simplified)":  [("\u4E00", "\u9FFF"), ("\u3400", "\u4DBF")],
    "chinese (traditional)": [("\u4E00", "\u9FFF"), ("\u3400", "\u4DBF")],
    "russian":    [("\u0400", "\u04FF")],
    "ukrainian":  [("\u0400", "\u04FF")],
    "bulgarian":  [("\u0400", "\u04FF")],
    "serbian":    [("\u0400", "\u04FF")],
    "greek":      [("\u0370", "\u03FF")],
    "georgian":   [("\u10A0", "\u10FF")],
    "armenian":   [("\u0530", "\u058F")],
    "tamil":      [("\u0B80", "\u0BFF")],
    "telugu":     [("\u0C00", "\u0C7F")],
    "kannada":    [("\u0C80", "\u0CFF")],
    "malayalam":  [("\u0D00", "\u0D7F")],
    "gujarati":   [("\u0A80", "\u0AFF")],
    "punjabi":    [("\u0A00", "\u0A7F")],
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
        text_bytes = text.encode('utf-16le') + b'\x00\x00'
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
        pyperclip.copy('')
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
        is_source = _detect_is_source_language(text_to_translate)

        if is_source is None:
            # Both languages use Latin script — use auto-detect
            # Try translating with source='auto'; if detected as target lang,
            # translate into source lang, and vice versa.
            auto_translator = GoogleTranslator(source='auto', target=config["target_language"])
            translated = auto_translator.translate(text_to_translate)
            # If auto resulted in the same text, try the reverse direction
            if translated and translated.strip().lower() == text_to_translate.strip().lower():
                auto_translator = GoogleTranslator(source='auto', target=config["source_language"])
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
