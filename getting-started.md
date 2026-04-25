# Getting Started

This page explains what Rica is, what you need, and what to expect after installation.

## Who Rica is for

Use Rica if you want a Discord bot that can answer questions, help manage a server, and keep community AI workflows under your control.

Good fits:

- Student, gaming, builder, or startup communities
- Servers that want a custom AI personality
- Teams that want BYOK instead of a hosted SaaS bot
- Developers who want to modify the bot and dashboard themselves

## Requirements

| Requirement | Why it is needed |
|---|---|
| Python 3.11+ | Bot, CLI, dashboard API |
| Node.js + npm | Next.js dashboard frontend |
| Git | Install and update from source |
| Discord bot token | Lets Rica connect to Discord as a bot |
| One LLM API key | Google AI, OpenAI, Anthropic, OpenRouter, or Groq |

## How Rica works

1. A Discord message arrives in a server where Rica is installed.
2. Rica checks whether the bot should act:
   - message mentions the bot, or
   - message contains the configured trigger word, default `Rica`, or
   - message is a Rica command such as `!status`.
3. The pipeline runs enabled workers:
   - DB Manager can preserve context/history
   - Moderator can inspect message safety
   - Responder generates the actual reply
   - Agent can run advanced owner-approved workflows
4. Rica replies in Discord and stores local state under `~/.rica`.

## Important Discord setup

In the Discord Developer Portal, enable these bot settings:

- **Message Content Intent**
- **Server Members Intent** if moderation/member workflows are needed
- Bot permissions for the target server/channel:
  - View Channels
  - Read Message History
  - Send Messages
  - Embed Links
  - Use Slash Commands, if you later add slash command support
  - Moderate Members / Manage Messages only if using moderation features

## Data and privacy

Rica does not need your Discord password. It uses a Discord bot token.

By default, Rica stores runtime data locally in:

```text
~/.rica/
```

This includes config, encrypted keys, logs, local database files, and bot runtime state.

## Next step

Go to [Installation](installation.md) and run the installer.
