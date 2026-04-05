# Rica — AI Discord Assistant

<p align="center">
  <img src="https://nexurlabs.com/logo.png" width="80" alt="Rica Logo" />
</p>

> The ultimate self-hosted AI Discord assistant. Zero telemetry, Bring Your Own Key (BYOK).

Rica is a production-ready Discord bot powered by LLMs, featuring a 4-worker pipeline (Responder, Moderator, DB Manager, Agent), an embedded web dashboard, and a simple CLI setup.

---

## ✨ Features

- **🤖 Smart AI Responses** — LLM-powered replies that understand context, intent, and conversation flow
- **🛡️ Auto Moderation** — Keyword filtering, spam detection, and automated moderation actions
- **📊 Embedded Dashboard** — Live web UI for monitoring, config, and analytics
- **🔗 Webhook Integration** — Connect external services and trigger bot actions via webhooks
- **💬 Multi-Server Support** — Handles multiple Discord servers from a single instance
- **🔒 Self-Hosted** — Zero telemetry, your server, your data, your control

---

## 🏗️ Architecture

Rica uses a **4-worker pipeline**:

```
User Message
    │
    ├── Responder    → crafts and sends AI responses
    ├── Moderator    → checks message safety, runs moderation filters
    ├── DB Manager   → logs conversations, handles history
    └── Agent        → handles commands, external API calls
```

Powered by **Python + SQLite** — lightweight enough to run on a $5 VPS.

---

## 🚀 Quick Start

```bash
curl -fsSL https://raw.githubusercontent.com/nexurlabs/rica/main/install.sh | bash
```

That's it — one command. The installer detects your OS, installs dependencies, clones the repo if needed, and walks you through setup — Discord token, API keys, dashboard URL.

---

## 📖 Sections

- [Getting Started](getting-started) — What to expect and what you'll need
- [Installation](installation) — Step-by-step install guide
- [Configuration](configuration) — All config options explained
- [Commands](commands) — Bot commands and how to use them
- [Dashboard](dashboard) — Using the built-in web dashboard
- [Deployment](deployment) — Deploy on your own server or cloud
- [Troubleshooting](troubleshooting) — Common issues and fixes

---

<p align="center">
  <strong>Built with 💜 by <a href="https://nexurlabs.com">NexurLabs</a></strong><br/>
  <a href="https://github.com/nexurlabs/rica">GitHub</a> · <a href="https://nexurlabs.com">Website</a>
</p>
