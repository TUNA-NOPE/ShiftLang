#!/bin/bash
# ShiftLang Remote Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/TUNA-NOPE/ShiftLang/main/install-remote.sh | bash

set -e

REPO_URL="https://github.com/TUNA-NOPE/ShiftLang.git"
INSTALL_DIR="$HOME/ShiftLang"

echo ""
echo "   ╭───────────────────────────────────────────────╮"
echo "   │                                               │"
echo "   │     ⚡  S H I F T L A N G  ⚡              │"
echo "   │                                               │"
echo "   │     Remote Installer                          │"
echo "   │                                               │"
echo "   ╰───────────────────────────────────────────────╯"
echo ""
echo ""

# Check for Python
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo "    ✗ Python 3.8+ required"
    echo ""
    exit 1
fi

# Check for git
if ! command -v git &>/dev/null; then
    echo "    ✗ git required"
    echo ""
    exit 1
fi

# Clone or update repository
if [ -d "$INSTALL_DIR" ]; then
    echo "    Updating repository..."
    cd "$INSTALL_DIR"
    git pull origin main || {
        echo "    ⚠ Using existing version"
    }
else
    echo "    Cloning repository..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo ""

# Run the installer
if command -v python3 &>/dev/null; then
    python3 install.py "$@"
else
    python install.py "$@"
fi
