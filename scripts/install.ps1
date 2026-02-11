# ShiftLang Remote Installer for Windows
# Usage: irm https://raw.githubusercontent.com/TUNA-NOPE/ShiftLang/main/install.ps1 | iex
#
# This script downloads and installs ShiftLang on Windows

param(
    [switch]$Auto,
    [switch]$Update,
    [switch]$Reconfigure
)

$ErrorActionPreference = "Stop"

$REPO_URL = "https://github.com/TUNA-NOPE/ShiftLang.git"
$INSTALL_DIR = "$env:USERPROFILE\ShiftLang"

function Write-Banner {
    Write-Host ""
    Write-Host "   ╭───────────────────────────────────────────────╮" -ForegroundColor Cyan
    Write-Host "   │                                               │"
    Write-Host "   │     ⚡  S H I F T L A N G  ⚡              │"
    Write-Host "   │                                               │"
    Write-Host "   │     Remote Installer (Windows)                │"
    Write-Host "   │                                               │"
    Write-Host "   ╰───────────────────────────────────────────────╯" -ForegroundColor Cyan
    Write-Host ""
    Write-Host ""
}

function Test-Python {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
    }
    
    if (-not $pythonCmd) {
        Write-Host "    ✗ Python 3.8+ is required but not found." -ForegroundColor Red
        Write-Host ""
        Write-Host "    Please install Python from: https://python.org/downloads"
        Write-Host "    Make sure to check 'Add Python to PATH' during installation."
        Write-Host ""
        exit 1
    }
    
    # Check Python version
    try {
        $versionOutput = & $pythonCmd.Source --version 2>&1
        $versionString = $versionOutput -replace "Python "
        $version = [System.Version]$versionString
        
        if ($version -lt [System.Version]"3.8") {
            Write-Host "    ✗ Python $versionString found, but Python 3.8+ is required." -ForegroundColor Red
            Write-Host ""
            exit 1
        }
        
        return $pythonCmd.Source
    }
    catch {
        Write-Host "    ✗ Could not determine Python version." -ForegroundColor Red
        Write-Host ""
        exit 1
    }
}

function Test-Git {
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    
    if (-not $gitCmd) {
        Write-Host "    ✗ git is required but not found." -ForegroundColor Red
        Write-Host ""
        Write-Host "    Please install Git from: https://git-scm.com/download/win"
        Write-Host ""
        exit 1
    }
    
    return $gitCmd.Source
}

function Install-ShiftLang {
    param(
        [string]$PythonPath
    )
    
    # Clone or update repository
    if (Test-Path $INSTALL_DIR) {
        Write-Host "    Updating repository..." -ForegroundColor DarkGray
        Set-Location $INSTALL_DIR
        try {
            $null = git pull origin main 2>&1
        }
        catch {
            Write-Host "    ⚠ Using existing version" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "    Cloning repository..." -ForegroundColor DarkGray
        $null = git clone -q $REPO_URL $INSTALL_DIR
        Set-Location $INSTALL_DIR
    }
    
    Write-Host ""
    
    # Build arguments for install.py
    $installArgs = @()
    if ($Auto) { $installArgs += "--auto" }
    if ($Update) { $installArgs += "--update" }
    if ($Reconfigure) { $installArgs += "--reconfigure" }
    
    # Run the installer
    Write-Host "    Running installer..." -ForegroundColor DarkGray
    Write-Host ""
    
    & $PythonPath install.py @installArgs
}

# Main execution
Write-Banner

Write-Host "    Checking prerequisites..." -ForegroundColor DarkGray
Write-Host ""

$pythonPath = Test-Python
$null = Test-Git

Write-Host "    ✓ Python found" -ForegroundColor Green
Write-Host "    ✓ Git found" -ForegroundColor Green
Write-Host ""

Install-ShiftLang -PythonPath $pythonPath
