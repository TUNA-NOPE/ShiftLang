# ShiftLang Remote Installer for Windows
# Usage: irm https://raw.githubusercontent.com/TUNA-NOPE/ShiftLang/main/scripts/install.ps1 | iex
#
# This script downloads and installs ShiftLang on Windows

param(
    [switch]$Auto,
    [switch]$Update,
    [switch]$Reconfigure,
    [switch]$NoSelfUpdate
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

function Get-InstallPyPath {
    # Returns the expected path to install.py
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
    
    # Build arguments
    $installArgs = @()
    if ($Auto) { $installArgs += "--auto" }
    if ($Update) { $installArgs += "--update" }
    if ($Reconfigure) { $installArgs += "--reconfigure" }
    
    Write-Host "    Running installer from: $installPy" -ForegroundColor DarkGray
    Write-Host ""
    
    & $PythonPath $installPy @installArgs
}

function Install-FromRemote {
    param(
        [string]$PythonPath
    )
    
    Write-Host "    Downloading and running installer directly..." -ForegroundColor DarkGray
    Write-Host ""
    
    # Ensure requirements directory exists and download requirements files
    $reqDir = Join-Path $INSTALL_DIR "requirements"
    if (-not (Test-Path $reqDir)) {
        Write-Host "    Creating requirements directory..." -ForegroundColor DarkGray
        New-Item -ItemType Directory -Path $reqDir -Force | Out-Null
    }
    
    # Download requirements files
    $reqFiles = @("requirements.txt", "requirements-base.txt")
    foreach ($reqFile in $reqFiles) {
        $reqUrl = "$RAW_URL/requirements/$reqFile"
        $reqPath = Join-Path $reqDir $reqFile
        if (-not (Test-Path $reqPath)) {
            Write-Host "    Downloading $reqFile..." -ForegroundColor DarkGray
            try {
                Invoke-WebRequest -Uri $reqUrl -OutFile $reqPath -UseBasicParsing
            }
            catch {
                Write-Host "    ⚠ Failed to download $reqFile" -ForegroundColor Yellow
            }
        }
    }
    
    # Download and execute install.py directly
    $installPyUrl = "$RAW_URL/scripts/install.py"
    
    try {
        # Use Invoke-WebRequest to download to temp file and execute
        $tempFile = [System.IO.Path]::GetTempFileName() + ".py"
        Invoke-WebRequest -Uri $installPyUrl -OutFile $tempFile -UseBasicParsing
        
        $installArgs = @()
        if ($Auto) { $installArgs += "--auto" }
        if ($Update) { $installArgs += "--update" }
        if ($Reconfigure) { $installArgs += "--reconfigure" }
        
        & $PythonPath $tempFile @installArgs
        
        # Cleanup
        Remove-Item $tempFile -ErrorAction SilentlyContinue
    }
    catch {
        Write-Host "    ✗ Failed to download/run remote installer: $_" -ForegroundColor Red
        throw
    }
}

function Install-ShiftLang {
    param(
        [string]$PythonPath
    )
    
    # Clone or update repository first
    $repoUpdated = $false
    if (Test-Path $INSTALL_DIR) {
        Write-Host "    Updating repository..." -ForegroundColor DarkGray
        Set-Location $INSTALL_DIR
        try {
            $pullOutput = git pull origin main 2>&1
            $repoUpdated = $true
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
            $repoUpdated = $true
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

# Check if we're being run from web (no local context)
if ($MyInvocation.MyCommand.Path -eq $null) {
    # Running from web (irm | iex)
    Write-Host "    Detected remote execution mode" -ForegroundColor DarkGray
    Write-Host ""
}

Install-ShiftLang -PythonPath $pythonPath
