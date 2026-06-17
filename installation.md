# Installation

## Recommended: one-command installer

Linux/macOS:

```bash
curl -fsSL https://raw.githubusercontent.com/nexurlabs/rica/main/install.sh | bash
```

The installer will:

1. Install missing system dependencies where possible: Git, Python, venv support, Node.js/npm
2. Clone or update Rica into `~/.nexurlabs/rica`
3. Create a Python virtual environment
4. Install the Rica Python package in editable mode
5. Install dashboard web dependencies
6. Launch `rica onboard`

## Windows PowerShell

Windows users have two paths: a one-line web pipeline (no clone required) or a manual local install.

### One-liner (PowerShell 5.1+ or PowerShell 7)

Open PowerShell and run:

```powershell
iwr -useb https://raw.githubusercontent.com/nexurlabs/rica/main/install.ps1 | iex
```

The installer:

1. Detects winget / chocolatey / scoop (prefers winget, falls back gracefully)
2. Installs Git, Python 3.11+, Node.js 18+ if missing
3. Clones Rica into `%USERPROFILE%\.nexurlabs\rica` (or updates an existing checkout)
4. Creates a virtualenv, installs Rica in editable mode + dashboard web deps
5. Runs `rica onboard` interactively
6. Offers to start Rica + dashboard in background

If Windows blocks script execution, allow it for the current user first:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Local install (clone first)

```powershell
git clone https://github.com/nexurlabs/rica.git
cd rica
.\install.ps1
```

### Manual install on Windows

If neither winget nor choco nor scoop is available, install prerequisites manually:

1. **Git for Windows** — https://git-scm.com/download/win (use Git Bash defaults)
2. **Python 3.11+** — https://www.python.org/downloads/windows/
   - Check **Add Python to PATH** during install
   - Check **tcl/tk and IDLE** if you want the Python launcher
3. **Node.js 18+** — https://nodejs.org/en/download (LTS recommended)

Then:

```powershell
git clone https://github.com/nexurlabs/rica.git
cd rica
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
cd dashboard\web
npm install
cd ..\..
rica onboard
```

> Note: on Windows, venv activation uses `Scripts\Activate.ps1`, not `bin/activate`.
> Use `pip install -e ".[dev]"` (double quotes) instead of `'.[dev]'` (single quotes) in PowerShell.

### Windows-specific notes

- `rica start -d` (background daemon mode) works on Windows since `subprocess.Popen` is patched with `CREATE_NO_WINDOW` to suppress the console flash.
- Logs are tailed via PowerShell `Get-Content -Wait -Tail` (set automatically when you run `rica logs` from PowerShell).
- File paths use backslashes internally; Rica normalizes them on read/write.
- The encryption key (`%USERPROFILE%\.rica\secret.key`) uses the same Fernet format as Linux/macOS — backups are cross-compatible.
- No WSL required: Rica runs natively on Windows.

## Manual install

```bash
git clone https://github.com/nexurlabs/rica.git
cd rica

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'

cd dashboard/web
npm install
cd ../..

rica onboard
rica start --with-frontend
```

## Onboarding

Run:

```bash
rica onboard
```

It asks for:

1. Discord bot token
2. LLM provider
3. API key
4. Optional model selection
5. Which workers to enable

It writes config to:

```text
~/.rica/config.yaml
```

## Start Rica

Foreground mode:

```bash
rica start --with-frontend
```

Background mode:

```bash
rica start --with-frontend -d
rica logs
rica stop
```

## Verify the install

```bash
rica status
rica doctor
```

For development checks:

```bash
pytest -q bot/tests
npm --prefix dashboard/web run build
```
