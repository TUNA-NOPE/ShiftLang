# ShiftLang

A lightweight background tool that instantly translates selected text between any two languages with a single hotkey.

## Features

- **Any-to-any translation** — supports 130+ languages via multiple translation providers
- **13+ free providers** — Google, Bing, Yandex, Baidu, and more (no API keys needed!)
- **AI-powered translation** — use OpenRouter LLM for more accurate translations (optional)
- **Hotkey-driven** — press a hotkey to translate any selected text in-place
- **Auto language detection** — detects the input language and translates accordingly
- **Clipboard-safe** — translated text is excluded from Windows Clipboard History
- **Cross-platform** — works on Windows, macOS, and Linux (X11 & Wayland)
- **One-command install** — single command to set up everything
- **Virtual environment** — isolated Python dependencies (no system-wide installs)
- **Reconfigurable** — change settings anytime without reinstalling

## Requirements

- **Python 3.8+**
- **git** (to clone the repository)

## Quick Install

### One-Liner Install

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/TUNA-NOPE/ShiftLang/main/scripts/install.ps1 | iex
```

**macOS / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/TUNA-NOPE/ShiftLang/main/scripts/install-remote.sh | bash
```

This will automatically:
- Clone the repository to `~/ShiftLang`
- Run the interactive installer
- Set up everything for you

### Manual Install

#### Windows (PowerShell)

```powershell
git clone https://github.com/TUNA-NOPE/ShiftLang.git; cd ShiftLang; python scripts/install.py
```

#### macOS / Linux (Terminal)

```bash
git clone https://github.com/TUNA-NOPE/ShiftLang.git && cd ShiftLang && ./scripts/install.sh
```

The installer will automatically:
1. Check your Python version and git
2. Create a virtual environment (uses `uv` if available, otherwise `venv`)
3. Install all dependencies into the isolated environment
4. Guide you through a preferences questionnaire:
   - **Language selection** (choose 2 languages)
   - **Translation provider** (13+ free options or OpenRouter AI)
   - **Auto-start preference**
   - **Hotkey configuration**
5. Configure everything for you

## Usage

1. Select any text in any application.
2. Press your configured hotkey (default: **Ctrl+Shift+Q**).
3. The selected text is replaced with its translation.

## Translation Providers

ShiftLang supports **13+ free translation providers** that work without any API key:

### Free Providers (No API Key Required)

| Provider | Description | Best For |
|----------|-------------|----------|
| **Google** | Fast, reliable, 130+ languages | General use (default) |
| **Bing** | Microsoft Translator | Microsoft ecosystem users |
| **Yandex** | Yandex Translate | Russian & Eastern European languages |
| **MyMemory** | 5000 characters/day free | Occasional use |
| **Baidu** | Baidu Translate | Chinese translation |
| **Alibaba** | Alibaba Translate | Chinese translation |
| **Tencent (QQ)** | Tencent Translate | Chinese translation |
| **Sogou** | Sogou Translate | Chinese search-backed |
| **Youdao** | Youdao Translate | Popular in China |
| **Reverso** | Context-aware translation | Context understanding |
| **Itranslate** | Simple & fast | Quick translations |
| **Argos** | LibreTranslate (open source) | Privacy-conscious users |

### AI-Powered Provider

| Provider | Description | Best For |
|----------|-------------|----------|
| **OpenRouter** | AI-powered translation | High accuracy, complex text |

### Choosing Your Provider

**During installation:**
The installer will show you all available providers and let you choose.

**After installation:**
Edit your `config/config.json` to switch providers:

```json
{
  "hotkey": "ctrl+shift+q",
  "auto_start": true,
  "source_language": "english",
  "target_language": "hebrew",
  "translation_provider": "bing",
  "openrouter_api_key": "",
  "openrouter_model": "openrouter/free"
}
```

**Available provider values:**
- `google` — Google Translate
- `bing` — Bing Microsoft Translator
- `yandex` — Yandex Translate
- `mymemory` — MyMemory (5000 chars/day)
- `baidu` — Baidu Translate
- `alibaba` — Alibaba Translate
- `tencent` — Tencent (QQ) Translate
- `sogou` — Sogou Translate
- `youdao` — Youdao Translate
- `reverso` — Reverso Translate
- `itranslate` — Itranslate
- `argos` — Argos (LibreTranslate)
- `openrouter` — OpenRouter AI (requires API key for paid models)

**Note:** The `openrouter_api_key` field is optional. The free tier works without an API key, but you can get an API key from [OpenRouter](https://openrouter.ai/) for higher rate limits.

## Reconfigure Settings

To change your languages, hotkey, or provider without reinstalling:

```bash
# Windows
python scripts/install.py --reconfigure

# macOS / Linux
python3 scripts/install.py --reconfigure
```

Short form: `python scripts/install.py -r`

## Manual Run

If you chose not to enable auto-start, run ShiftLang manually:

```bash
# Windows
.venv\Scripts\python.exe bin\main.pyw

# macOS / Linux
.venv/bin/python bin/main.pyw
```

> **Note:** On Windows, run as administrator if the hotkey doesn't register in elevated windows.

### Wayland Users (Linux)

On Wayland sessions, ShiftLang uses a dedicated implementation with improved clipboard handling:

```bash
.venv/bin/python bin/shiftlang_wayland.py
```

## Project Structure

```
ShiftLang/
├── shiftlang/               # Core package (all library code)
│   ├── __init__.py          # Package exports
│   ├── config.py            # Configuration management
│   ├── language.py          # Language detection utilities
│   ├── translator.py        # Translator factory with 13+ providers
│   └── openrouter.py        # OpenRouter AI provider
├── scripts/                 # Install scripts
│   ├── install.py           # Interactive installer
│   ├── install.sh           # Bash wrapper
│   ├── install-remote.sh    # Remote installer (macOS/Linux)
│   └── install.ps1          # Remote installer (Windows)
├── bin/                     # Application entry points
│   ├── main.pyw             # Windows/macOS/X11
│   ├── shiftlang_wayland.py # Linux Wayland
│   └── apply_autostart.py   # Autostart utility
├── requirements/            # Dependencies
│   ├── requirements.txt     # Python dependencies
│   └── linux.txt            # Linux-specific dependencies
├── config/                  # Configuration
│   ├── config.json          # User preferences (generated)
│   └── config.example.json  # Config template
└── README.md
```

## Dependencies

| Package           | Purpose                          |
|-------------------|----------------------------------|
| `keyboard`        | Global hotkey registration       |
| `pyperclip`       | Cross-platform clipboard access  |
| `deep-translator` | Google & MyMemory translation    |
| `translators`     | Bing, Baidu, Yandex, etc.        |
| `requests`        | HTTP client for OpenRouter API   |

### System Requirements

- **Wayland (Linux)**: Requires `wl-clipboard` package for clipboard operations
  - Ubuntu/Debian: `sudo apt install wl-clipboard`
  - Fedora: `sudo dnf install wl-clipboard`
  - Arch: `sudo pacman -S wl-clipboard`

## License

This project is open source and available under the [MIT License](LICENSE).
