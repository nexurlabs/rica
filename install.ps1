$ErrorActionPreference = 'Stop'

$RepoUrl = 'https://github.com/nexurlabs/rica.git'
$DefaultDir = Join-Path $HOME '.nexurlabs\rica'
$InstallDir = if ($env:RICA_DIR) { $env:RICA_DIR } else { $DefaultDir }

$SkipOnboard = [bool]$env:RICA_SKIP_ONBOARD
$SkipStart = [bool]$env:RICA_SKIP_START

function Write-Step($Message) {
  Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Write-Warn($Message) {
  Write-Host "[warn] $Message" -ForegroundColor Yellow
}

function Write-Ok($Message) {
  Write-Host "  ✓ $Message" -ForegroundColor Green
}

# Pick the best available package manager: winget > choco > scoop.
# Returns either 'winget', 'choco', 'scoop', or $null.
function Get-PackageManager {
  if (Get-Command winget -ErrorAction SilentlyContinue) { return 'winget' }
  if (Get-Command choco -ErrorAction SilentlyContinue) { return 'choco' }
  if (Get-Command scoop -ErrorAction SilentlyContinue) { return 'scoop' }
  return $null
}

function Install-Package($Id, $CommandName) {
  if (Get-Command $CommandName -ErrorAction SilentlyContinue) {
    Write-Ok "$CommandName already installed"
    return
  }

  $pm = Get-PackageManager
  if (-not $pm) {
    Write-Warn "Missing $CommandName and no supported package manager found."
    Write-Warn "Install $CommandName manually:"
    Write-Warn "  winget: https://aka.ms/getwinget"
    Write-Warn "  choco:  https://chocolatey.org/install"
    Write-Warn "  scoop:  https://scoop.sh"
    Write-Warn "Then re-run this installer."
    exit 1
  }

  Write-Step "Installing $CommandName via $pm"
  switch ($pm) {
    'winget' { winget install --accept-source-agreements --accept-package-agreements --id $Id }
    'choco'  { choco install -y $Id }
    'scoop'  { scoop install $Id }
  }
  if ($LASTEXITCODE -ne 0) {
    Write-Warn "Failed to install $CommandName via $pm (exit code $LASTEXITCODE)."
    exit 1
  }
  # Refresh PATH so the newly installed command is available immediately
  $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
  if (-not (Get-Command $CommandName -ErrorAction SilentlyContinue)) {
    Write-Warn "$CommandName installed but not on PATH. Open a new PowerShell window and re-run."
    exit 1
  }
}

function Get-RepoDir {
  if ((Test-Path './pyproject.toml') -and (Select-String -Path './pyproject.toml' -Pattern 'name = "rica"' -Quiet)) {
    return (Get-Location).Path
  }

  Install-Package 'Git.Git' 'git'
  $parent = Split-Path $InstallDir -Parent
  if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }

  if (Test-Path (Join-Path $InstallDir '.git')) {
    Write-Step "Updating existing Rica checkout at $InstallDir"
    git -C $InstallDir pull --ff-only | Out-Host
  } else {
    Write-Step "Cloning Rica into $InstallDir"
    git clone $RepoUrl $InstallDir | Out-Host
  }
  return $InstallDir
}

Install-Package 'Python.Python.3.12' 'py'
Install-Package 'OpenJS.NodeJS.LTS' 'node'
# npm ships with the Node LTS winget package, but choco users get it via the Node install.
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
  Install-Package 'OpenJS.NodeJS.LTS' 'npm'
}

$RepoDir = Get-RepoDir
Set-Location $RepoDir

Write-Step 'Creating Python virtual environment'
py -m venv .venv

$pythonExe = Join-Path $RepoDir '.venv\Scripts\python.exe'
$ricaExe = Join-Path $RepoDir '.venv\Scripts\rica.exe'

# Ensure the .venv\Scripts folder is permanently in the User PATH
# so the 'rica' command works even after the terminal is closed.
$venvScripts = Join-Path $RepoDir '.venv\Scripts'

# Update current session PATH so the rest of the script works
if ($env:Path -notmatch [regex]::Escape($venvScripts)) {
    $env:Path = "$venvScripts;$env:Path"
}

# Update permanent User PATH in Windows registry
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notmatch [regex]::Escape($venvScripts)) {
    Write-Host "  Adding Rica to User PATH..." -ForegroundColor DarkGray
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$venvScripts", "User")
}

Write-Step 'Upgrading pip'
& $pythonExe -m pip install --upgrade pip

Write-Step 'Installing Rica backend dependencies'
& $pythonExe -m pip install -e '.[dev]'

Write-Step 'Installing Rica dashboard web dependencies (this can take a minute)'
Push-Location (Join-Path $RepoDir 'dashboard\web')
npm install --no-fund --no-audit --loglevel=error | Out-Host
Pop-Location

function Show-PostInstall {
  Write-Host "`nRica is installed. Rica commands:" -ForegroundColor Green
  Write-Host "  rica start --with-frontend -d   (Run in background)"
  Write-Host "  rica logs                       (View background logs)"
  Write-Host "  rica stop                       (Stop background bot)"
  Write-Host "  rica update                     (Update to latest version)`n"
}

if (-not $SkipOnboard) {
  Write-Host "`n==> Web dependencies installed. Next: onboarding will open interactively." -ForegroundColor Yellow
  Write-Host "==> If the terminal looks idle for a moment, wait — the prompt is loading.`n" -ForegroundColor Yellow
  Write-Step 'Launching Rica onboarding'
  & $ricaExe onboard
} else {
  Write-Ok "Skipping onboard (RICA_SKIP_ONBOARD=1). Run 'rica onboard' later."
}

if ($SkipStart) {
  Show-PostInstall
  exit 0
}

$startNow = Read-Host "Start Rica now? [Y/n]"
if ([string]::IsNullOrWhiteSpace($startNow) -or $startNow -match '^[Yy]$') {
  Write-Host "`n==> Starting Rica and the dashboard frontend in background mode..." -ForegroundColor Yellow
  Write-Host "==> API: http://localhost:8000" -ForegroundColor Yellow
  Write-Host "==> Dashboard UI: http://localhost:3000`n" -ForegroundColor Yellow
  Write-Step 'Starting Rica + dashboard frontend (daemon)'
  & $ricaExe start --with-frontend -d
  exit $LASTEXITCODE
}

Show-PostInstall
