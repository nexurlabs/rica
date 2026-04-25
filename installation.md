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

From PowerShell, use the repository's `install.ps1` script after cloning or downloading the project.

```powershell
.\install.ps1
```

If Windows blocks script execution, run PowerShell as your user and use:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

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
