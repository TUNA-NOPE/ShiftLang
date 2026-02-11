#!/bin/bash
# ShiftLang Installer Bootstrap
# Usage: ./install.sh [--auto] [--update] [--reconfigure]
#
# Auto-detects if this is a fresh install or reconfiguration:
# - If config.json exists and no args provided → runs with --reconfigure
# - If config.json doesn't exist → runs fresh install
# - If args are provided → passes them through as-is

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../config/config.json"

# Ensure config directory exists
mkdir -p "$(dirname "$CONFIG_FILE")"

# Find Python
if command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
else
    echo "Error: Python 3 is required but not found."
    echo "Please install Python 3.8+ and try again."
    exit 1
fi

# Auto-detect mode if no arguments provided
if [ $# -eq 0 ]; then
    if [ -f "$CONFIG_FILE" ]; then
        echo "📝 Detected existing installation - launching reconfigure mode"
        echo ""
        $PYTHON "$SCRIPT_DIR/install.py" --reconfigure
    else
        echo "🆕 No existing config found - launching fresh install"
        echo ""
        $PYTHON "$SCRIPT_DIR/install.py"
    fi
else
    # Arguments provided, pass them through
    $PYTHON "$SCRIPT_DIR/install.py" "$@"
fi
