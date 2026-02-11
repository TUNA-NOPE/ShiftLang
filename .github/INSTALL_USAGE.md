# Installation & Configuration Guide

ShiftLang installer now **auto-detects** whether you're doing a fresh install or reconfiguring!

## Quick Start

### Fresh Install (First Time)

```bash
./install.sh
```

If `config.json` doesn't exist, it automatically runs a fresh installation.

### Reconfigure (Change Settings)

```bash
./install.sh
```

If `config.json` exists, it automatically launches reconfigure mode to change your settings.

That's it! The script is smart enough to know what to do.

## Manual Modes

If you want to force a specific mode:

### Force Fresh Install
```bash
./install.sh           # Auto-detects
# OR
python install.py      # Manual
```

### Force Reconfigure
```bash
./install.sh --reconfigure
# OR
python install.py --reconfigure
```

### Silent/Auto Mode
```bash
./install.sh --auto
# OR
python install.py --auto
```

Uses saved config or defaults without prompting.

### Update Mode
```bash
./install.sh --update
# OR
python install.py --update
```

Updates dependencies and keeps existing config.

## What Gets Auto-Detected?

The `install.sh` script checks for `config.json`:

- **File exists** → Runs `python install.py --reconfigure`
  - Lets you change: languages, hotkey, translation provider, API key, auto-start

- **File missing** → Runs `python install.py`
  - Fresh installation with full setup wizard

## One-Liner Remote Install

For fresh installs from anywhere:

```bash
curl -sSL https://raw.githubusercontent.com/yourusername/ShiftLang/main/install.sh | bash
```

## Examples

### Scenario 1: First Time Setup
```bash
# Clone the repo
git clone https://github.com/yourusername/ShiftLang.git
cd ShiftLang

# Run installer (auto-detects fresh install)
./install.sh
```

### Scenario 2: Change Translation Provider
```bash
# Later, you want to switch from Google to OpenRouter
./install.sh
# Auto-detects existing config and opens reconfigure menu
```

### Scenario 3: Change Hotkey
```bash
# You want to change your hotkey
./install.sh
# Opens reconfigure menu automatically
```

### Scenario 4: Silent Update
```bash
# Pull latest changes and update
git pull
./install.sh --update
# Updates dependencies, keeps all settings
```

## Unattended Installation

For scripts/automation:

```bash
# Fresh install with defaults
./install.sh --auto

# Update existing installation
./install.sh --update

# Reconfigure with ESC hotkey
./install.sh --reconfigure --esc
```

## Troubleshooting

### "Python 3 is required but not found"

Install Python 3.8+:

**Ubuntu/Debian:**
```bash
sudo apt install python3 python3-pip
```

**Fedora:**
```bash
sudo dnf install python3 python3-pip
```

**macOS:**
```bash
brew install python3
```

### Script Not Executable

```bash
chmod +x install.sh
./install.sh
```

### Want to Start Over?

```bash
# Remove config and reinstall
rm config.json
./install.sh
```

## What Happens During Install?

1. **Checks Python** - Ensures Python 3.8+ is available
2. **Creates venv** - Isolated Python environment (fast with `uv`, standard fallback)
3. **Installs deps** - Installs required packages
4. **Configuration** - Interactive setup (auto-detected mode)
5. **Auto-start** - Optionally configures boot startup
6. **Launch** - Starts ShiftLang immediately

## Files Created

```
ShiftLang/
├── .venv/              # Virtual environment (auto-created)
├── config.json         # Your settings (auto-detected)
├── install.sh          # Smart installer script
├── install.py          # Python installer
└── main.py            # Main application
```

## Advanced Usage

### Using with Different Python Versions

```bash
# Use specific Python version
python3.11 install.py

# Or edit install.sh to prefer your version
```

### Install to Custom Location

```bash
# Just run from any directory
cd /path/to/ShiftLang
./install.sh
```

The virtual environment will be created in `.venv` within that directory.

## Related Guides

- [OpenRouter Setup](OPENROUTER_SETUP.md) - Configure AI-powered translation
- [README](README.md) - Project overview and features
- [Quick Start](QUICK_START.md) - Get started in 2 minutes

## Support

Issues or questions? Open an issue on GitHub!
