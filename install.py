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


# ──────────────────────── TTY Input Helper ─────────────────
def get_tty():
    """Get a file descriptor for the terminal, even when piped."""
    if OS_NAME == "Windows":
        return None
    try:
        return open("/dev/tty", "r")
    except (OSError, IOError):
        return None


def tty_input(prompt=""):
    """Read input from /dev/tty if available, otherwise stdin."""
    tty = get_tty()
    if tty:
        try:
            if prompt:
                # Write prompt to stderr so it still appears
                sys.stderr.write(prompt)
                sys.stderr.flush()
            return tty.readline().rstrip("\n")
        finally:
            tty.close()
    else:
        return input(prompt)


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
    # Try to use venv Python if available to import deep_translator
    if os.path.exists(VENV_PYTHON):
        try:
            result = subprocess.run(
                [VENV_PYTHON, "-c", 
                 "from deep_translator import GoogleTranslator; "
                 "import json; "
                 "langs = GoogleTranslator().get_supported_languages(as_dict=True); "
                 "print(json.dumps(langs))"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                import json
                return json.loads(result.stdout.strip())
        except Exception:
            pass  # Fall through to fallback list
    
    # Fallback: return hardcoded list
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
        elif key == "LEFT":
            if allow_back:
                print()
                return None  # Signal to go back
        elif key == "ESC":
            print()
            return None


def ask_input(prompt, default=None):
    """Simple text input with optional default - reads from /dev/tty when piped."""
    suffix = f" {dim(f'({default})')}" if default else ""
    full_prompt = f"    {prompt}{suffix}: "
    val = tty_input(full_prompt).strip()
    return val if val else default


def _read_key():
    """Read a single keypress and return a normalized string - reads from /dev/tty when piped."""
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

        # Always use /dev/tty for key input on Unix
        try:
            fd = os.open("/dev/tty", os.O_RDONLY)
            use_dev_tty = True
        except OSError:
            # Fallback to stdin if /dev/tty not available
            fd = sys.stdin.fileno()
            use_dev_tty = False
            if not sys.stdin.isatty():
                # Last resort - try to read a line
                line = tty_input("")
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

        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = os.read(fd, 1).decode()
            if ch == "\x1b":
                ch2 = os.read(fd, 1).decode()
                if ch2 == "[":
                    ch3 = os.read(fd, 1).decode()
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
            if use_dev_tty:
                os.close(fd)


def ask_language(prompt, languages, default=None, allow_back=True):
    """Interactive language selector with arrow keys and live search. Returns (selected_list, went_back) tuple.
    
    selected_list is None if ESC pressed or went back.
    Use LEFT arrow to go back to previous step.
    """
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
        if allow_back:
            print(
                dim(
                    "    ↑↓ navigate • space select • ← back • enter confirm • backspace clear"
                )
            )
        else:
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
                return selected_names, False
        elif key == "LEFT":
            if allow_back:
                print()
                return None, True
        elif key == "ESC":
            print()
            return None, False
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


# ──────────────────────── Back Navigation Support ──────────
def ask_choice_with_back(question, options, note=None, allow_back=True, show_arrows=True):
    """Arrow-key choice selector with left/right navigation. Returns (index, went_back, went_forward)."""
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
        if show_arrows:
            if allow_back:
                print(dim("    ↑↓ select • ← back • →/enter confirm"))
            else:
                print(dim("    ↑↓ select • →/enter confirm • esc exit"))
        else:
            if allow_back:
                print(dim("    ↑↓ navigate • enter confirm • esc exit/back"))
            else:
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
        elif key == "LEFT":
            if allow_back:
                print()
                return None, True, False
        elif key == "RIGHT" or key == "ENTER":
            print()
            return cursor, False, key == "RIGHT"
        elif key == "ESC":
            print()
            return None, False, False


def ask_input_with_back(prompt, default=None, allow_back=True):
    """Text input with back option. Returns (value, went_back)."""
    suffix = f" {dim(f'({default})')}" if default else ""
    full_prompt = f"    {prompt}{suffix}: "
    val = tty_input(full_prompt).strip()
    return val if val else default, False


def run_interactive_setup(args=None):
    """Run the interactive preferences questionnaire with back navigation."""
    # State definitions
    STEP_WAYLAND = "wayland"
    STEP_LANGUAGE = "language"
    STEP_PROVIDER = "provider"
    STEP_OPENROUTER_MODEL = "openrouter_model"
    STEP_OPENROUTER_API_KEY = "openrouter_api_key"
    STEP_AUTOSTART = "autostart"
    STEP_HOTKEY = "hotkey"
    STEP_SUMMARY = "summary"
    
    # Ordered steps for navigation
    ALL_STEPS = [STEP_WAYLAND, STEP_LANGUAGE, STEP_PROVIDER, STEP_AUTOSTART, STEP_HOTKEY]
    
    # State
    step_index = 0
    languages = None
    chosen_langs = None
    source_lang = None
    target_lang = None
    provider = None
    model = None
    api_key = None
    auto_start = None
    hotkey = None
    default_hotkey = DEFAULTS.get(OS_NAME, "ctrl+shift+q")
    
    # Model maps
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
    free_model_map = {
        0: "openrouter/free",
        1: "google/gemini-2.0-flash-exp:free",
        2: "meta-llama/llama-3.1-8b-instruct:free",
        3: "nvidia/nemotron-3-nano-30b-a3b:free",
        4: "arcee-ai/trinity-mini:free",
    }
    
    # Welcome screen - wait for user to press Enter
    print()
    print(cyan("  ›") + " " + bold("Setup"))
    print()
    print()
    print(dim("    Press Enter to begin setup..."))
    print()
    # Skip waiting in non-interactive mode (piped input or --auto)
    try:
        tty_input("")
    except (EOFError, OSError):
        pass  # Non-interactive, skip waiting
    
    # Load languages once
    print(dim("    Loading languages..."))
    languages = get_supported_languages()
    print(green("    ✓") + f" {len(languages)} languages available")
    time.sleep(0.5)

    while step_index < len(ALL_STEPS):
        current_step = ALL_STEPS[step_index]
        went_back = False
        
        # ──────────────────────── WAYLAND CHECK ────────────────────────
        if current_step == STEP_WAYLAND:
            if IS_WAYLAND and not check_input_group():
                clear_screen()
                print()
                print(yellow("    ⚠ Wayland requires input group membership"))
                print()
                choice, went_back, _ = ask_choice_with_back(
                    "Add your user to input group?",
                    [
                        "Yes (requires sudo)",
                        "No, I'll do it manually",
                    ],
                    allow_back=False,  # First step, can't go back
                )
                if choice is None:
                    print(dim("    Cancelled"))
                    print()
                    sys.exit(0)
                if choice == 0:
                    add_user_to_input_group()
                print()
            # Always advance from wayland step
            step_index += 1
            continue
        
        # ──────────────────────── LANGUAGE SELECTION ────────────────────────
        elif current_step == STEP_LANGUAGE:
            clear_screen()
            chosen_langs, went_back = ask_language("Select 2 languages", list(languages.keys()))
            if chosen_langs is None and not went_back:
                print(dim("    Cancelled"))
                print()
                sys.exit(0)
            if chosen_langs:
                source_lang = languages[chosen_langs[0]]
                target_lang = languages[chosen_langs[1]]
            
            if went_back:
                step_index = max(0, step_index - 1)
            else:
                step_index += 1
            continue
        
        # ──────────────────────── TRANSLATION PROVIDER ────────────────────────
        elif current_step == STEP_PROVIDER:
            clear_screen()
            provider_choice, went_back, _ = ask_choice_with_back(
                "Choose translation provider",
                [
                    "Google Translate (Fast, free, no setup)",
                    "OpenRouter AI (More accurate, requires internet)",
                ],
                note="Google Translate is recommended for most users",
                allow_back=step_index > 0,
            )
            if provider_choice is None and not went_back:
                print(dim("    Cancelled"))
                print()
                sys.exit(0)
            
            if went_back:
                step_index = max(0, step_index - 1)
                continue
            
            if provider_choice == 0:
                provider = "google"
                api_key = ""
                model = ""
            else:
                provider = "openrouter"
                
                # OpenRouter model selection loop (allows going back)
                model_step_active = True
                while model_step_active:
                    clear_screen()
                    model_choice, went_back, _ = ask_choice_with_back(
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
                        allow_back=True,
                    )
                    if went_back:
                        # Go back to provider selection
                        model_step_active = False
                        step_index = max(0, step_index - 1)
                        break
                    if model_choice is None:
                        print(dim("    Cancelled"))
                        print()
                        sys.exit(0)
                    
                    model = model_map[model_choice]
                    is_free_model = model_choice in [0, 1, 2, 3, 4]
                    
                    # API Key step
                    api_step_active = True
                    while api_step_active:
                        clear_screen()
                        if is_free_model:
                            print(green("    ✓") + " Free model selected - no API key required")
                            print(dim("    (You can optionally add an API key for rate limit increases)"))
                            print()
                            api_key, went_back = ask_input_with_back("OpenRouter API key (optional)", default="")
                            api_key = (api_key or "").strip()
                            if went_back:
                                # Go back to model selection
                                api_step_active = False
                                break
                        else:
                            print(yellow("    ⚠ This model requires an API key with credits"))
                            print()
                            print(dim("    Get a free API key at:"))
                            print(cyan("    https://openrouter.ai/keys"))
                            print()
                            print(dim("    Note: You'll need to add credits ($5 minimum)"))
                            print()
                            
                            api_key, went_back = ask_input_with_back("OpenRouter API key (required)", default="")
                            api_key = (api_key or "").strip()
                            if went_back:
                                # Go back to model selection
                                api_step_active = False
                                break
                            
                            if not api_key:
                                # Show options when no API key entered
                                choice, went_back, _ = ask_choice_with_back(
                                    "API key is required for paid models",
                                    [
                                        "Enter API key now",
                                        "Switch to Google Translate instead",
                                        "Choose a free OpenRouter model",
                                    ],
                                    allow_back=True,
                                )
                                if went_back:
                                    # Go back to model selection
                                    api_step_active = False
                                    break
                                if choice == 1:
                                    # Switch to Google
                                    provider = "google"
                                    api_key = ""
                                    model = ""
                                    api_step_active = False
                                    model_step_active = False
                                    break
                                elif choice == 2:
                                    # Choose free model
                                    clear_screen()
                                    free_model_choice, went_back, _ = ask_choice_with_back(
                                        "Choose a free OpenRouter model",
                                        [
                                            "Free Auto-Router (automatic model selection)",
                                            "Gemini 2.0 Flash Exp (free, very fast, experimental)",
                                            "Llama 3.1 8B (free, fast, good for translation)",
                                            "NVIDIA Nemotron 3 Nano (free, 30B/3.5B active, 1M context)",
                                            "Arcee Trinity Mini (free, 26B/3B active, multi-turn)",
                                        ],
                                        allow_back=True,
                                    )
                                    if went_back:
                                        # Stay in API key step, but let user try again
                                        continue
                                    if free_model_choice is None:
                                        print(dim("    Cancelled"))
                                        print()
                                        sys.exit(0)
                                    model = free_model_map[free_model_choice]
                                    print()
                                    print(green("    ✓") + " Free model selected - no API key required")
                                    api_key = ""
                                    api_step_active = False
                                    model_step_active = False
                                    break
                                # choice == 0 means continue to enter API key
                                continue
                        
                        # API key entered successfully
                        api_step_active = False
                        model_step_active = False
                    
                    if went_back and api_step_active == False and model_step_active == False:
                        # We came from API step and went back to model selection
                        continue
                
                if went_back and step_index != ALL_STEPS.index(STEP_PROVIDER):
                    # We went back further than model selection
                    continue
            
            if not went_back:
                step_index += 1
            continue
        
        # ──────────────────────── AUTOSTART ────────────────────────
        elif current_step == STEP_AUTOSTART:
            clear_screen()
            auto_start_choice, went_back, _ = ask_choice_with_back(
                "Start automatically on boot?",
                [
                    "Yes",
                    "No, I'll start manually",
                ],
                allow_back=step_index > 0,
            )
            if auto_start_choice is None and not went_back:
                print(dim("    Cancelled"))
                print()
                sys.exit(0)
            
            if went_back:
                step_index = max(0, step_index - 1)
                # If coming back from provider was openrouter, we need to skip the nested steps
                continue
            
            auto_start = auto_start_choice == 0
            step_index += 1
            continue
        
        # ──────────────────────── HOTKEY ────────────────────────
        elif current_step == STEP_HOTKEY:
            clear_screen()
            if OS_NAME == "Darwin":
                default_label = f"Default (Cmd+Shift+G)"
            else:
                default_label = f"Default (Ctrl+Shift+Q)"

            hotkey_choice, went_back, _ = ask_choice_with_back(
                "Choose keyboard shortcut",
                [
                    default_label,
                    "Custom shortcut",
                ],
                allow_back=step_index > 0,
            )
            if hotkey_choice is None and not went_back:
                print(dim("    Cancelled"))
                print()
                sys.exit(0)
            
            if went_back:
                step_index = max(0, step_index - 1)
                continue
            
            if hotkey_choice == 0:
                hotkey = default_hotkey
                step_index += 1
            else:
                # Custom hotkey input
                print()
                print(dim("    Examples: ctrl+shift+t, alt+g, cmd+shift+k"))
                print()
                custom_hotkey, went_back = ask_input_with_back("Enter hotkey", default=default_hotkey)
                if went_back:
                    # Stay on hotkey step to choose again
                    continue
                hotkey = custom_hotkey if custom_hotkey else default_hotkey
                step_index += 1
            continue

    # Apply settings
    clear_screen()
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
