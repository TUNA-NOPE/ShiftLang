import os
import sys
import traceback

# ──────────────────────── Fix Windows Console Encoding ─────────────────────
# Windows may use a legacy codepage (e.g., cp1255 for Hebrew) that cannot
# encode all Unicode characters. Force UTF-8 to prevent UnicodeEncodeError.
if sys.platform == "win32" and sys.stdout:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        pass  # Fallback: continue with default encoding

# Add parent directory to path for importing shiftlang package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Log file for debugging startup errors
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shiftlang_error.log")

def log_error(title, message, exc_info=None):
    """Log error to file for debugging."""
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"{'='*60}\n")
            f.write(f"ERROR: {title}\n")
            f.write(f"{'='*60}\n")
            f.write(f"{message}\n")
            if exc_info:
                f.write(f"\nTraceback:\n{exc_info}\n")
            f.write(f"\nPython: {sys.executable}\n")
            f.write(f"Python Version: {sys.version}\n")
            f.write(f"Working Directory: {os.getcwd()}\n")
            f.write(f"Python Path: {sys.path}\n")
            f.write(f"{'='*60}\n")
    except Exception:
        pass  # If logging fails, continue to show error

def show_error_and_pause(title, message, exc_info=None):
    """Show error message and wait for key press before exiting."""
    # Log error first
    log_error(title, message, exc_info)
    
    # Ensure we're using a console for output (not pythonw.exe)
    if sys.stdout is None or sys.stderr is None:
        # Reattach to console if running as pythonw
        try:
            import ctypes
            ctypes.windll.kernel32.AllocConsole()
            sys.stdout = open('CONOUT$', 'w')
            sys.stderr = sys.stdout
        except Exception:
            pass  # Can't create console, just exit
    
    print(f"\n{'='*60}")
    print(f"ERROR: {title}")
    print(f"{'='*60}")
    print(message)
    if exc_info:
        print(f"\nTraceback:\n{exc_info}")
    print(f"\n{'='*60}")
    print(f"Error log saved to: {LOG_FILE}")
    print(f"{'='*60}")
    print("\nPress Enter to exit...")
    try:
        input()
    except:
        try:
            import msvcrt
            msvcrt.getch()
        except:
            pass
    sys.exit(1)

# Wrap all imports in try-except to catch startup errors
try:
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
except ImportError as e:
    tb = traceback.format_exc()
    show_error_and_pause(
        "Import Error",
        f"Failed to import required module: {e}\n\n"
        f"Make sure all dependencies are installed:\n"
        f"  {sys.executable} -m pip install -r requirements/requirements.txt",
        tb
    )
except Exception as e:
    tb = traceback.format_exc()
    show_error_and_pause("Initialization Error", str(e), tb)

try:
    config = load_config()
    print(f"DEBUG: Loaded config: {config}")
    print(f"DEBUG: Hotkey to register: {config['hotkey']}")
except Exception as e:
    show_error_and_pause("Config Load Error", f"Failed to load config: {e}")

# ──────────────────────── Translators (cached) ─────────────
try:
    _translator_forward, _translator_reverse, _provider = create_translators(config)
except Exception as e:
    show_error_and_pause("Translator Init Error", f"Failed to create translators: {e}")

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
_MIN_TRANSLATION_INTERVAL = 1.5  # Minimum seconds between translations (increased to prevent double-trigger)


def _get_hotkey_modifier_keys():
    """Extract modifier key names from the configured hotkey for release-wait."""
    parts = config["hotkey"].replace("+", " ").split()
    modifiers = {"ctrl", "shift", "alt", "cmd", "command", "option", "meta", "win"}
    return [p for p in parts if p.lower() in modifiers]


def translate_text():
    global _is_translating, _last_translation_time

    # Debounce: prevent rapid re-triggering
    current_time = time.time()
    if _is_translating:
        print("Translation already in progress, ignoring hotkey")
        return
    
    if current_time - _last_translation_time < _MIN_TRANSLATION_INTERVAL:
        print(f"Translation debounced - too soon since last translation ({current_time - _last_translation_time:.2f}s < {_MIN_TRANSLATION_INTERVAL}s)")
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
    
    # Ensure console is visible for debugging (comment out for production)
    print(f"ShiftLang running — {src} ↔ {tgt}")
    print(f"Press {hotkey} to translate selected text.")
    print(f"OS: {OS_NAME}")
    print(f"Provider: {_provider}")
    print("")
    print("Running in background... (Press Ctrl+C to stop)")
    print("")
    
    try:
        keyboard.add_hotkey(hotkey, translate_text)
        keyboard.wait()
    except Exception as e:
        tb = traceback.format_exc()
        show_error_and_pause("Runtime Error", f"Failed to register hotkey or run: {e}", tb)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nShiftLang stopped by user.")
        sys.exit(0)
    except Exception as e:
        tb = traceback.format_exc()
        show_error_and_pause("Fatal Error", str(e), tb)
