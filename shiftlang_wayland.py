#!/usr/bin/env python3
"""ShiftLang - Wayland edition with full config support."""

import os
import sys
import json
import subprocess
import threading
import time
from pathlib import Path

OS_NAME = "Linux"

# ──────────────────────── Config ───────────────────────────
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

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
        except Exception as e:
            print(f"Config load error: {e}")
    return defaults


config = load_config()
print(f"DEBUG: Loaded config: {config}")
print(f"DEBUG: Hotkey to register: {config['hotkey']}")

try:
    from evdev import InputDevice, categorize, ecodes
    from deep_translator import GoogleTranslator
    from openrouter_translator import OpenRouterTranslator
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install evdev deep-translator")
    sys.exit(1)

# ──────────────────────── Translators (cached) ─────────────
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
_LANGUAGE_UNICODE_RANGES = {
    "hebrew": [("\u0590", "\u05ff")],
    "arabic": [("\u0600", "\u06ff"), ("\u0750", "\u077f")],
    "persian": [("\u0600", "\u06ff"), ("\u0750", "\u077f")],
    "urdu": [("\u0600", "\u06ff"), ("\u0750", "\u077f")],
    "hindi": [("\u0900", "\u097f")],
    "bengali": [("\u0980", "\u09ff")],
    "thai": [("\u0e00", "\u0e7f")],
    "korean": [("\uac00", "\ud7af"), ("\u1100", "\u11ff")],
    "japanese": [("\u3040", "\u309f"), ("\u30a0", "\u30ff"), ("\u4e00", "\u9fff")],
    "chinese (simplified)": [("\u4e00", "\u9fff"), ("\u3400", "\u4dbf")],
    "chinese (traditional)": [("\u4e00", "\u9fff"), ("\u3400", "\u4dbf")],
    "russian": [("\u0400", "\u04ff")],
    "ukrainian": [("\u0400", "\u04ff")],
    "bulgarian": [("\u0400", "\u04ff")],
    "serbian": [("\u0400", "\u04ff")],
    "greek": [("\u0370", "\u03ff")],
    "georgian": [("\u10a0", "\u10ff")],
    "armenian": [("\u0530", "\u058f")],
    "tamil": [("\u0b80", "\u0bff")],
    "telugu": [("\u0c00", "\u0c7f")],
    "kannada": [("\u0c80", "\u0cff")],
    "malayalam": [("\u0d00", "\u0d7f")],
    "gujarati": [("\u0a80", "\u0aff")],
    "punjabi": [("\u0a00", "\u0a7f")],
}


def _detect_is_source_language(text):
    """
    Check if text is written in the source language's script.
    Returns True if source language script is detected, False otherwise.
    If the source language has no known script range, we always
    translate source→target (returns None for auto-detect).
    """
    src = config["source_language"].lower()
    ranges = _LANGUAGE_UNICODE_RANGES.get(src)
    if not ranges:
        return None  # signals "unknown, use auto-detect"

    for ch in text:
        for lo, hi in ranges:
            if lo <= ch <= hi:
                return True
    return False


# ──────────────────────── Clipboard ────────────────────────
def get_clip():
    """Read clipboard via wl-paste."""
    r = subprocess.run(["wl-paste", "--no-newline"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def set_clip(text):
    """Write to clipboard via wl-copy."""
    proc = None
    try:
        # Use communicate() to properly send data and wait
        proc = subprocess.Popen(
            ["wl-copy"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if proc.stdin is not None:
            proc.stdin.write(text.encode())
            proc.stdin.close()
        # Wait for process to finish with timeout
        proc.wait(timeout=0.5)
    except subprocess.TimeoutExpired:
        if proc:
            proc.kill()
    except Exception as e:
        print(f"Clipboard write error: {e}")


# ──────────────────────── Key Sending ──────────────────────
def send_keys(keys):
    """Send keys via wtype."""
    parts = keys.lower().split("+")
    if len(parts) == 2 and parts[0] in ("ctrl", "control"):
        subprocess.run(
            ["wtype", "-M", "ctrl", "-k", parts[1], "-m", "ctrl"], capture_output=True
        )
    else:
        subprocess.run(["wtype", "-k", keys.lower()], capture_output=True)


# ──────────────────────── Translation ──────────────────────
_COPY_KEYS = "ctrl+c"
_PASTE_KEYS = "ctrl+v"


def translate():
    """Main translation flow."""
    time.sleep(0.2)  # Wait for hotkey release

    orig = get_clip()
    send_keys(_COPY_KEYS)
    time.sleep(0.2)  # Wait for copy to complete

    # Wait for clipboard with longer timeout
    text = ""
    for _ in range(20):  # 20 * 0.1s = 2 seconds max
        time.sleep(0.1)
        text = get_clip()
        if text and text != orig:
            break

    if not text:
        print("No text selected or clipboard empty.")
        return

    print(f"Original: {text}")

    # Detect direction & translate
    try:
        provider = config.get("translation_provider", "google").lower()
        is_source = _detect_is_source_language(text)

        if provider == "openrouter":
            # OpenRouter: Use LLM's intelligence to detect language automatically
            # Try forward translation first
            translated = _translator_forward.translate(text)
            # If result is same as input, try reverse
            if translated.strip().lower() == text.strip().lower():
                translated = _translator_reverse.translate(text)
        else:
            # Google Translator: Use script-based detection
            if is_source is None:
                # Both languages use Latin script — use auto-detect
                auto_translator = GoogleTranslator(
                    source="auto", target=config["target_language"]
                )
                translated = auto_translator.translate(text)
                # If auto resulted in the same text, try the reverse direction
                if translated and translated.strip().lower() == text.strip().lower():
                    auto_translator = GoogleTranslator(
                        source="auto", target=config["source_language"]
                    )
                    translated = auto_translator.translate(text)
            elif is_source:
                # Text is in source language → translate to target
                translated = _translator_forward.translate(text)
            else:
                # Text is in target language → translate to source
                translated = _translator_reverse.translate(text)

        print(f"Translated: {translated}")

        # Paste - need more time for clipboard to update
        set_clip(translated)
        time.sleep(0.3)  # Wait for wl-copy to finish
        send_keys(_PASTE_KEYS)
        time.sleep(0.1)
    except Exception as e:
        print(f"Translation error: {e}")


# ──────────────────────── Hotkey Parsing ───────────────────
def parse_hotkey(hotkey_str):
    """Parse hotkey string into list of ecodes."""
    parts = hotkey_str.lower().replace(" ", "").split("+")
    codes = []

    key_map = {
        "ctrl": (ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL),
        "control": (ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL),
        "shift": (ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT),
        "alt": (ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT),
        "meta": (ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA),
        "cmd": (ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA),
        "command": (ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA),
        "win": (ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA),
        "q": (ecodes.KEY_Q,),
        "g": (ecodes.KEY_G,),
        "t": (ecodes.KEY_T,),
        "a": (ecodes.KEY_A,),
        "c": (ecodes.KEY_C,),
        "v": (ecodes.KEY_V,),
        "x": (ecodes.KEY_X,),
        "z": (ecodes.KEY_Z,),
    }

    for part in parts:
        if part in key_map:
            codes.append(key_map[part])
        elif len(part) == 1 and part.isalpha():
            # Single letter keys
            key_code = getattr(ecodes, f"KEY_{part.upper()}", None)
            if key_code:
                codes.append((key_code,))

    return codes


def check_hotkey(pressed_codes, hotkey_codes):
    """Check if all hotkey codes are pressed."""
    for code_tuple in hotkey_codes:
        if not any(code in pressed_codes for code in code_tuple):
            return False
    return True


# ──────────────────────── Input Listener ───────────────────
class Listener:
    def __init__(self):
        self.pressed = set()
        self.last_trigger = 0
        self.busy = False
        self.hotkey_codes = parse_hotkey(config["hotkey"])
        print(f"DEBUG: Parsed hotkey codes: {self.hotkey_codes}")

    def find_devs(self):
        """Find keyboard input devices."""
        devs = []
        for p in Path("/dev/input").glob("event*"):
            try:
                d = InputDevice(p)
                caps = d.capabilities()
                if ecodes.EV_KEY in caps:
                    keys = caps[ecodes.EV_KEY]
                    # Check if it has typical keyboard keys
                    if ecodes.KEY_A in keys and ecodes.KEY_SPACE in keys:
                        devs.append(d)
                        print(f"DEBUG: Found keyboard: {d.name}")
            except (PermissionError, OSError):
                pass
        return devs

    def handle(self, ev):
        if ev.type != ecodes.EV_KEY:
            return

        e = categorize(ev)
        if e.keystate == e.key_down:
            self.pressed.add(e.scancode)
        elif e.keystate == e.key_up:
            self.pressed.discard(e.scancode)

        # Check hotkey
        if check_hotkey(self.pressed, self.hotkey_codes):
            now = time.time()
            if now - self.last_trigger < 1.5 or self.busy:
                return
            self.last_trigger = now
            self.busy = True
            self.pressed.clear()

            def run():
                try:
                    translate()
                finally:
                    self.busy = False

            threading.Thread(target=run, daemon=True).start()

    def monitor(self, d):
        """Monitor a single input device."""
        try:
            for ev in d.read_loop():
                self.handle(ev)
        except Exception as e:
            print(f"Device error: {e}")

    def start(self):
        devs = self.find_devs()
        if not devs:
            print("ERROR: No keyboard devices found.")
            print("Make sure you're in the 'input' group:")
            print("  sudo usermod -a -G input $USER")
            print("Then log out and log back in.")
            return False

        src = config["source_language"]
        tgt = config["target_language"]
        hotkey = config["hotkey"]

        print(f"\n{'=' * 50}")
        print(f"ShiftLang Wayland Edition")
        print(f"{'=' * 50}")
        print(f"Translation: {src} ↔ {tgt}")
        print(f"Hotkey: {hotkey}")
        print(f"Keyboards detected: {len(devs)}")
        print(f"Config: {CONFIG_PATH}")
        print(f"{'=' * 50}\n")
        print(f"Press {hotkey} to translate selected text")
        print("Press Ctrl+C to exit\n")

        for d in devs:
            threading.Thread(target=self.monitor, args=(d,), daemon=True).start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nGoodbye!")
        return True


# ──────────────────────── Main ─────────────────────────────
if __name__ == "__main__":
    Listener().start()
