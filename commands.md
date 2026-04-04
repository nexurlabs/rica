# Commands

Rica uses the bot prefix (default: `!`) to trigger commands.

## General Commands

| Command | Description |
|---------|-------------|
| `!help` | Show help message with all available commands |
| `!ping` | Check if Rica is responsive |
| `!info` | Show Rica version and status |
| `!stats` | Display bot statistics (servers, users, uptime) |

## AI Chat Commands

| Command | Description |
|---------|-------------|
| `!ask <question>` | Ask Rica anything |
| `!explain <topic>` | Get a detailed explanation of a topic |
| `!summarize <text>` | Summarize long text or a pasted message |

## Moderation Commands

| Command | Description |
|---------|-------------|
| `!mod status` | Show current moderation settings |
| `!mod logs [limit]` | View recent moderation actions |
| `!mod strike <user> [reason]` | Issue a strike to a user |
| `!mod strikes <user>` | List strikes for a user |

> **Note:** Moderation commands require the user to have moderation permissions.

## Dashboard Commands

| Command | Description |
|---------|-------------|
| `!dashboard` | Get the link to the web dashboard |
| `!logs` | Get recent log entries |

## Utility Commands

| Command | Description |
|---------|-------------|
| `!translate <text>` | Translate text (requires API config) |
| `!weather <city>` | Get current weather for a city |
| `!calc <expression>` | Quick calculator |

## Slash Commands

Rica also supports Discord **Slash Commands** for modern Discord clients:

```
/ask What is the capital of France?
/explain machine learning
/summarize [paste text]
/stats
```

Slash commands are automatically registered when Rica joins a server.

## Custom Commands (Server Admins)

Server admins can create custom responses:

```
!cmd add hello "Hello! Welcome to the server."
!cmd list
!cmd delete hello
```
