$ErrorActionPreference = 'Stop'

$RepoUrl = 'https://github.com/nexurlabs/rica.git'
$DefaultDir = Join-Path $HOME '.nexurlabs\rica'
$InstallDir = if ($env:RICA_DIR) { $env:RICA_DIR } else { $DefaultDir }

function Write-Step($Message) {
  Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Ensure-Command($Command, $WingetId) {
  if (Get-Command $Command -ErrorAction SilentlyContinue) { return }
  if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw "Missing $Command and winget is unavailable. Please install $Command manually."
  }
  Write-Step "Installing $Command via winget"
  winget install --accept-source-agreements --accept-package-agreements --id $WingetId
}

function Get-RepoDir {
  if ((Test-Path './pyproject.toml') -and (Select-String -Path './pyproject.toml' -Pattern 'name = "rica"' -Quiet)) {
    return (Get-Location).Path
  }

  Ensure-Command git 'Git.Git'
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

Ensure-Command py 'Python.Python.3.12'
Ensure-Command node 'OpenJS.NodeJS.LTS'
Ensure-Command npm 'OpenJS.NodeJS.LTS'

$RepoDir = Get-RepoDir
Set-Location $RepoDir

Write-Step 'Creating Python virtual environment'
py -m venv .venv

$pythonExe = Join-Path $RepoDir '.venv\Scripts\python.exe'
$ricaExe = Join-Path $RepoDir '.venv\Scripts\rica.exe'

Write-Step 'Upgrading pip'
& $pythonExe -m pip install --upgrade pip

Write-Step 'Installing Rica backend dependencies'
& $pythonExe -m pip install -e '.[dev]'
& $pythonExe -m pip install -r bot/requirements.txt -r dashboard/api/requirements.txt

Write-Step 'Installing Rica dashboard web dependencies'
Push-Location (Join-Path $RepoDir 'dashboard\web')
npm install | Out-Host
Pop-Location

Write-Step 'Launching Rica onboarding'
& $ricaExe onboard

Write-Host "`nRica is installed. Next steps:" -ForegroundColor Green
Write-Host "  cd $RepoDir"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  rica start`n"
