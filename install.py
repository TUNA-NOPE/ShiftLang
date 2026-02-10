#!/usr/bin/env python3
"""
ShiftLang Installer — One-step setup & update
Run:  python install.py          (interactive)
Run:  python install.py --auto   (silent/automatic)
Run:  python install.py --update (update existing install)
"""

import os
import sys
import json
import platform
import subprocess
import shutil
import argparse
import time

# ──────────────────────── Constants ────────────────────────
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_NAME = "ShiftLang"
OS_NAME = platform.system()

# Detect display server on Linux
IS_WAYLAND = False
if OS_NAME == "Linux":
    IS_WAYLAND = (
        os.environ.get("WAYLAND_DISPLAY") is not None
        or "wayland" in os.environ.get("XDG_SESSION_TYPE", "").lower()
    )

MAIN_SCRIPT = os.path.join(
    PROJECT_DIR, "shiftlang_wayland.py" if IS_WAYLAND else "main.pyw"
)

DEFAULTS = {
    "Windows": "ctrl+shift+q",
    "Darwin": "ctrl+shift+q",
    "Linux": "ctrl+shift+q",
}


# ──────────────────────── Helpers ──────────────────────────
def clear_screen():
    os.system("cls" if OS_NAME == "Windows" else "clear")


def color(text, code):
    """ANSI color wrapper."""
    if OS_NAME == "Windows":
        try:
            os.system("")  # enable ANSI on Windows 10+
        except Exception:
            pass
    return f"\033[{code}m{text}\033[0m"


def green(t):
    return color(t, "92")


def cyan(t):
    return color(t, "96")


def yellow(t):
    return color(t, "93")


def red(t):
    return color(t, "91")


def bold(t):
    return color(t, "1")


def dim(t):
    return color(t, "2")


def banner():
    print()
    print(cyan("   ╭───────────────────────────────────────────────╮"))
    print(cyan("   │                                               │"))
    print(
        cyan("   │     ") + bold("⚡  S H I F T L A N G  ⚡") + cyan("              │")
    )
    print(cyan("   │                                               │"))
    print(cyan("   │     ") + dim("Instant translation, any language") + cyan("     │"))
    if IS_WAYLAND:
        print(
            cyan("   │     ")
            + dim("Running on Wayland")
            + cyan("                    │")
        )
    print(cyan("   │                                               │"))
    print(cyan("   ╰───────────────────────────────────────────────╯"))
    print()
    print()


# ──────────────────────── Linux Input Group Check ──────────
def check_input_group():
    """Check if user is in input group (required for Wayland)."""
    if OS_NAME != "Linux":
        return True

    try:
        import grp

        user = os.environ.get("USER", os.environ.get("USERNAME", ""))
        input_group = grp.getgrnam("input")
        return user in input_group.gr_mem
    except:
        return False


def add_user_to_input_group():
    """Add current user to input group."""
    user = os.environ.get("USER", os.environ.get("USERNAME", ""))
    print(dim(f"    Adding {user} to input group..."))
    try:
        result = subprocess.run(
            ["sudo", "usermod", "-a", "-G", "input", user],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(green("    ✓") + " User added to input group")
            print(yellow("    ⚠ Log out and back in for changes to take effect"))
            return True
        else:
            print(red(f"    ✗ Failed: {result.stderr}"))
            return False
    except Exception as e:
        print(red(f"    ✗ Error: {e}"))
        return False


# ──────────────────────── Prerequisite Checks ──────────────
def check_python():
    v = sys.version_info
    print(f"    Python {v.major}.{v.minor}.{v.micro}", end=" ")
    if v >= (3, 8):
        print(green("✓"))
        return True
    else:
        print(red("✗"))
        print(red(f"    ShiftLang requires Python 3.8+"))
        return False


def check_pip():
    print("    pip", end=" ")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(green("✓"))
        return True
    except Exception:
        print(red("✗"))
        print(red("    Please install pip first"))
        return False


def check_git():
    print("    git", end=" ")
    if shutil.which("git"):
        print(green("✓"))
        return True
    else:
        print(dim("(optional)"))
        return True


# ──────────────────────── Virtual Environment ──────────────
VENV_DIR = os.path.join(PROJECT_DIR, ".venv")
VENV_PYTHON = (
    os.path.join(VENV_DIR, "bin", "python")
    if OS_NAME != "Windows"
    else os.path.join(VENV_DIR, "Scripts", "python.exe")
)


def has_uv():
    """Check if uv is available."""
    return shutil.which("uv") is not None


def create_virtualenv():
    """Create a virtual environment in the project directory."""
    print(dim(f"    Creating virtual environment..."))

    # Try uv first (faster)
    if has_uv():
        result = subprocess.run(
            ["uv", "venv", VENV_DIR], cwd=PROJECT_DIR, capture_output=True, text=True
        )
        if result.returncode == 0:
            print(green("    ✓") + " Virtual environment created")
            return True
        else:
            print(dim(f"    uv failed, trying standard venv..."))

    # Fall back to standard venv
    try:
        result = subprocess.run(
            [sys.executable, "-m", "venv", VENV_DIR],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(green("    ✓") + " Virtual environment created")
            return True
        else:
            print(red(f"    ✗ venv creation failed: {result.stderr}"))
            return False
    except Exception as e:
        print(red(f"    ✗ Failed to create venv: {e}"))
        return False


# ──────────────────────── Install dependencies ─────────────
def install_dependencies():
    # Use Linux-specific requirements if on Linux, otherwise use base requirements
    req_file = "requirements-linux.txt" if OS_NAME == "Linux" else "requirements.txt"
    req = os.path.join(PROJECT_DIR, req_file)
    if not os.path.exists(req):
        print(red(f"    ✗ {req_file} not found"))
        return False

    # Create venv if it doesn't exist
    if not os.path.exists(VENV_PYTHON):
        if not create_virtualenv():
            return False
        print()

    # Install into venv
    print(dim("    Installing dependencies..."))
    print()

    # Try uv pip (fastest)
    if has_uv():
        result = subprocess.run(
            ["uv", "pip", "install", "-r", req, "--python", VENV_PYTHON],
            cwd=PROJECT_DIR,
        )
        if result.returncode == 0:
            print()
            print(green("    ✓") + " Dependencies installed")
            return True
        else:
            print(dim("    Trying alternative method..."))

    # Fall back to venv pip
    result = subprocess.run(
        [VENV_PYTHON, "-m", "pip", "install", "-r", req],
        cwd=PROJECT_DIR,
    )
    print()
    if result.returncode == 0:
        print(green("    ✓") + " Dependencies installed")
        return True
    else:
        print(red("    ✗ Failed to install dependencies"))
        return False


# ──────────────────────── Fetch Supported Languages ────────
def get_supported_languages():
    """Fetch the supported languages from GoogleTranslator as a dict."""
    try:
        from deep_translator import GoogleTranslator

        langs_dict = GoogleTranslator().get_supported_languages(as_dict=True)
        return langs_dict
    except Exception as e:
        print(red(f"  Failed to fetch supported languages: {e}"))
        return {
            "afrikaans": "af",
            "albanian": "sq",
            "amharic": "am",
            "arabic": "ar",
            "armenian": "hy",
            "azerbaijani": "az",
            "basque": "eu",
            "belarusian": "be",
            "bengali": "bn",
            "bosnian": "bs",
            "bulgarian": "bg",
            "catalan": "ca",
            "cebuano": "ceb",
            "chichewa": "ny",
            "chinese (simplified)": "zh-CN",
            "chinese (traditional)": "zh-TW",
            "corsican": "co",
            "croatian": "hr",
            "czech": "cs",
            "danish": "da",
            "dutch": "nl",
            "english": "en",
            "esperanto": "eo",
            "estonian": "et",
            "filipino": "tl",
            "finnish": "fi",
            "french": "fr",
            "frisian": "fy",
            "galician": "gl",
            "georgian": "ka",
            "german": "de",
            "greek": "el",
            "gujarati": "gu",
            "haitian creole": "ht",
            "hausa": "ha",
            "hawaiian": "haw",
            "hebrew": "iw",
            "hindi": "hi",
            "hmong": "hmn",
            "hungarian": "hu",
            "icelandic": "is",
            "igbo": "ig",
            "indonesian": "id",
            "irish": "ga",
            "italian": "it",
            "japanese": "ja",
            "javanese": "jw",
            "kannada": "kn",
            "kazakh": "kk",
            "khmer": "km",
            "kinyarwanda": "rw",
            "korean": "ko",
            "kurdish (kurmanji)": "ku",
            "kyrgyz": "ky",
            "lao": "lo",
            "latin": "la",
            "latvian": "lv",
            "lithuanian": "lt",
            "luxembourgish": "lb",
            "macedonian": "mk",
            "malagasy": "mg",
            "malay": "ms",
            "malayalam": "ml",
            "maltese": "mt",
            "maori": "mi",
            "marathi": "mr",
            "mongolian": "mn",
            "myanmar (burmese)": "my",
            "nepali": "ne",
            "norwegian": "no",
            "odia (oriya)": "or",
            "pashto": "ps",
            "persian": "fa",
            "polish": "pl",
            "portuguese": "pt",
            "punjabi": "pa",
            "romanian": "ro",
            "russian": "ru",
            "samoan": "sm",
            "scots gaelic": "gd",
            "serbian": "sr",
            "sesotho": "st",
            "shona": "sn",
            "sindhi": "sd",
            "sinhala": "si",
            "slovak": "sk",
            "slovenian": "sl",
            "somali": "so",
            "spanish": "es",
            "sundanese": "su",
            "swahili": "sw",
            "swedish": "sv",
            "tajik": "tg",
            "tamil": "ta",
            "telugu": "te",
            "thai": "th",
            "turkish": "tr",
            "turkmen": "tk",
            "ukrainian": "uk",
            "urdu": "ur",
            "uyghur": "ug",
            "vietnamese": "vi",
            "welsh": "cy",
            "xhosa": "xh",
            "yiddish": "yi",
            "yoruba": "yo",
            "zulu": "zu",
        }


# ──────────────────────── Auto-start Setup ─────────────────
def get_venv_python():
    """Get the path to the venv Python executable."""
    return VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable


def setup_autostart_windows():
    try:
        startup = os.path.join(
            os.environ.get("APPDATA", ""),
            "Microsoft",
            "Windows",
            "Start Menu",
            "Programs",
            "Startup",
        )
        os.makedirs(startup, exist_ok=True)
        python_exe = get_venv_python()
        vbs_content = (
            f'Set WshShell = CreateObject("WScript.Shell")\n'
            f'WshShell.Run """{python_exe}"" ""{MAIN_SCRIPT}""", 0, False\n'
        )
        os.makedirs(startup, exist_ok=True)
        python_exe = sys.executable
        vbs_content = (
            f'Set WshShell = CreateObject("WScript.Shell")\n'
            f'WshShell.Run """{python_exe}"" ""{MAIN_SCRIPT}""", 0, False\n'
        )
        vbs_path = os.path.join(startup, f"{APP_NAME}.vbs")
        with open(vbs_path, "w") as f:
            f.write(vbs_content)
        print(green("    ✓") + " Auto-start configured")
        return True
    except Exception as e:
        print(red(f"    ✗ Auto-start failed: {e}"))
        return False


def setup_autostart_mac():
    try:
        agents_dir = os.path.expanduser("~/Library/LaunchAgents")
        os.makedirs(agents_dir, exist_ok=True)
        python_exe = get_venv_python()
        plist_path = os.path.join(agents_dir, f"com.shiftlang.app.plist")
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.shiftlang.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_exe}</string>
        <string>{MAIN_SCRIPT}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>WorkingDirectory</key>
    <string>{PROJECT_DIR}</string>
</dict>
</plist>
"""
        with open(plist_path, "w") as f:
            f.write(plist_content)
        print(green("    ✓") + " Auto-start configured")
        return True
    except Exception as e:
        print(red(f"    ✗ Auto-start failed: {e}"))
        return False


def setup_autostart_linux():
    try:
        autostart_dir = os.path.expanduser("~/.config/autostart")
        os.makedirs(autostart_dir, exist_ok=True)
        python_exe = get_venv_python()
        desktop_path = os.path.join(autostart_dir, f"{APP_NAME}.desktop")

        # Use different startup commands for Wayland vs X11
        if IS_WAYLAND:
            # Wayland needs to wait for session to be ready
            exec_cmd = f"sh -c 'sleep 5 && {python_exe} {MAIN_SCRIPT}'"
        else:
            exec_cmd = f"{python_exe} {MAIN_SCRIPT}"

        desktop_content = f"""[Desktop Entry]
Type=Application
Name={APP_NAME}
Exec={exec_cmd}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Comment=ShiftLang translation tool
"""
        with open(desktop_path, "w") as f:
            f.write(desktop_content)
        print(green("    ✓") + " Auto-start configured")
        return True
    except Exception as e:
        print(red(f"    ✗ Auto-start failed: {e}"))
        return False


def setup_autostart():
    if OS_NAME == "Windows":
        return setup_autostart_windows()
    elif OS_NAME == "Darwin":
        return setup_autostart_mac()
    elif OS_NAME == "Linux":
        return setup_autostart_linux()
    else:
        print(yellow(f"  Auto-start not supported on {OS_NAME}"))
        return False


# ──────────────────────── Save Config ──────────────────────
def save_config(
    hotkey,
    auto_start,
    source_lang,
    target_lang,
    provider="google",
    api_key="",
    model="openrouter/free",
):
    cfg = {
        "hotkey": hotkey,
        "auto_start": auto_start,
        "source_language": source_lang,
        "target_language": target_lang,
        "translation_provider": provider,
        "openrouter_api_key": api_key,
        "openrouter_model": model,
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
    print(green("    ✓") + " Configuration saved")


def load_config():
    """Load existing config."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return None


# ──────────────────────── Start ShiftLang ─────────────────
def start_shiftlang():
    """Start ShiftLang in the background."""
    print(dim("    Starting ShiftLang..."))
    python_exe = get_venv_python()
    try:
        if OS_NAME == "Windows":
            subprocess.Popen(
                [python_exe, MAIN_SCRIPT],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        else:
            # Start in background, suppress output
            subprocess.Popen(
                [python_exe, MAIN_SCRIPT],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        print(green("    ✓") + " ShiftLang started")
        return True
    except Exception as e:
        print(red(f"    ✗ Failed to start: {e}"))
        return False


# ──────────────────────── Interactive Mode ─────────────────
def ask_choice(question, options, note=None):
    """Arrow-key choice selector. Returns the 0-based index chosen, or None if ESC pressed."""
    cursor = 0

    def draw_choice():
        clear_screen()
        print()
        print("  " + bold(question))
        print()
        if note:
            print(dim(f"    {note}"))
            print()
        for i, opt in enumerate(options):
            if i == cursor:
                print(f"  {cyan('›')} {opt}")
            else:
                print(f"    {dim(opt)}")
        print()
        print(dim("    ↑↓ navigate • enter confirm • esc exit"))
        sys.stdout.flush()

    draw_choice()

    while True:
        key = _read_key()
        if key == "UP" and cursor > 0:
            cursor -= 1
            draw_choice()
        elif key == "DOWN" and cursor < len(options) - 1:
            cursor += 1
            draw_choice()
        elif key == "ENTER":
            print()
            return cursor
        elif key == "ESC":
            print()
            return None


def ask_input(prompt, default=None):
    """Simple text input with optional default."""
    suffix = f" {dim(f'({default})')}" if default else ""
    val = input(f"    {prompt}{suffix}: ").strip()
    return val if val else default


def _read_key():
    """Read a single keypress and return a normalized string."""
    if OS_NAME == "Windows":
        import msvcrt

        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            ch2 = msvcrt.getwch()
            if ch2 == "H":
                return "UP"
            elif ch2 == "P":
                return "DOWN"
            elif ch2 == "K":
                return "LEFT"
            elif ch2 == "M":
                return "RIGHT"
            return "UNKNOWN"
        elif ch == "\r":
            return "ENTER"
        elif ch == " ":
            return "SPACE"
        elif ch == "\x08":
            return "BACKSPACE"
        elif ch == "\x1b":
            return "ESC"
        else:
            return ch
    else:
        import tty
        import termios

        if not sys.stdin.isatty():
            line = sys.stdin.readline()
            if not line:
                return "ENTER"
            first_char = line[0]
            if first_char == "\n" or first_char == "\r":
                return "ENTER"
            elif first_char == " ":
                return "SPACE"
            elif first_char == "\x7f" or first_char == "\x08":
                return "BACKSPACE"
            elif first_char == "\x1b":
                return "ESC"
            return first_char

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    ch3 = sys.stdin.read(1)
                    if ch3 == "A":
                        return "UP"
                    elif ch3 == "B":
                        return "DOWN"
                    elif ch3 == "C":
                        return "RIGHT"
                    elif ch3 == "D":
                        return "LEFT"
                return "ESC"
            elif ch == "\r" or ch == "\n":
                return "ENTER"
            elif ch == " ":
                return "SPACE"
            elif ch == "\x7f" or ch == "\x08":
                return "BACKSPACE"
            else:
                return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def ask_language(prompt, languages, default=None):
    """Interactive language selector with arrow keys and live search. Returns list of languages or None if ESC pressed."""
    VIEWPORT_SIZE = 15
    all_languages = list(languages)
    items = list(all_languages)
    cursor = 0
    selected_names = []
    scroll_top = 0
    search_query = ""

    def ensure_visible():
        nonlocal scroll_top
        if cursor < scroll_top:
            scroll_top = cursor
        elif cursor >= scroll_top + VIEWPORT_SIZE:
            scroll_top = cursor - VIEWPORT_SIZE + 1

    def draw_full():
        nonlocal scroll_top
        ensure_visible()
        total = len(items)
        clear_screen()
        print()
        print("  " + bold(prompt))
        print()
        if len(selected_names) == 0:
            print(dim("    Select 2 languages") + dim(" · 0/2"))
        elif len(selected_names) == 1:
            print(f"    {green('✓')} {selected_names[0]}  {dim('· 1/2')}")
        else:
            print(
                f"    {green('✓')} {selected_names[0]}  {dim('→')}  {green('✓')} {selected_names[1]}  {green('· 2/2')}"
            )
        print()
        if search_query:
            print(f"    Search: {bold(search_query)}█")
        else:
            print(f"    Search: {dim('type to filter...')}")
        print()
        if total == 0:
            print(red("    No languages match your search."))
        else:
            end = min(scroll_top + VIEWPORT_SIZE, total)
            for idx in range(scroll_top, end):
                lang = items[idx]
                is_selected = lang in selected_names
                is_cursor = idx == cursor
                if is_cursor and is_selected:
                    print(f"  {cyan('›')} {green('✓')} {lang}")
                elif is_cursor:
                    print(f"  {cyan('›')}   {lang}")
                elif is_selected:
                    print(f"    {green('✓')} {dim(lang)}")
                else:
                    print(f"      {dim(lang)}")
            if total > VIEWPORT_SIZE:
                above = scroll_top
                below = total - (scroll_top + VIEWPORT_SIZE)
                hints = []
                if above > 0:
                    hints.append(f"{above} more above")
                if below > 0:
                    hints.append(f"{below} more below")
                print()
                print(dim(f"    {' · '.join(hints)}"))
        print()
        print(
            dim(
                "    ↑↓ navigate • space select • enter confirm • backspace clear • esc exit"
            )
        )
        sys.stdout.flush()

    draw_full()
    while True:
        key = _read_key()
        if key == "UP" and cursor > 0:
            cursor -= 1
            draw_full()
        elif key == "DOWN" and cursor < len(items) - 1:
            cursor += 1
            draw_full()
        elif key == "SPACE":
            if len(items) > 0:
                lang = items[cursor]
                if lang in selected_names:
                    selected_names.remove(lang)
                elif len(selected_names) < 2:
                    selected_names.append(lang)
                draw_full()
        elif key == "ENTER":
            if len(selected_names) == 2:
                clear_screen()
                print()
                print(green("  ✓") + f" {selected_names[0]} ↔ {selected_names[1]}")
                print()
                return selected_names
        elif key == "ESC":
            print()
            return None
        elif key == "BACKSPACE":
            if search_query:
                search_query = search_query[:-1]
                if search_query:
                    items = [
                        l for l in all_languages if search_query.lower() in l.lower()
                    ]
                else:
                    items = list(all_languages)
                cursor = 0
                scroll_top = 0
                draw_full()
        elif isinstance(key, str) and len(key) == 1 and key.isprintable():
            new_query = search_query + key
            filtered = [l for l in all_languages if new_query.lower() in l.lower()]
            if filtered:
                search_query = new_query
                items = filtered
                cursor = 0
                scroll_top = 0
            draw_full()


def run_interactive_setup(args=None):
    """Run the interactive preferences questionnaire."""
    # Welcome screen - wait for user to press Enter
    print(dim("    Press Enter to begin setup..."))
    print()
    # Skip waiting in non-interactive mode (piped input or --auto)
    try:
        input()
    except (EOFError, OSError):
        pass  # Non-interactive, skip waiting

    clear_screen()
    print()
    print(cyan("  ›") + " " + bold("Setup"))
    print()
    print()

    # Check input group for Wayland
    if IS_WAYLAND and not check_input_group():
        print(yellow("    ⚠ Wayland requires input group membership"))
        print()
        choice = ask_choice(
            "Add your user to input group?",
            [
                "Yes (requires sudo)",
                "No, I'll do it manually",
            ],
        )
        if choice is None:
            print(dim("    Cancelled"))
            print()
            sys.exit(0)
        if choice == 0:
            add_user_to_input_group()
        print()

    print(dim("    Loading languages..."))
    languages = get_supported_languages()
    print(green("    ✓") + f" {len(languages)} languages available")
    print()

    chosen_langs = ask_language("Select 2 languages", list(languages.keys()))
    if chosen_langs is None:
        print(dim("    Cancelled"))
        print()
        sys.exit(0)
    source_lang = languages[chosen_langs[0]]
    target_lang = languages[chosen_langs[1]]

    # Ask about translation provider
    provider_choice = ask_choice(
        "Choose translation provider",
        [
            "Google Translate (Fast, free, no setup)",
            "OpenRouter AI (More accurate, requires internet)",
        ],
        note="Google Translate is recommended for most users",
    )
    if provider_choice is None:
        print(dim("    Cancelled"))
        print()
        sys.exit(0)

    if provider_choice == 0:
        provider = "google"
        api_key = ""
        model = ""
    else:
        provider = "openrouter"

        # Ask for model selection first
        print()
        model_choice = ask_choice(
            "Choose OpenRouter model",
            [
                "Free Auto-Router (automatic model selection)",
                "Gemini 2.0 Flash Exp (free, very fast, experimental)",
                "Llama 3.1 8B (free, fast, good for translation)",
                "NVIDIA Nemotron 3 Nano (free, 30B/3.5B active, 1M context)",
                "Arcee Trinity Mini (free, 26B/3B active, multi-turn)",
                "Gemini Flash 1.5 (paid, $0.075/$0.30 per M tokens, ~2.3s)",
                "GPT-4o Mini (paid, excellent translation quality)",
                "Llama 3.3 70B (paid, efficient, high quality)",
            ],
            note="Free models don't require payment, paid models need API credits",
        )
        if model_choice is None:
            print(dim("    Cancelled"))
            print()
            sys.exit(0)

        # Map choice to model ID
        model_map = {
            0: "openrouter/free",
            1: "google/gemini-2.0-flash-exp:free",
            2: "meta-llama/llama-3.1-8b-instruct:free",
            3: "nvidia/nemotron-3-nano-30b-a3b:free",
            4: "arcee-ai/trinity-mini:free",
            5: "google/gemini-flash-1.5",
            6: "openai/gpt-4o-mini",
            7: "meta-llama/llama-3.3-70b-instruct",
        }
        model = model_map[model_choice]

        # Determine if API key is required
        is_free_model = model_choice in [0, 1, 2, 3, 4]

        print()
        if is_free_model:
            print(green("    ✓") + " Free model selected - no API key required")
            print(
                dim("    (You can optionally add an API key for rate limit increases)")
            )
            print()
            api_key = ask_input("OpenRouter API key (optional)", default="").strip()
        else:
            print(yellow("    ⚠ This model requires an API key with credits"))
            print()
            print(dim("    Get a free API key at:"))
            print(cyan("    https://openrouter.ai/keys"))
            print()
            print(dim("    Note: You'll need to add credits ($5 minimum)"))
            print()

            api_key = ""
            while not api_key:
                api_key = ask_input("OpenRouter API key (required)", default="").strip()
                if not api_key:
                    print()
                    choice = ask_choice(
                        "API key is required for paid models",
                        [
                            "Enter API key now",
                            "Switch to Google Translate instead",
                            "Choose a free OpenRouter model",
                        ],
                    )
                    if choice == 1:
                        # Switch to Google
                        provider = "google"
                        api_key = ""
                        model = ""
                        print()
                        break
                    elif choice == 2:
                        # Go back to model selection with free models
                        print()
                        free_model_choice = ask_choice(
                            "Choose a free OpenRouter model",
                            [
                                "Free Auto-Router (automatic model selection)",
                                "Gemini 2.0 Flash Exp (free, very fast, experimental)",
                                "Llama 3.1 8B (free, fast, good for translation)",
                                "NVIDIA Nemotron 3 Nano (free, 30B/3.5B active, 1M context)",
                                "Arcee Trinity Mini (free, 26B/3B active, multi-turn)",
                            ],
                        )
                        if free_model_choice is None:
                            print(dim("    Cancelled"))
                            print()
                            sys.exit(0)

                        free_model_map = {
                            0: "openrouter/free",
                            1: "google/gemini-2.0-flash-exp:free",
                            2: "meta-llama/llama-3.1-8b-instruct:free",
                            3: "nvidia/nemotron-3-nano-30b-a3b:free",
                            4: "arcee-ai/trinity-mini:free",
                        }
                        model = free_model_map[free_model_choice]
                        print()
                        print(
                            green("    ✓")
                            + " Free model selected - no API key required"
                        )
                        api_key = ""
                        break
                    print()

        if provider == "openrouter" and api_key:
            print(green("    ✓") + " API key configured")
        print()

    default_hotkey = DEFAULTS.get(OS_NAME, "ctrl+shift+q")

    auto_start_choice = ask_choice(
        "Start automatically on boot?",
        [
            "Yes",
            "No, I'll start manually",
        ],
    )
    if auto_start_choice is None:
        print(dim("    Cancelled"))
        print()
        sys.exit(0)
    auto_start = auto_start_choice == 0

    if OS_NAME == "Darwin":
        default_label = f"Default (Cmd+Shift+G)"
    else:
        default_label = f"Default (Ctrl+Shift+Q)"

    hotkey_choice = ask_choice(
        "Choose keyboard shortcut",
        [
            default_label,
            "Custom shortcut",
        ],
    )
    if hotkey_choice is None:
        print(dim("    Cancelled"))
        print()
        sys.exit(0)

    if hotkey_choice == 0:
        hotkey = default_hotkey
    else:
        print()
        print(dim("    Examples: ctrl+shift+t, alt+g, cmd+shift+k"))
        print()
        hotkey = ask_input("Enter hotkey", default=default_hotkey)
        if not hotkey:
            hotkey = default_hotkey
    print()

    # Apply settings
    print()
    print(dim("  Saving configuration..."))
    print()
    save_config(
        hotkey,
        auto_start,
        source_lang,
        target_lang,
        provider,
        api_key,
        model if provider == "openrouter" else "",
    )
    if auto_start:
        setup_autostart()
    print()

    # Start now
    start_shiftlang()
    print()

    # Done
    clear_screen()
    print()
    print(green("  ✓") + " " + bold("Setup complete"))
    print()
    print()
    print(f"    Languages    {dim(source_lang)} → {dim(target_lang)}")
    if provider == "google":
        print(f"    Provider     {dim('Google Translate')}")
    else:
        print(f"    Provider     {dim('OpenRouter AI')}")
        print(f"    Model        {dim(model if model else 'openrouter/free')}")
    print(f"    Hotkey       {dim(hotkey)}")
    print(f"    Auto-start   {dim('enabled' if auto_start else 'disabled')}")
    print()
    if IS_WAYLAND and not check_input_group():
        print(yellow("    ⚠ Log out and back in for input group changes"))
        print()
    if auto_start:
        print(dim("    ShiftLang will start automatically on boot"))
        print()
    print()
    print(dim("    Ready to translate ⚡"))
    print()
    print()


# ──────────────────────── Silent/Auto Mode ─────────────────
def run_auto_setup(args=None):
    """Run automatic setup with defaults or existing config."""
    existing = load_config()

    if existing:
        print(dim("    Using saved configuration"))
        hotkey = existing.get("hotkey", DEFAULTS.get(OS_NAME, "ctrl+shift+q"))
        auto_start = existing.get("auto_start", True)
        source_lang = existing.get("source_language", "hebrew")
        target_lang = existing.get("target_language", "english")
        provider = existing.get("translation_provider", "google")
        api_key = existing.get("openrouter_api_key", "")
        model = existing.get("openrouter_model", "openrouter/free")
    else:
        print(dim("    Using default configuration"))
        hotkey = DEFAULTS.get(OS_NAME, "ctrl+shift+q")
        auto_start = True
        source_lang = "hebrew"
        target_lang = "english"
        provider = "google"
        api_key = ""
        model = "openrouter/free"

    if args and getattr(args, "esc", False):
        hotkey = "esc"

    print()
    save_config(hotkey, auto_start, source_lang, target_lang, provider, api_key, model)

    if auto_start:
        setup_autostart()

    print()
    start_shiftlang()
    print()

    print(green("  ✓") + " " + bold("Ready"))
    print()
    print(f"    Languages    {dim(source_lang)} → {dim(target_lang)}")
    if provider == "google":
        print(f"    Provider     {dim('Google Translate')}")
    else:
        print(f"    Provider     {dim('OpenRouter AI')}")
        print(f"    Model        {dim(model if model else 'openrouter/free')}")
    print(f"    Hotkey       {dim(hotkey)}")
    print()
    print()


# ──────────────────────── Main Installer Flow ──────────────
def main():
    parser = argparse.ArgumentParser(description="ShiftLang Installer")
    parser.add_argument(
        "--auto", "-a", action="store_true", help="Automatic/silent mode"
    )
    parser.add_argument(
        "--update", "-u", action="store_true", help="Update existing install"
    )
    parser.add_argument(
        "--reconfigure", "-r", action="store_true", help="Reconfigure settings"
    )
    args = parser.parse_args()

    silent_mode = args.auto or args.update

    # Always show banner
    clear_screen()
    banner()

    if args.reconfigure:
        if not silent_mode:
            print(dim("  Reconfiguring ShiftLang settings..."))
            print()
        run_interactive_setup()
        return

    # Check if this is an update
    is_update = args.update or os.path.exists(CONFIG_FILE)

    if is_update and silent_mode:
        print(dim("    Updating..."))
    elif not silent_mode:
        print()
        print(dim("  Checking prerequisites"))
        print()

    # Prerequisites
    if not silent_mode:
        ok = check_python() and check_pip()
        check_git()
        print()
        if not ok:
            print(red("    Prerequisites check failed"))
            print()
            sys.exit(1)

    # Dependencies
    if not install_dependencies():
        print(red("    Installation failed"))
        print()
        sys.exit(1)
    print()

    # Setup mode
    if silent_mode:
        run_auto_setup(args)
    else:
        run_interactive_setup(args)


if __name__ == "__main__":
    main()
