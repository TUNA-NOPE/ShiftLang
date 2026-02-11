import os
import sys
import json
import time
import platform
import keyboard
import pyperclip
from deep_translator import GoogleTranslator
from shiftlang import OpenRouterTranslator

# ──────────────────────── Import Shared Modules ─────────────
from shiftlang import load_config, detect_is_source_language, create_translators
from shiftlang.config import OS_NAME, CONFIG_PATH

config = load_config()
print(f"DEBUG: Loaded config: {config}")
print(f"DEBUG: Hotkey to register: {config['hotkey']}")

# ──────────────────────── Translators (cached) ─────────────
_translator_forward, _translator_reverse, _provider = create_translators(config)

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
_last_translation_time = 0
_MIN_TRANSLATION_INTERVAL = 0.5  # Minimum seconds between translations


def _get_hotkey_modifier_keys():
    """Extract modifier key names from the configured hotkey for release-wait."""
    parts = config["hotkey"].replace("+", " ").split()
    modifiers = {"ctrl", "shift", "alt", "cmd", "command", "option", "meta", "win"}
    return [p for p in parts if p.lower() in modifiers]


def translate_text():
    global _is_translating, _last_translation_time

    # Debounce: prevent rapid re-triggering
    current_time = time.time()
    if current_time - _last_translation_time < _MIN_TRANSLATION_INTERVAL:
        print("Translation debounced - too soon since last translation")
        return
    
    if _is_translating:
        return

    _is_translating = True
    _last_translation_time = current_time
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
        is_source = detect_is_source_language(text_to_translate, config["source_language"])

        if _provider == "openrouter":
            # OpenRouter: Use bidirectional translation with smart language detection
            translated = _translator_forward.translate_bidirectional(text_to_translate, is_source)
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

        # Validate translation result
        if not translated or translated.strip() == text_to_translate.strip():
            print("Translation returned same text - skipping paste")
            return
        
        # Check for doubled text (heuristic: if translation contains the original twice)
        original_stripped = text_to_translate.strip()
        translated_stripped = translated.strip()
        if len(translated_stripped) >= len(original_stripped) * 2:
            # Check if it's doubled
            if original_stripped in translated_stripped and translated_stripped.count(original_stripped) >= 2:
                print("Warning: Detected doubled text in translation, using first half only")
                # Try to extract just the first half
                mid = len(translated_stripped) // 2
                if translated_stripped[:mid] == translated_stripped[mid:]:
                    translated = translated_stripped[:mid]

        # 6. Paste translated text
        if copy_to_clipboard_no_history(translated):
            # Small delay to ensure clipboard is ready
            time.sleep(0.05)
            keyboard.press_and_release(_PASTE_KEYS)
            time.sleep(0.15)

            # 7. Clear clipboard if configured to prevent history spam
            if config.get("clear_clipboard_after_paste", True):
                pyperclip.copy("")
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
