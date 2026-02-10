#!/usr/bin/env python3
"""
ShiftLang Installer — Interactive one-step setup
Run:  python install.py   (or python3 install.py)
"""

import os
import sys
import json
import platform
import subprocess
import shutil

# ──────────────────────── Constants ────────────────────────
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_NAME = "ShiftLang"
MAIN_SCRIPT = os.path.join(PROJECT_DIR, "main.py")

DEFAULTS = {
    "Windows": "ctrl+shift+q",
    "Darwin": "cmd+shift+g",      # macOS
    "Linux": "alt+shift+g",
}

OS_NAME = platform.system()  # 'Windows' | 'Darwin' | 'Linux'


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


def green(t):  return color(t, "92")
def cyan(t):   return color(t, "96")
def yellow(t): return color(t, "93")
def red(t):    return color(t, "91")
def bold(t):   return color(t, "1")
def dim(t):    return color(t, "2")


def banner():
    print()
    print(cyan("╔══════════════════════════════════════════════╗"))
    print(cyan("║") + bold("       ⚡  ShiftLang Installer  ⚡            ") + cyan("║"))
    print(cyan("║") + "  Instant translation between any languages   " + cyan("║"))
    print(cyan("╚══════════════════════════════════════════════╝"))
    print()


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


# ──────────────── Raw Key Input (cross-platform) ───────────
def _read_key():
    """
    Read a single keypress and return a normalized string:
    'UP', 'DOWN', 'SPACE', 'ENTER', 'BACKSPACE',
    or the character itself for printable keys.
    """
    if OS_NAME == "Windows":
        import msvcrt
        ch = msvcrt.getwch()
        if ch in ('\x00', '\xe0'):  # special key prefix
            ch2 = msvcrt.getwch()
            if ch2 == 'H':
                return 'UP'
            elif ch2 == 'P':
                return 'DOWN'
            elif ch2 == 'K':
                return 'LEFT'
            elif ch2 == 'M':
                return 'RIGHT'
            return 'UNKNOWN'
        elif ch == '\r':
            return 'ENTER'
        elif ch == ' ':
            return 'SPACE'
        elif ch == '\x08':
            return 'BACKSPACE'
        elif ch == '\x1b':
            return 'ESC'
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
            if ch == '\x1b':
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    if ch3 == 'A':
                        return 'UP'
                    elif ch3 == 'B':
                        return 'DOWN'
                    elif ch3 == 'C':
                        return 'RIGHT'
                    elif ch3 == 'D':
                        return 'LEFT'
                return 'ESC'
            elif ch == '\r' or ch == '\n':
                return 'ENTER'
            elif ch == ' ':
                return 'SPACE'
            elif ch == '\x7f' or ch == '\x08':
                return 'BACKSPACE'
            else:
                return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ──────────────── Interactive Language Selector ────────────
def ask_language(prompt, languages, default=None):
    """
    Interactive language selector with arrow keys and live search.
    ↑/↓ to navigate, Space to select, Enter to confirm.
    Just type to search — the search box is always active.
    """
    VIEWPORT_SIZE = 15  # visible rows at a time

    all_languages = list(languages)
    items = list(all_languages)
    cursor = 0        # highlighted row
    selected = set()  # indices of selected items (in the `items` list — we track by name)
    selected_names = []  # ordered list of selected language names (max 2)
    scroll_top = 0    # first visible index
    search_query = ""

    def ensure_visible():
        """Scroll viewport so cursor is visible."""
        nonlocal scroll_top
        if cursor < scroll_top:
            scroll_top = cursor
        elif cursor >= scroll_top + VIEWPORT_SIZE:
            scroll_top = cursor - VIEWPORT_SIZE + 1

    def draw_full():
        """Clear screen and redraw everything."""
        nonlocal scroll_top
        ensure_visible()
        total = len(items)

        clear_screen()

        # Title
        print(bold(prompt))
        print()

        # Selection status
        if len(selected_names) == 0:
            print(dim("  Select 2 languages (0/2 selected)"))
        elif len(selected_names) == 1:
            print(f"  {green('●')} {bold(selected_names[0])}  {dim('(1/2 — select one more)')}")
        else:
            print(f"  {green('●')} {bold(selected_names[0])}  ↔  {green('●')} {bold(selected_names[1])}  {green('(2/2 ✓ press Enter to confirm)')}")
        print()

        # Search box (always visible)
        if search_query:
            print(f"  🔍 Search: {bold(search_query)}█")
        else:
            print(f"  🔍 Search: {dim('type to filter...')}")
        print()

        # Controls hint
        print(dim("  ↑/↓ move  |  Space toggle  |  Enter confirm  |  Backspace clear search"))
        print()

        # Language rows
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
                    print(f"  {cyan('►')} {green('●')} {cyan(num)}  {bold(green(lang))}")
                elif is_cursor:
                    print(f"  {cyan('►')}   {cyan(num)}  {bold(lang)}")
                elif is_selected:
                    print(f"    {green('●')} {num}  {green(lang)}")
                else:
                    print(f"      {dim(num)}  {lang}")

            # Scroll hint at bottom
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

    # Initial draw
    draw_full()

    while True:
        key = _read_key()

        if key == 'UP' and cursor > 0:
            cursor -= 1
            draw_full()
        elif key == 'DOWN' and cursor < len(items) - 1:
            cursor += 1
            draw_full()
        elif key == 'SPACE':
            if len(items) > 0:
                lang = items[cursor]
                if lang in selected_names:
                    # Deselect
                    selected_names.remove(lang)
                elif len(selected_names) < 2:
                    # Select (max 2)
                    selected_names.append(lang)
                # If already 2 selected and trying to add a third, ignore
                draw_full()
        elif key == 'ENTER':
            if len(selected_names) == 2:
                clear_screen()
                print(green(f"  → Languages: {selected_names[0]} ↔ {selected_names[1]}"))
                print()
                return selected_names
            # If not exactly 2, ignore Enter
        elif key == 'BACKSPACE':
            if search_query:
                search_query = search_query[:-1]
                if search_query:
                    items = [l for l in all_languages if search_query.lower() in l.lower()]
                else:
                    items = list(all_languages)
                cursor = 0
                scroll_top = 0
                draw_full()
        elif isinstance(key, str) and len(key) == 1 and key.isprintable():
            # Live search: typing filters the list
            new_query = search_query + key
            filtered = [l for l in all_languages if new_query.lower() in l.lower()]
            if filtered:
                search_query = new_query
                items = filtered
                cursor = 0
                scroll_top = 0
            draw_full()



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
        return True  # not blocking


# ──────────────────────── Install dependencies ─────────────
def install_dependencies():
    req = os.path.join(PROJECT_DIR, "requirements.txt")
    if not os.path.exists(req):
        print(red("  requirements.txt not found!"))
        return False

    print(dim("  Running: pip install -r requirements.txt ..."))
    print()
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", req],
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
        return sorted([
            "english", "hebrew", "spanish", "french", "german", "italian",
            "portuguese", "russian", "chinese (simplified)", "chinese (traditional)",
            "japanese", "korean", "arabic", "turkish", "dutch", "polish",
            "swedish", "danish", "norwegian", "finnish", "greek", "czech",
            "romanian", "hungarian", "thai", "vietnamese", "indonesian",
            "malay", "filipino", "hindi", "bengali", "urdu", "persian",
            "ukrainian", "bulgarian", "croatian", "serbian", "slovak",
            "slovenian", "estonian", "latvian", "lithuanian",
        ])


# ──────────────────────── Auto-start Setup ─────────────────
def setup_autostart_windows():
    try:
        startup = os.path.join(
            os.environ.get("APPDATA", ""),
            "Microsoft", "Windows", "Start Menu", "Programs", "Startup",
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
        python_exe = sys.executable
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
        python_exe = sys.executable
        desktop_path = os.path.join(autostart_dir, f"{APP_NAME}.desktop")
        desktop_content = f"""[Desktop Entry]
Type=Application
Name={APP_NAME}
Exec={python_exe} {MAIN_SCRIPT}
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
    config = {
        "hotkey": hotkey,
        "auto_start": auto_start,
        "source_language": source_lang,
        "target_language": target_lang,
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    print(green(f"  Preferences saved to config.json ✓"))

# ──────────────────────── Preferences Questionnaire ────────
def run_questionnaire():
    """Run the interactive preferences questionnaire (Phase 2)."""
    print(cyan("══════════════════════════════════════════════"))
    print(cyan("║") + bold("       📋  Preferences Questionnaire         ") + cyan("║"))
    print(cyan("══════════════════════════════════════════════"))
    print()

    # --- Q1: Select 2 languages ---
    print(dim("  Fetching supported languages..."))
    languages = get_supported_languages()
    print(green(f"  {len(languages)} languages available ✓"))
    print()

    chosen_langs = ask_language(
        "1) Select your 2 languages:",
        languages,
    )
    source_lang = chosen_langs[0]
    target_lang = chosen_langs[1]

    # --- Q2: Auto-start ---
    default_hotkey = DEFAULTS.get(OS_NAME, "ctrl+shift+q")

    if OS_NAME == "Windows":
        run_cmd = "python main.py"
    else:
        run_cmd = "python3 main.py"

    auto_start_choice = ask_choice(
        "2) Do you want ShiftLang to run automatically when the computer starts?",
        [
            "Yes — start automatically on boot",
            f"No  — I prefer to run manually using:  {cyan(run_cmd)}",
        ],
    )
    auto_start = auto_start_choice == 0

    # --- Q3: Hotkey ---
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
        print(yellow("  ⚠  Make sure your chosen combination does not conflict with"))
        print(yellow("     other applications or system shortcuts on your OS."))
        print()
        print(dim("  Format examples: ctrl+shift+t, alt+g, cmd+shift+k"))
        hotkey = ask_input("Enter your preferred hotkey combination", default=default_hotkey)
        if not hotkey:
            hotkey = default_hotkey
    print()

    # ════════════════════════════════════════════
    #  Applying settings
    # ════════════════════════════════════════════
    print(bold("─── Applying settings ───"))
    print()

    save_config(hotkey, auto_start, source_lang, target_lang)

    if auto_start:
        setup_autostart()

    print()

    # ── Done ──
    print(cyan("══════════════════════════════════════════════"))
    print(green(bold("  ✅  ShiftLang is ready!")))
    print(cyan("══════════════════════════════════════════════"))
    print()
    print(f"  Languages:   {bold(source_lang)} ↔ {bold(target_lang)}")
    print(f"  Hotkey:      {bold(hotkey)}")
    print(f"  Auto-start:  {bold('Enabled' if auto_start else 'Disabled')}")
    print()
    if not auto_start:
        print(f"  To run ShiftLang manually:")
        print(f"    {cyan('cd ' + PROJECT_DIR)}")
        print(f"    {cyan(run_cmd)}")
        print()
    else:
        print(f"  ShiftLang will start automatically on next boot.")
        print(f"  To run it right now:")
        print(f"    {cyan('cd ' + PROJECT_DIR)}")
        print(f"    {cyan(run_cmd)}")
        print()
    print(dim("  Happy translating! ⚡"))
    print()


# ──────────────────────── Main Installer Flow ──────────────
def main():
    reconfigure = "--reconfigure" in sys.argv or "-r" in sys.argv

    clear_screen()
    banner()

    if reconfigure:
        # Skip installation, go straight to preferences
        print(dim("  Reconfiguring ShiftLang settings..."))
        print()
        run_questionnaire()
        return

    # ════════════════════════════════════════════
    #  PHASE 1 — Installation (automatic, quiet)
    # ════════════════════════════════════════════
    print(bold("─── Installing ShiftLang ───"))
    print()

    # Prerequisites
    ok = check_python() and check_pip()
    check_git()
    print()
    if not ok:
        print(red("Prerequisites check failed. Please fix the issues above and re-run."))
        sys.exit(1)
    print(green("  All prerequisites met!"))
    print()

    # Dependencies
    if not install_dependencies():
        print(red("Installation failed. Please check the errors above."))
        sys.exit(1)
    print()

    print(green(bold("  Installation complete ✓")))
    print()

    # PHASE 2 — Preferences
    run_questionnaire()


if __name__ == "__main__":
    main()
