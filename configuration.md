# Configuration

All configuration lives in `bot/.env`. Copy from `bot/.env.example` to start.

## Required Variables

```env
# Discord
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# LLM Provider (choose one)
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...
# or
GEMINI_API_KEY=your_gemini_api_key_here

# LLM Model
LLM_MODEL=gpt-4o-mini
```

## Optional Variables

```env
# Bot Settings
BOT_PREFIX=!
BOT_DESCRIPTION=Rica AI Assistant
LOG_LEVEL=INFO

# Dashboard
DASHBOARD_PORT=3000
DASHBOARD_PASSWORD=change_me_pls

# Database
DB_PATH=./data/rica.db

# Moderation
MODERATION_ENABLED=true
MODERATION_STRIKE_THRESHOLD=3

# Response Settings
MAX_RESPONSE_LENGTH=2000
RESPONSE_DELAY_MS=500
```

## Environment Variable Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCORD_BOT_TOKEN` | — | **Required.** Your Discord bot token |
| `LLM_PROVIDER` | `openai` | LLM provider: `openai`, `anthropic`, `gemini` |
| `LLM_MODEL` | `gpt-4o-mini` | Model to use |
| `BOT_PREFIX` | `!` | Command prefix |
| `DASHBOARD_PORT` | `3000` | Web dashboard port |
| `DASHBOARD_PASSWORD` | random | Password for dashboard (auto-generated if not set) |
| `LOG_LEVEL` | `INFO` | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `MAX_RESPONSE_LENGTH` | `2000` | Max characters in a Discord message |
| `MODERATION_ENABLED` | `true` | Enable auto-moderation |

## Using a Config File

You can also use `config.yaml` instead of environment variables:

```yaml
discord:
  token: "your_token_here"

llm:
  provider: "openai"
  model: "gpt-4o-mini"
  api_key: "sk-..."

bot:
  prefix: "!"
  log_level: "INFO"

dashboard:
  port: 3000
  password: "change_me"
```

If both `.env` and `config.yaml` exist, `.env` takes precedence.
