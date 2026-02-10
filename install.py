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
    PROJECT_DIR, "shiftlang_wayland.py" if IS_WAYLAND else "main.py"
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
    print(cyan("╔══════════════════════════════════════════════╗"))
    print(
        cyan("║") + bold("       ⚡  ShiftLang Installer  ⚡            ") + cyan("║")
    )
    print(cyan("║") + "  Instant translation between any languages   " + cyan("║"))
    if IS_WAYLAND:
        print(cyan("║") + "  [Wayland mode detected]                     " + cyan("║"))
    print(cyan("╚══════════════════════════════════════════════╝"))
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
    print(yellow(f"  Adding {user} to 'input' group..."))
    try:
        result = subprocess.run(
            ["sudo", "usermod", "-a", "-G", "input", user],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(green("  ✓ User added to input group"))
            print(
                yellow(
                    "  ⚠ You'll need to log out and back in for changes to take effect"
                )
            )
            return True
        else:
            print(red(f"  ✗ Failed: {result.stderr}"))
            return False
    except Exception as e:
        print(red(f"  ✗ Error: {e}"))
        return False


# ──────────────────────── Prerequisite Checks ──────────────
def check_python():
    v = sys.version_info
    print(f"  Python version: {v.major}.{v.minor}.{v.micro} ... ", end="")
    if v >= (3, 8):
        print(green("OK ✓"))
        return True
    else:
        print(red("FAIL ✗"))
        print(red(f"  ShiftLang requires Python 3.8+. You have {v.major}.{v.minor}."))
        return False


def check_pip():
    print("  pip available: ", end="")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(green("OK ✓"))
        return True
    except Exception:
        print(red("FAIL ✗"))
        print(red("  pip is not installed. Please install pip first."))
        return False


def check_git():
    print("  git available: ", end="")
    if shutil.which("git"):
        print(green("OK ✓"))
        return True
    else:
        print(yellow("Not found (optional)"))
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
    print(dim(f"  Creating virtual environment at {VENV_DIR}..."))

    # Try uv first (faster)
    if has_uv():
        result = subprocess.run(
            ["uv", "venv", VENV_DIR], cwd=PROJECT_DIR, capture_output=True, text=True
        )
        if result.returncode == 0:
            print(green("  ✓ Virtual environment created with uv"))
            return True
        else:
            print(yellow(f"  uv venv failed: {result.stderr}"))

    # Fall back to standard venv
    try:
        result = subprocess.run(
            [sys.executable, "-m", "venv", VENV_DIR],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(green("  ✓ Virtual environment created"))
            return True
        else:
            print(red(f"  venv creation failed: {result.stderr}"))
            return False
    except Exception as e:
        print(red(f"  Failed to create venv: {e}"))
        return False


# ──────────────────────── Install dependencies ─────────────
def install_dependencies():
    req = os.path.join(PROJECT_DIR, "requirements.txt")
    if not os.path.exists(req):
        print(red("  requirements.txt not found!"))
        return False

    # Create venv if it doesn't exist
    if not os.path.exists(VENV_PYTHON):
        print(dim("  Virtual environment not found, creating one..."))
        if not create_virtualenv():
            return False
        print()

    # Install into venv
    print(dim(f"  Installing dependencies into virtual environment..."))
    print()

    # Try uv pip (fastest)
    if has_uv():
        result = subprocess.run(
            ["uv", "pip", "install", "-r", req, "--python", VENV_PYTHON],
            cwd=PROJECT_DIR,
        )
        if result.returncode == 0:
            print(green("  Dependencies installed successfully with uv ✓"))
            return True
        else:
            print(yellow("  uv pip install failed, trying venv pip..."))

    # Fall back to venv pip
    result = subprocess.run(
        [VENV_PYTHON, "-m", "pip", "install", "-r", req],
        cwd=PROJECT_DIR,
    )
    print()
    if result.returncode == 0:
        print(green("  Dependencies installed successfully ✓"))
        return True
    else:
        print(red("  Failed to install dependencies."))
        return False


# ──────────────────────── Fetch Supported Languages ────────
def get_supported_languages():
    """Fetch the list of supported languages from GoogleTranslator."""
    try:
        from deep_translator import GoogleTranslator

        langs = GoogleTranslator().get_supported_languages()
        return sorted(langs)
    except Exception as e:
        print(red(f"  Failed to fetch supported languages: {e}"))
        # Fallback minimal list
        return sorted(
            [
                "english",
                "hebrew",
                "spanish",
                "french",
                "german",
                "italian",
                "portuguese",
                "russian",
                "chinese (simplified)",
                "chinese (traditional)",
                "japanese",
                "korean",
                "arabic",
                "turkish",
                "dutch",
                "polish",
                "swedish",
                "danish",
                "norwegian",
                "finnish",
                "greek",
                "czech",
                "romanian",
                "hungarian",
                "thai",
                "vietnamese",
                "indonesian",
                "malay",
                "filipino",
                "hindi",
                "bengali",
                "urdu",
                "persian",
                "ukrainian",
                "bulgarian",
                "croatian",
                "serbian",
                "slovak",
                "slovenian",
                "estonian",
                "latvian",
                "lithuanian",
            ]
        )


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
        print(green(f"  Auto-start configured ✓"))
        print(dim(f"  Created: {vbs_path}"))
        return True
    except Exception as e:
        print(red(f"  Failed to configure auto-start: {e}"))
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
        print(green(f"  Auto-start configured ✓"))
        print(dim(f"  Created: {plist_path}"))
        return True
    except Exception as e:
        print(red(f"  Failed to configure auto-start: {e}"))
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
        print(green(f"  Auto-start configured ✓"))
        print(dim(f"  Created: {desktop_path}"))
        return True
    except Exception as e:
        print(red(f"  Failed to configure auto-start: {e}"))
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
def save_config(hotkey, auto_start, source_lang, target_lang):
    cfg = {
        "hotkey": hotkey,
        "auto_start": auto_start,
        "source_language": source_lang,
        "target_language": target_lang,
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
    print(green(f"  Preferences saved to config.json ✓"))


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
    print(dim("  Starting ShiftLang..."))
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
        print(green("  ✓ ShiftLang started in background"))
        return True
    except Exception as e:
        print(red(f"  ✗ Failed to start: {e}"))
        return False


# ──────────────────────── Interactive Mode ─────────────────
def ask_choice(question, options, note=None):
    """Arrow-key choice selector. Returns the 0-based index chosen."""
    cursor = 0

    def draw_choice():
        clear_screen()
        print(bold(question))
        if note:
            print(dim(f"  ℹ  {note}"))
        print(dim("  ↑/↓ to move  |  Enter to confirm"))
        print()
        for i, opt in enumerate(options):
            if i == cursor:
                print(f"  {cyan('►')} {bold(opt)}")
            else:
                print(f"    {dim(opt)}")
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


def ask_input(prompt, default=None):
    """Simple text input with optional default."""
    suffix = f" [{default}]" if default else ""
    val = input(f"  {prompt}{suffix}: ").strip()
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
    """Interactive language selector with arrow keys and live search."""
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
        print(bold(prompt))
        print()
        if len(selected_names) == 0:
            print(dim("  Select 2 languages (0/2 selected)"))
        elif len(selected_names) == 1:
            print(
                f"  {green('●')} {bold(selected_names[0])}  {dim('(1/2 — select one more)')}"
            )
        else:
            print(
                f"  {green('●')} {bold(selected_names[0])}  ↔  {green('●')} {bold(selected_names[1])}  {green('(2/2 ✓ press Enter to confirm)')}"
            )
        print()
        if search_query:
            print(f"  🔍 Search: {bold(search_query)}█")
        else:
            print(f"  🔍 Search: {dim('type to filter...')}")
        print()
        print(
            dim(
                "  ↑/↓ move  |  Space toggle  |  Enter confirm  |  Backspace clear search"
            )
        )
        print()
        if total == 0:
            print(red("  No languages match your search."))
        else:
            end = min(scroll_top + VIEWPORT_SIZE, total)
            for idx in range(scroll_top, end):
                lang = items[idx]
                num = f"{idx + 1:>4}"
                is_selected = lang in selected_names
                is_cursor = idx == cursor
                if is_cursor and is_selected:
                    print(
                        f"  {cyan('►')} {green('●')} {cyan(num)}  {bold(green(lang))}"
                    )
                elif is_cursor:
                    print(f"  {cyan('►')}   {cyan(num)}  {bold(lang)}")
                elif is_selected:
                    print(f"    {green('●')} {num}  {green(lang)}")
                else:
                    print(f"      {dim(num)}  {lang}")
            if total > VIEWPORT_SIZE:
                above = scroll_top
                below = total - (scroll_top + VIEWPORT_SIZE)
                hints = []
                if above > 0:
                    hints.append(f"↑ {above} more above")
                if below > 0:
                    hints.append(f"↓ {below} more below")
                print(dim(f"\n  {' | '.join(hints)}"))
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
                print(
                    green(f"  → Languages: {selected_names[0]} ↔ {selected_names[1]}")
                )
                print()
                return selected_names
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


def run_interactive_setup():
    """Run the interactive preferences questionnaire."""
    print(cyan("══════════════════════════════════════════════"))
    print(cyan("║") + bold("       📋  Preferences Questionnaire         ") + cyan("║"))
    print(cyan("══════════════════════════════════════════════"))
    print()

    # Check input group for Wayland
    if IS_WAYLAND and not check_input_group():
        print(yellow("  ⚠ Wayland requires your user to be in the 'input' group"))
        choice = ask_choice(
            "Add your user to the 'input' group?",
            [
                "Yes — add me to input group (requires sudo)",
                "No — I'll do it manually later",
            ],
        )
        if choice == 0:
            add_user_to_input_group()
        print()

    print(dim("  Fetching supported languages..."))
    languages = get_supported_languages()
    print(green(f"  {len(languages)} languages available ✓"))
    print()

    chosen_langs = ask_language("1) Select your 2 languages:", languages)
    source_lang = chosen_langs[0]
    target_lang = chosen_langs[1]

    default_hotkey = DEFAULTS.get(OS_NAME, "ctrl+shift+q")
    run_cmd = "python main.py" if OS_NAME == "Windows" else "python3 main.py"

    auto_start_choice = ask_choice(
        "2) Do you want ShiftLang to run automatically when the computer starts?",
        [
            "Yes — start automatically on boot",
            f"No  — I prefer to run manually using:  {cyan(run_cmd)}",
        ],
    )
    auto_start = auto_start_choice == 0

    if OS_NAME == "Darwin":
        default_label = f"Default: {cyan('Cmd+Shift+G')} (macOS)"
    else:
        default_label = f"Default: {cyan('Ctrl+Shift+Q')} ({OS_NAME})"

    hotkey_choice = ask_choice(
        "3) What keyboard shortcut would you like to trigger translation?",
        [
            default_label,
            "Custom — choose your own combination",
        ],
    )

    if hotkey_choice == 0:
        hotkey = default_hotkey
    else:
        print(yellow("  ⚠ Make sure your chosen combination does not conflict with"))
        print(yellow("     other applications or system shortcuts on your OS."))
        print()
        print(dim("  Format examples: ctrl+shift+t, alt+g, cmd+shift+k"))
        hotkey = ask_input(
            "Enter your preferred hotkey combination", default=default_hotkey
        )
        if not hotkey:
            hotkey = default_hotkey
    print()

    # Apply settings
    print(bold("─── Applying settings ───"))
    print()
    save_config(hotkey, auto_start, source_lang, target_lang)
    if auto_start:
        setup_autostart()
    print()

    # Start now
    print(bold("─── Starting ShiftLang ───"))
    print()
    start_shiftlang()
    print()

    # Done
    print(cyan("══════════════════════════════════════════════"))
    print(green(bold("  ✅  ShiftLang is ready!")))
    print(cyan("══════════════════════════════════════════════"))
    print()
    print(f"  Languages:   {bold(source_lang)} ↔ {bold(target_lang)}")
    print(f"  Hotkey:      {bold(hotkey)}")
    print(f"  Auto-start:  {bold('Enabled' if auto_start else 'Disabled')}")
    print()
    if IS_WAYLAND and not check_input_group():
        print(yellow("  ⚠ Remember to log out and back in for input group changes!"))
        print()
    if auto_start:
        print(f"  ShiftLang will also start automatically on next boot.")
        print()
    print(dim("  Happy translating! ⚡"))
    print()


# ──────────────────────── Silent/Auto Mode ─────────────────
def run_auto_setup():
    """Run automatic setup with defaults or existing config."""
    existing = load_config()

    if existing:
        print(dim("  Existing config found, using saved preferences..."))
        hotkey = existing.get("hotkey", DEFAULTS.get(OS_NAME, "ctrl+shift+q"))
        auto_start = existing.get("auto_start", True)
        source_lang = existing.get("source_language", "hebrew")
        target_lang = existing.get("target_language", "english")
    else:
        print(dim("  No existing config, using defaults..."))
        hotkey = DEFAULTS.get(OS_NAME, "ctrl+shift+q")
        auto_start = True
        source_lang = "hebrew"
        target_lang = "english"

    print()
    save_config(hotkey, auto_start, source_lang, target_lang)

    if auto_start:
        setup_autostart()

    print()
    start_shiftlang()
    print()

    print(green(bold("✅ ShiftLang is running!")))
    print(f"  Languages: {source_lang} ↔ {target_lang}")
    print(f"  Hotkey: {hotkey}")
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

    if not silent_mode:
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
        print(dim("  Updating ShiftLang..."))
    elif not silent_mode:
        print(bold("─── Installing ShiftLang ───"))
        print()

    # Prerequisites
    if not silent_mode:
        ok = check_python() and check_pip()
        check_git()
        print()
        if not ok:
            print(
                red(
                    "Prerequisites check failed. Please fix the issues above and re-run."
                )
            )
            sys.exit(1)
        print(green("  All prerequisites met!"))
        print()

    # Dependencies
    if not install_dependencies():
        print(red("Installation failed. Please check the errors above."))
        sys.exit(1)
    print()

    if not silent_mode:
        print(green(bold("  Installation complete ✓")))
        print()

    # Setup mode
    if silent_mode:
        run_auto_setup()
    else:
        run_interactive_setup()


if __name__ == "__main__":
    main()
