# Deployment

## Deploy on a VPS / Dedicated Server

### Ubuntu / Debian

```bash
# SSH into your server
ssh user@your-server

# Install Python and Git
sudo apt update && sudo apt install -y python3 python3-venv git

# Clone the repo
git clone https://github.com/nexurlabs/rica.git
cd rica

# Run the installer
bash run.sh

# Set up systemd for auto-restart
sudo cp deploy/rica.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rica
sudo systemctl start rica
```

### Checking Status

```bash
sudo systemctl status rica
```

### Viewing Logs

```bash
# systemd logs
sudo journalctl -u rica -f

# Bot logs
tail -f logs/rica.log
```

## Deploy with Docker

```bash
# Build the image
docker build -t nexurlabs/rica .

# Run with environment file
docker run -d \
  --name rica \
  --env-file bot/.env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  nexurlabs/rica
```

## Deploy with Docker Compose

```yaml
services:
  rica:
    build: .
    container_name: rica
    env_file: bot/.env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
```

```bash
docker compose up -d
```

## Cloud Platforms

### Railway

1. Fork the Rica repo to your GitHub
2. Connect the repo to [Railway](https://railway.app)
3. Add environment variables from your `.env`
4. Deploy — Railway auto-detects Python

### Render

1. Fork the Rica repo
2. Create a new **Web Service** on [Render](https://render.com)
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python bot/main.py`
5. Add environment variables

### Fly.io

```bash
fly launch
fly secrets set DISCORD_BOT_TOKEN=your_token
fly deploy
```

## Firewall Setup

Make sure your firewall allows:
- **Port 3000** — Dashboard (restrict to your IP in production)
- **Port 443** — HTTPS (if using a reverse proxy)
- **Outbound 443** — Discord API + your LLM provider API

## Keeping Rica Updated

```bash
cd rica
git pull
pip install -r requirements.txt
# Restart the service
sudo systemctl restart rica
```
