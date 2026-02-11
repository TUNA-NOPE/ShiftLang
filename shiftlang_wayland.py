#!/usr/bin/env python3
"""ShiftLang - Wayland edition with full config support."""

import os
import sys
import subprocess
import threading
import time
import fcntl
from pathlib import Path

# ──────────────────────── Import Shared Modules ─────────────
from shiftlang import load_config, detect_is_source_language, create_translators
from shiftlang.config import CONFIG_PATH

# Thread lock to prevent race conditions when multiple input devices detect the same hotkey
_hotkey_lock = threading.Lock()

OS_NAME = "Linux"

# ──────────────────────── Single Instance Lock ─────────────
_LOCK_FILE = "/tmp/shiftlang_wayland.lock"
_lock_fd = None


def _ensure_single_instance():
    """Ensure only one instance of ShiftLang is running."""
    global _lock_fd
    _lock_fd = open(_LOCK_FILE, "w")
    try:
        fcntl.flock(_lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        _lock_fd.write(str(os.getpid()))
        _lock_fd.flush()
        return True
    except (IOError, OSError):
        print("ERROR: ShiftLang is already running!")
        print("Only one instance can run at a time.")
        return False


# ──────────────────────── Config ───────────────────────────
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
_translator_forward, _translator_reverse, _provider = create_translators(config)


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
        is_source = detect_is_source_language(text, config["source_language"])

        if _provider == "openrouter":
            # OpenRouter: Use bidirectional translation with smart language detection
            translated = _translator_forward.translate_bidirectional(text, is_source)
            # If OpenRouter failed (returned original text), fall back to Google
            if translated.strip().lower() == text.strip().lower():
                print("OpenRouter failed, falling back to Google Translate...")
                # Create Google translator for fallback
                if is_source is None:
                    fallback = GoogleTranslator(source="auto", target=config["target_language"])
                elif is_source:
                    fallback = GoogleTranslator(source=config["source_language"], target=config["target_language"])
                else:
                    fallback = GoogleTranslator(source=config["target_language"], target=config["source_language"])
                translated = fallback.translate(text)
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

        # Clear clipboard if configured to prevent history spam
        if config.get("clear_clipboard_after_paste", True):
            set_clip("")
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
        """Find keyboard input devices, filtering out non-keyboards and avoiding duplicates."""
        devs = []
        seen_physical_paths = set()
        
        for p in sorted(Path("/dev/input").glob("event*")):
            try:
                d = InputDevice(p)
                caps = d.capabilities()
                if ecodes.EV_KEY in caps:
                    keys = caps[ecodes.EV_KEY]
                    # Strict keyboard check: must have A-Z keys and be a real keyboard
                    has_alphabet = all(ecodes.KEY_A + i in keys for i in range(26))
                    has_digits = ecodes.KEY_1 in keys and ecodes.KEY_0 in keys
                    
                    # Skip if it doesn't look like a full keyboard
                    if not (has_alphabet and has_digits and ecodes.KEY_SPACE in keys):
                        continue
                    
                    # Deduplicate by physical path (some keyboards appear as multiple event devices)
                    phys = d.phys or str(p)
                    if phys in seen_physical_paths:
                        continue
                    seen_physical_paths.add(phys)
                    
                    devs.append(d)
                    print(f"DEBUG: Found keyboard: {d.name} ({p.name})")
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
            # Use lock to prevent race conditions between multiple input devices
            with _hotkey_lock:
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
    if not _ensure_single_instance():
        sys.exit(1)
    Listener().start()
