# Commands

Rica currently has a small, real command surface in the Discord bot plus the local CLI.

## Discord commands available today

Rica listens for messages beginning with `!`.

| Command | What it does |
|---|---|
| `!status` | Shows trigger word, enabled workers, search/creative status, and active sessions |
| `!usage` | Shows stored usage statistics for the current server |

If no API key is configured, Rica will reply with a setup warning when triggered or when a command is used.

## AI chat

Rica does not require a separate `!ask` command. Mention the bot or use the trigger word:

```text
Rica explain this announcement in simpler words
```

or:

```text
@Rica can you summarize the last few messages?
```

## CLI commands

Run these in a terminal after installation.

| Command | Purpose |
|---|---|
| `rica onboard` | Interactive setup wizard |
| `rica start` | Start bot and dashboard API |
| `rica start --with-frontend` | Start bot, dashboard API, and dashboard UI |
| `rica start -d --with-frontend` | Start in background mode |
| `rica status` | Show config summary and runtime status |
| `rica doctor` | Diagnose common setup problems |
| `rica dashboard` | Open dashboard URL in browser |
| `rica logs` | Show background logs |
| `rica stop` | Stop background process |
| `rica update` | Pull latest source and reinstall/update dependencies |

## Planned / not currently documented as live

Older docs mentioned commands like `!ask`, `!help`, `!weather`, and slash commands. Those are not implemented in the current bot entry point, so they have been removed from the live docs to avoid misleading users.
