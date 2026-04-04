# Dashboard

Rica comes with a built-in web dashboard for monitoring and management.

## Accessing the Dashboard

```
http://localhost:3000
```

Or, if Rica is running on a server, replace `localhost` with your server's IP or domain.

> **Important:** Change the `DASHBOARD_PASSWORD` in your `.env` file before exposing the dashboard publicly.

## Features

### 📊 Overview Panel

- Total messages processed
- Active servers count
- Response time trends
- Uptime indicator

### 💬 Conversation Logs

- Browse full conversation history
- Filter by server, channel, or user
- Search by keyword
- Export logs as JSON or CSV

### 🛡️ Moderation Dashboard

- View all moderation actions
- See strike counts per user
- Issue or remove strikes
- Configure moderation thresholds

### ⚙️ Configuration

- Update bot settings without restarting
- Restart specific workers
- Reload command registry
- View and edit the active config

### 📈 Analytics

- Message volume over time
- Most active channels
- Top users by message count
- LLM token usage (if tracking enabled)

## Securing the Dashboard

By default, the dashboard is password-protected. For production:

```env
DASHBOARD_PASSWORD=your_secure_password_here
DASHBOARD_PORT=3000
```

### Reverse Proxy (Recommended)

In production, serve the dashboard behind a reverse proxy (Nginx or Caddy) with HTTPS:

```nginx
location / {
    proxy_pass http://localhost:3000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

Or with Caddy:

```
rica.example.com {
    reverse_proxy localhost:3000
}
```
