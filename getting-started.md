# Getting Started

## What You Need

Before installing Rica, make sure you have:

| Requirement | Details |
|-------------|---------|
| **Python** | 3.10 or higher |
| **Discord Bot Token** | From the [Discord Developer Portal](https://discord.com/developers/applications) |
| **LLM API Key** | OpenAI, Anthropic, or Gemini — you bring your own key |
| **Bot Permissions** | Server member with Admin or specific channel permissions |

## How Rica Works

1. A user sends a message in a channel where Rica is present
2. The **Moderator** worker checks the message for safety/spam
3. The **Responder** worker generates an AI response using your LLM
4. The **DB Manager** logs the conversation to SQLite
5. Rica replies in the same channel

## What Rica Does NOT Do

- Rica does **not** read messages outside channels it has access to
- Rica does **not** store data outside your own database
- Rica does **not** send analytics or telemetry anywhere
- Rica does **not** require your Discord password — bot accounts are separate

## Next Steps

Ready? Head to [Installation](installation) to get Rica running.
