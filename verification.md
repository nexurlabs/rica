# Verification

This is the current verification state of Rica.

## Environment used

- OS: Linux
- Python: 3.12.3
- Node/npm: available on the VM
- Repo: `/home/rishabh/.openclaw/workspace/nexurlabs/rica`

## Backend and bot checks

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python -m compileall -q bot cli dashboard/api
pytest -q bot/tests
```

Result:

```text
51 passed, 7 skipped
```

## Dashboard web check

```bash
npm --prefix dashboard/web ci
npm --prefix dashboard/web run build
```

Result: production build completed successfully.

## Dashboard API check

```bash
uvicorn dashboard.api.main:app --host 127.0.0.1 --port 8765
curl http://127.0.0.1:8765/health
```

Result:

```json
{"status":"ok","mode":"local"}
```

## Not tested with live Discord token

The codebase is verified structurally and locally. A full live Discord test requires a real Discord bot token and server invite. Once those are available, use:

```bash
rica onboard
rica start --with-frontend
```

Then test in Discord:

```text
Rica hello
!status
!usage
```
