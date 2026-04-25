# Configuration

Rica is configured primarily through:

```text
~/.rica/config.yaml
```

The easiest way to create it is:

```bash
rica onboard
```

## Example config

```yaml
discord:
  token: "YOUR_DISCORD_BOT_TOKEN_HERE"

provider:
  name: "google_ai"        # google_ai | openai | anthropic | openrouter | groq
  api_key: "YOUR_API_KEY_HERE"
  model: ""                # optional; empty means provider default

workers:
  responder:
    enabled: true
  moderator:
    enabled: false
  agent:
    enabled: false
  db_manager:
    enabled: false

trigger_word: "Rica"
```

## Config locations

| Path | Purpose |
|---|---|
| `~/.rica/config.yaml` | Main local config |
| `~/.rica/rica.log` | Background runtime log |
| `~/.rica/rica.pid` | Background process id |
| `bot/.env.example` | Optional env reference for compatibility |
| `config.yaml.example` | Manual config template |

## Providers

Supported provider IDs:

- `google_ai`
- `openai`
- `anthropic`
- `openrouter`
- `groq`

Model names are provider-specific. If you leave `model` empty, Rica uses the provider adapter's default or the model selected during onboarding.

## Workers

| Worker | What it does | Recommended default |
|---|---|---|
| Responder | Generates user-facing AI replies | On |
| Moderator | Reviews messages for safety/mod actions | Off until configured |
| DB Manager | Maintains context and local knowledge/history | Off for lightweight installs |
| Agent | Advanced owner/trusted-user workflows | Off unless you understand the risk |

## Trigger word

Default:

```yaml
trigger_word: "Rica"
```

Rica responds when the trigger word appears in the message or when the bot is mentioned.

## Environment variables

Rica still loads `.env` for backward compatibility, but local self-hosted mode should use `~/.rica/config.yaml`.

Useful overrides:

```bash
RICA_HOME=/custom/path rica start
DISCORD_BOT_TOKEN=... rica start
```

`RICA_HOME` changes where config, logs, and runtime state are stored.
