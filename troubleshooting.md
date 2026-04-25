# Troubleshooting

## Run doctor first

```bash
rica doctor
```

It checks config, token/key presence, encryption setup, and common runtime issues.

## Bot says API key is not configured

Rica needs at least one provider key configured.

Fix:

```bash
rica onboard
```

or edit:

```text
~/.rica/config.yaml
```

## Bot does not respond in Discord

Check:

1. Bot is online in the Discord member list
2. Message Content Intent is enabled in Discord Developer Portal
3. Bot has channel permissions: View Channel, Read Message History, Send Messages
4. You mentioned the bot or used the trigger word, default `Rica`
5. Responder worker is enabled

Run:

```bash
rica status
rica logs
```

## Invalid Discord token

Create/reset token in Discord Developer Portal:

1. Applications → your app → Bot
2. Reset Token
3. Run `rica onboard` again

Do not paste a user token. Rica uses a bot token only.

## Dashboard does not load

Check API:

```bash
curl http://localhost:8000/health
```

Check frontend:

```bash
cd dashboard/web
npm run build
npm run dev
```

If using a VPS, make sure your reverse proxy points to the correct ports.

## `python3 -m venv` fails on Ubuntu/Debian

Install venv support:

```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip
```

Then rerun the installer.

## Model or provider errors

Check provider name and key:

```yaml
provider:
  name: "google_ai"  # google_ai | openai | anthropic | openrouter | groq
  api_key: "..."
  model: ""
```

If a model name fails, leave `model` empty or choose a model returned during onboarding.

## SQLite/local database issues

Stop duplicate Rica processes:

```bash
rica stop
ps aux | grep rica
```

Then restart:

```bash
rica start --with-frontend -d
```

## Node dashboard vulnerabilities warning

`npm audit` may report issues from frontend dependencies. For production, review before using `npm audit fix --force`, because force upgrades can break Next.js dependency compatibility.
