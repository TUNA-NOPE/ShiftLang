# ShiftLang Remote Installer for Windows
# Usage: irm https://raw.githubusercontent.com/TUNA-NOPE/ShiftLang/main/scripts/install.ps1 | iex
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
$RAW_URL = "https://raw.githubusercontent.com/TUNA-NOPE/ShiftLang/main"

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

function Ensure-Requirements {
    <#
    Ensures requirements directory and files exist.
    Downloads from GitHub if missing.
    #>
    param(
        [string]$ReqDir
    )
    
    # Create requirements directory if it doesn't exist
    if (-not (Test-Path $ReqDir)) {
        Write-Host "    Creating requirements directory..." -ForegroundColor DarkGray
        New-Item -ItemType Directory -Path $ReqDir -Force | Out-Null
    }
    
    # Download requirements files if missing
    $reqFiles = @(
        @{ Name = "requirements.txt"; Critical = $true },
        @{ Name = "requirements-base.txt"; Critical = $false },
        @{ Name = "linux.txt"; Critical = $false }
    )
    
    foreach ($req in $reqFiles) {
        $reqPath = Join-Path $ReqDir $req.Name
        if (-not (Test-Path $reqPath)) {
            $reqUrl = "$RAW_URL/requirements/$($req.Name)"
            Write-Host "    Downloading $($req.Name)..." -ForegroundColor DarkGray
            try {
                Invoke-WebRequest -Uri $reqUrl -OutFile $reqPath -UseBasicParsing -ErrorAction Stop
                Write-Host "    ✓ Downloaded $($req.Name)" -ForegroundColor Green
            }
            catch {
                if ($req.Critical) {
                    Write-Host "    ✗ Failed to download $($req.Name): $_" -ForegroundColor Red
                    throw
                }
                else {
                    Write-Host "    ⚠ Failed to download $($req.Name)" -ForegroundColor Yellow
                }
            }
        }
    }
}

function Get-InstallPyPath {
    return Join-Path $INSTALL_DIR "scripts" "install.py"
}

function Test-InstallPyExists {
    $installPy = Get-InstallPyPath
    return Test-Path $installPy
}

function Install-FromLocal {
    param(
        [string]$PythonPath
    )
    
    $installPy = Get-InstallPyPath
    
    # Ensure requirements exist before running
    $reqDir = Join-Path $INSTALL_DIR "requirements"
    Ensure-Requirements -ReqDir $reqDir
    
    # Build arguments
    $installArgs = @()
    if ($Auto) { $installArgs += "--auto" }
    if ($Update) { $installArgs += "--update" }
    if ($Reconfigure) { $installArgs += "--reconfigure" }
    
    Write-Host "    Running installer..." -ForegroundColor DarkGray
    Write-Host ""
    
    & $PythonPath $installPy @installArgs
}

function Install-FromRemote {
    param(
        [string]$PythonPath
    )
    
    Write-Host "    Running installer from remote..." -ForegroundColor DarkGray
    Write-Host ""
    
    # Ensure requirements exist (download them)
    $reqDir = Join-Path $INSTALL_DIR "requirements"
    Ensure-Requirements -ReqDir $reqDir
    
    # Download install.py to temp location
    $installPyUrl = "$RAW_URL/scripts/install.py"
    $tempFile = [System.IO.Path]::GetTempFileName() + ".py"
    
    try {
        Invoke-WebRequest -Uri $installPyUrl -OutFile $tempFile -UseBasicParsing -ErrorAction Stop
        
        $installArgs = @()
        if ($Auto) { $installArgs += "--auto" }
        if ($Update) { $installArgs += "--update" }
        if ($Reconfigure) { $installArgs += "--reconfigure" }
        
        & $PythonPath $tempFile @installArgs
    }
    finally {
        Remove-Item $tempFile -ErrorAction SilentlyContinue
    }
}

function Install-ShiftLang {
    param(
        [string]$PythonPath
    )
    
    # Clone or update repository first
    $repoExists = Test-Path $INSTALL_DIR
    
    if ($repoExists) {
        Write-Host "    Updating repository..." -ForegroundColor DarkGray
        Set-Location $INSTALL_DIR
        try {
            $pullOutput = git pull origin main 2>&1
            if ($pullOutput -match "Already up to date") {
                Write-Host "    ✓ Repository is up to date" -ForegroundColor Green
            }
            else {
                Write-Host "    ✓ Repository updated" -ForegroundColor Green
            }
        }
        catch {
            Write-Host "    ⚠ Git pull failed, using existing version" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "    Cloning repository..." -ForegroundColor DarkGray
        try {
            $null = git clone -q $REPO_URL $INSTALL_DIR 2>&1
            Write-Host "    ✓ Repository cloned" -ForegroundColor Green
        }
        catch {
            Write-Host "    ✗ Git clone failed: $_" -ForegroundColor Red
            throw
        }
    }
    
    Write-Host ""
    
    # Check if install.py exists locally
    $installPyExists = Test-InstallPyExists
    
    if ($installPyExists) {
        # Try local install first
        try {
            Install-FromLocal -PythonPath $PythonPath
            return
        }
        catch {
            Write-Host ""
            Write-Host "    ⚠ Local installer failed, trying remote..." -ForegroundColor Yellow
            Write-Host ""
        }
    }
    
    # Fall back to remote install
    Install-FromRemote -PythonPath $PythonPath
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
