# Deployment

Rica can run on a laptop, Raspberry Pi, or VPS. For a real Discord server, a small Linux VPS is the simplest production setup.

## Simple VPS deployment

```bash
ssh user@your-server
curl -fsSL https://raw.githubusercontent.com/nexurlabs/rica/main/install.sh | bash
rica start --with-frontend -d
rica status
```

## Run behind Caddy

Recommended public layout:

- Keep the bot process private
- Reverse proxy only the dashboard UI/API if you actually need remote dashboard access
- Use HTTPS

Example Caddyfile:

```caddy
rica.example.com {
    encode gzip

    handle /api/* {
        reverse_proxy 127.0.0.1:8000
    }

    handle {
        reverse_proxy 127.0.0.1:3000
    }
}
```

Set your dashboard frontend API URL to match your deployment if needed.

## systemd service

Create `/etc/systemd/system/rica.service`:

```ini
[Unit]
Description=Rica Discord Assistant
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/home/YOUR_USER/.nexurlabs/rica
Environment=RICA_HOME=/home/YOUR_USER/.rica
ExecStart=/home/YOUR_USER/.nexurlabs/rica/.venv/bin/rica start --with-frontend
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now rica
sudo systemctl status rica
journalctl -u rica -f
```

## Updating

```bash
cd ~/.nexurlabs/rica
git pull
source .venv/bin/activate
pip install -e '.[dev]'
npm --prefix dashboard/web install
npm --prefix dashboard/web run build
sudo systemctl restart rica
```

or, if installed through the CLI:

```bash
rica update
rica stop
rica start --with-frontend -d
```

## Firewall

Minimum outbound access:

- Discord API over HTTPS
- Your selected LLM provider over HTTPS
- GitHub/npm/PyPI for installation and updates

Only expose inbound ports if you need remote dashboard access:

- `443` for HTTPS reverse proxy
- Avoid exposing raw `3000` and `8000` publicly

## Docker note

The current repository does not include a production Dockerfile. Use direct install/systemd unless a Docker setup is added later.
