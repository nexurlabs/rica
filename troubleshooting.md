# Troubleshooting

## Common Issues

### Bot won't start — "Token not provided"

**Cause:** `DISCORD_BOT_TOKEN` is not set in your `.env` file.

**Fix:**
```bash
cp bot/.env.example bot/.env
nano bot/.env  # add your token
python bot/main.py
```

---

### Bot starts but goes offline immediately

**Cause:** The bot token is invalid or the bot has been disabled in the Discord Developer Portal.

**Fix:**
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Find your application → Bot
3. Make sure the bot is **Enabled**
4. Reset the token and update your `.env`

---

### "AI response failed: Model not found"

**Cause:** The LLM model name is wrong or the API key is missing.

**Fix:** Check your `.env`:
```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```

---

### Bot doesn't respond to messages

**Cause:** The bot doesn't have permission to read/send messages in the channel.

**Fix:**
1. In Discord Developer Portal → OAuth2 → URL Generator
2. Check scopes: `bot`, `applications.commands`
3. Check permissions: `Read Messages`, `Send Messages`, `Embed Links`
4. Use the generated URL to re-invite the bot

---

### Dashboard shows "Connection Refused"

**Cause:** Dashboard isn't running or is bound to the wrong interface.

**Fix:** Make sure `DASHBOARD_PORT` is set and the port isn't already in use:
```bash
lsof -i :3000
```

To bind to all interfaces (for remote access):
```env
DASHBOARD_HOST=0.0.0.0
```

---

### Messages are being sent but no AI response

**Cause:** The Responder worker might be overloaded or the LLM API is down.

**Fix:**
1. Check logs: `tail logs/rica.log`
2. Verify your LLM API key is valid
3. Try a different model in your config

---

### Database locked errors

**Cause:** Multiple Rica instances trying to write to the same SQLite file.

**Fix:** Only run one instance of Rica at a time. Use process managers like `systemd` or `pm2`.

---

## Getting Help

If you're stuck, open an issue on [GitHub](https://github.com/nexurlabs/rica/issues) with:
- Your `rica` version (`!info` in Discord)
- Relevant log output
- Steps to reproduce the issue
