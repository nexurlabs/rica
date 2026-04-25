# Architecture

Rica is split into four runtime surfaces.

## 1. Discord bot

Path:

```text
bot/main.py
```

Responsibilities:

- Connect to Discord through `discord.py`
- Listen for messages
- Decide whether Rica is triggered
- Run worker pipeline
- Send replies and moderation actions

## 2. Worker pipeline

Path:

```text
bot/workers/
```

Workers:

```text
Message
  ├─ DB Manager   -> context/history support
  ├─ Moderator    -> safety/moderation review
  ├─ Responder    -> normal AI replies
  └─ Agent        -> trusted-user advanced workflows
```

## 3. Providers

Path:

```text
bot/providers/
```

Provider adapters normalize model calls for:

- Google AI
- OpenAI
- Anthropic
- OpenRouter
- Groq

## 4. Dashboard

```text
dashboard/api/   FastAPI backend
dashboard/web/   Next.js frontend
```

The dashboard manages setup, keys, workers, channels, data, usage, and errors.

## Local storage

Rica uses local self-hosted storage by default:

```text
~/.rica/
```

The storage compatibility modules keep old names such as `firestore_client` and `gcs_client`, but in local mode these map to local database/file implementations.

## Runtime flow

```text
Discord message
  -> trigger/command check
  -> load server config
  -> rate limit
  -> worker pipeline
  -> provider API call if needed
  -> Discord reply
  -> local persistence
```
