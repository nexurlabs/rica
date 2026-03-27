# Rica — Open-Source AI Assistant for Discord

> Self-hosted, BYOK (Bring Your Own Key), multi-provider AI bot for Discord communities.

Rica is a **fully self-hosted** AI assistant for Discord that you run on your own machine. Bring your own API keys, choose your AI provider, and manage everything through a local web dashboard — no cloud dependency, no subscription, your data stays on your system.

Originally built by [NexurLabs](https://nexurlabs.com).

---

## Quick Start

```bash
# Install
pip install rica

# Setup (interactive wizard)
rica onboard

# Run
rica start

# Open dashboard in browser
rica dashboard
```

---

## Features

- **BYOK (Bring Your Own Key)** — use your own API keys from Google AI, OpenAI, Anthropic, OpenRouter, or Groq
- **4-Worker AI Pipeline** — Responder, Moderator, DB Manager, and Agent workers
- **Local Dashboard** — full web UI at `localhost:3000` for configuration, key management, and stats
- **Creative Tools** — Google Imagen, Lyria, and Veo integration for media generation
- **Sandboxed Code Execution** — Agent worker can execute Python code safely
- **Encrypted Key Storage** — API keys encrypted at rest with Fernet
- **Session Management** — intelligent conversation context with auto-cleanup
- **Rate Limiting** — built-in per-user rate limiting
- **100% Local** — all data stored on your machine, no cloud services required

---

## Requirements

- Python 3.11+
- A Discord bot token ([create one here](https://discord.com/developers/applications))
- An API key from at least one AI provider

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `rica onboard` | Interactive setup wizard |
| `rica start` | Start the bot and dashboard API |
| `rica dashboard` | Open the dashboard in your browser |
| `rica status` | Show current configuration summary |
| `rica doctor` | Diagnose common issues |

---

## Architecture

```
rica/
├── cli/              ← CLI entry point + onboarding wizard
├── bot/              ← Discord bot runtime
│   ├── workers/      ← AI pipeline (responder, moderator, db_manager, agent)
│   ├── providers/    ← AI provider adapters (Google, OpenAI, Anthropic, etc.)
│   ├── creative/     ← Media generation (Imagen, Lyria, Veo)
│   └── storage/      ← Local storage (SQLite + files)
├── dashboard/
│   ├── api/          ← FastAPI dashboard backend
│   └── web/          ← Next.js dashboard frontend
└── pyproject.toml
```

---

## Supported AI Providers

| Provider | Models |
|----------|--------|
| Google AI | Gemini 2.5 Pro, Gemini 2.5 Flash, etc. |
| OpenAI | GPT-4o, GPT-4.1, etc. |
| Anthropic | Claude 4 Sonnet, Claude 3.5 Haiku, etc. |
| OpenRouter | Any model on OpenRouter |
| Groq | Llama, Mixtral, etc. |

---

## Data Storage

All data is stored locally on your machine:

```
~/.rica/
├── config.yaml       ← Bot configuration
├── rica.db           ← SQLite database (usage stats, errors, sessions)
├── secret.key        ← Encryption key for API keys
├── files/            ← Data browser files
└── logs/             ← Bot logs (markdown)
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

[MIT](LICENSE) — built by [NexurLabs](https://nexurlabs.com).
