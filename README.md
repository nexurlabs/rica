# Rica — self-hosted AI Discord assistant

<p align="center">
  <img src="https://nexurlabs.com/logo.png" width="84" alt="NexurLabs logo" />
</p>

Rica is an open-source Discord assistant for communities that want AI support without giving up control of their data. It runs on your own machine or VPS, stores configuration locally, and lets you bring your own LLM key.

## What Rica does today

- **AI replies in Discord** when someone mentions the bot or uses the configured trigger word, default: `Rica`
- **Four-worker pipeline** for community automation:
  - **Responder** answers user messages
  - **Moderator** can inspect messages and suggest moderation actions
  - **DB Manager** maintains context and local knowledge/history
  - **Agent** handles higher-trust advanced workflows for selected users
- **Provider support** for Google AI/Gemini, OpenAI, Anthropic, OpenRouter, and Groq
- **Local-first storage** under `~/.rica` with SQLite-style local persistence and encrypted API keys
- **FastAPI dashboard API** and **Next.js dashboard UI** for setup, keys, workers, channels, usage, errors, and data browsing
- **CLI workflow**: `rica onboard`, `rica start`, `rica status`, `rica doctor`, `rica logs`, `rica stop`, `rica update`

## Verified status

The current repository was checked on Linux with Python 3.12 and Node.js:

```bash
python -m compileall -q bot cli dashboard/api
pytest -q bot/tests
npm --prefix dashboard/web ci
npm --prefix dashboard/web run build
uvicorn dashboard.api.main:app --host 127.0.0.1 --port 8765
curl http://127.0.0.1:8765/health
```

Result: **51 Python tests passed, 7 skipped**, dashboard frontend builds successfully, and the dashboard API health endpoint returns `{"status":"ok","mode":"local"}`.

## Quick start

```bash
curl -fsSL https://raw.githubusercontent.com/nexurlabs/rica/main/install.sh | bash
```

The installer sets up Python, Node.js, the dashboard, and then launches interactive onboarding.

After onboarding:

```bash
rica start --with-frontend
```

Then open:

- Dashboard UI: `http://localhost:3000`
- Dashboard API: `http://localhost:8000`

## Documentation

- [Getting Started](getting-started.md)
- [Installation](installation.md)
- [Configuration](configuration.md)
- [Commands](commands.md)
- [Dashboard](dashboard.md)
- [Deployment](deployment.md)
- [Troubleshooting](troubleshooting.md)
- [Verification](verification.md)
- [Architecture](architecture.md)

## Privacy model

Rica is designed for self-hosting:

- No NexurLabs telemetry in the bot
- Discord messages are processed only where the bot has access
- API keys are yours, provided by you, and stored locally
- Local data lives in `~/.rica` unless you deliberately deploy it elsewhere

## Project structure

```text
rica/
├── bot/                 # Discord bot, workers, providers, local storage
├── cli/                 # Rica CLI and onboarding wizard
├── dashboard/api/       # FastAPI dashboard API
├── dashboard/web/       # Next.js dashboard frontend
├── install.sh           # Linux/macOS installer
├── install.ps1          # Windows PowerShell installer
└── *.md                 # Documentation site pages
```

<p align="center">
  Built by <a href="https://nexurlabs.com">NexurLabs</a> · Open source · BYOK
</p>
