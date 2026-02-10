#!/bin/bash
# ShiftLang Installer Bootstrap
# Usage: ./install.sh [--auto] [--update] [--reconfigure]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if command -v python3 &>/dev/null; then
    python3 "$SCRIPT_DIR/install.py" "$@"
elif command -v python &>/dev/null; then
    python "$SCRIPT_DIR/install.py" "$@"
else
    echo "Error: Python 3 is required but not found."
    echo "Please install Python 3.8+ and try again."
    exit 1
fi
