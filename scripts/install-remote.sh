#!/bin/bash
# ShiftLang Remote Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/TUNA-NOPE/ShiftLang/main/scripts/install-remote.sh | bash

set -e

REPO_URL="https://github.com/TUNA-NOPE/ShiftLang.git"
INSTALL_DIR="$HOME/ShiftLang"
FORCE_REFRESH=0

# Parse arguments
for arg in "$@"; do
    case $arg in
        --force|-f)
            FORCE_REFRESH=1
            shift
            ;;
    esac
done

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

# Force refresh if requested
if [ "$FORCE_REFRESH" = "1" ] && [ -d "$INSTALL_DIR" ]; then
    echo "    Removing old installation..."
    rm -rf "$INSTALL_DIR"
fi

# Clone or update repository
if [ -d "$INSTALL_DIR" ]; then
    echo "    Updating repository..."
    cd "$INSTALL_DIR"
    # Stash any local changes and pull latest
    git stash push -m "install-remote stash" --quiet 2>/dev/null || true
    if git pull origin main 2>/dev/null; then
        echo "    ✓ Updated to latest version"
    else
        echo "    ⚠ Update failed, attempting fresh clone..."
        cd "$HOME"
        rm -rf "$INSTALL_DIR"
        git clone "$REPO_URL" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi
else
    echo "    Cloning repository..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo ""

# Run the installer
if command -v python3 &>/dev/null; then
    python3 scripts/install.py "$@"
else
    python scripts/install.py "$@"
fi
