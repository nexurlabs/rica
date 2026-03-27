# Rica Deployment Guide (for Rose / VM Setup)

## What is Rica?
A BYOK (Bring Your Own Key) Discord AI bot with a web dashboard. Built with:
- **Bot**: Python + discord.py (4 AI workers: DB Manager, Moderator, Responder, Agent)
- **Dashboard API**: Python + FastAPI
- **Dashboard Frontend**: Next.js (React)
- **Storage**: Google Firestore (config) + Google Cloud Storage (data files)
- **Encryption**: Fernet with master key in GCP Secret Manager

## Project Structure
```
Rica/
├── bot/                    ← Discord bot (Python)
│   ├── main.py             ← Entry point
│   ├── config.py
│   ├── sessions.py
│   ├── prompts.py
│   ├── executor.py         ← Sandboxed code executor
│   ├── workers/            ← 4 AI workers
│   ├── providers/          ← 4 API provider adapters
│   ├── creative/           ← Imagen, Lyria, Veo
│   └── storage/            ← Firestore + GCS + encryption
├── dashboard/
│   ├── api/                ← FastAPI backend
│   │   ├── main.py
│   │   └── routes/         ← auth, servers, keys, data, stats
│   └── web/                ← Next.js frontend (13 pages)
└── .gitignore
```

---

## Step 1: Prerequisites (GCP APIs + Resources)

```bash
# Enable required GCP APIs
gcloud services enable firestore.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Create Firestore database in Native mode
gcloud firestore databases create --location=us-central1

# Create GCS bucket
gsutil mb -l us-central1 gs://Rica-data

# Generate and store encryption master key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" > /tmp/Rica_key.txt
gcloud secrets create Rica-master-key --data-file=/tmp/Rica_key.txt
rm /tmp/Rica_key.txt

# Create a service account (or use the VM's default SA)
# The service account needs these roles:
#   - Cloud Datastore User (for Firestore)
#   - Storage Object Admin (for GCS)
#   - Secret Manager Secret Accessor (for the master key)
```

---

## Step 2: Upload Project to VM

Copy the entire `Rica/` directory to the VM. The project has no Docker files — runs directly.

---

## Step 3: Install Dependencies

```bash
cd ~/Rica

# Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Bot deps
pip install -r bot/requirements.txt

# Dashboard API deps
pip install -r dashboard/api/requirements.txt

# Dashboard frontend deps
cd dashboard/web
npm install
npm run build
cd ../..
```

---

## Step 4: Configure Environment Files

### bot/.env
```env
DISCORD_BOT_TOKEN=<discord bot token>
GCP_PROJECT_ID=<gcp project id>
GCS_BUCKET_NAME=Rica-data
ENCRYPTION_KEY_SECRET_NAME=Rica-master-key
GOOGLE_APPLICATION_CREDENTIALS=<path to service account json, if not using default SA>
```

### dashboard/api/.env
```env
DISCORD_CLIENT_ID=<discord app client id>
DISCORD_CLIENT_SECRET=<discord app client secret>
DISCORD_REDIRECT_URI=http://<VM_PUBLIC_IP>:3000/auth/callback
GCP_PROJECT_ID=<gcp project id>
GCS_BUCKET_NAME=Rica-data
JWT_SECRET=<generate a random 32+ char string>
ENCRYPTION_KEY_SECRET_NAME=Rica-master-key
FRONTEND_URL=http://<VM_PUBLIC_IP>:3000
GOOGLE_APPLICATION_CREDENTIALS=<path to service account json, if not using default SA>
```

### dashboard/web/.env.local
```env
NEXT_PUBLIC_API_URL=http://<VM_PUBLIC_IP>:8000/api/v1
```

**Note**: Replace `<VM_PUBLIC_IP>` with the actual public IP of the VM.

---

## Step 5: Run All 3 Services

### Option A: Using tmux (quick)
```bash
# Start tmux
tmux new-session -d -s Rica

# Bot (window 0)
tmux send-keys -t Rica "cd ~/Rica && source venv/bin/activate && python -m bot.main" C-m

# Dashboard API (window 1)
tmux new-window -t Rica
tmux send-keys -t Rica "cd ~/Rica && source venv/bin/activate && uvicorn dashboard.api.main:app --host 0.0.0.0 --port 8000" C-m

# Dashboard Frontend (window 2)
tmux new-window -t Rica
tmux send-keys -t Rica "cd ~/Rica/dashboard/web && npm start -- -p 3000 -H 0.0.0.0" C-m

# Attach to see logs
tmux attach -t Rica
```

### Option B: Using systemd (production)

Create `/etc/systemd/system/Rica-bot.service`:
```ini
[Unit]
Description=Rica Discord Bot
After=network.target

[Service]
User=<your_user>
WorkingDirectory=/home/<your_user>/Rica
ExecStart=/home/<your_user>/Rica/venv/bin/python -m bot.main
Restart=always
RestartSec=5
EnvironmentFile=/home/<your_user>/Rica/bot/.env

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/Rica-api.service`:
```ini
[Unit]
Description=Rica Dashboard API
After=network.target

[Service]
User=<your_user>
WorkingDirectory=/home/<your_user>/Rica
ExecStart=/home/<your_user>/Rica/venv/bin/uvicorn dashboard.api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
EnvironmentFile=/home/<your_user>/Rica/dashboard/api/.env

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/Rica-web.service`:
```ini
[Unit]
Description=Rica Dashboard Frontend
After=network.target

[Service]
User=<your_user>
WorkingDirectory=/home/<your_user>/Rica/dashboard/web
ExecStart=/usr/bin/npm start -- -p 3000 -H 0.0.0.0
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now Rica-bot Rica-api Rica-web
```

---

## Step 6: Firewall Rules

Make sure these ports are open on the GCP VM firewall:
```bash
# Allow Dashboard API (port 8000) and Frontend (port 3000)
gcloud compute firewall-rules create Rica-dashboard \
  --allow tcp:3000,tcp:8000 \
  --target-tags=<vm-network-tag> \
  --description="Rica Dashboard"
```

---

## Step 7: Verify

1. Check bot is online: `sudo systemctl status Rica-bot`
2. Check API: `curl http://localhost:8000/health` → should return `{"status":"ok"}`
3. Check frontend: open `http://<VM_PUBLIC_IP>:3000` in browser
4. Discord: type `!status` in a server the bot has joined

---

## Discord App Configuration Required

The owner needs to create a Discord application at https://discord.com/developers/applications:
1. Create new application named "Rica"
2. **Bot tab**: Reset Token → copy (this is DISCORD_BOT_TOKEN)
3. **Bot tab**: Enable "Message Content Intent" + "Server Members Intent"
4. **OAuth2 tab**: Copy Client ID (DISCORD_CLIENT_ID) and Client Secret (DISCORD_CLIENT_SECRET)
5. **OAuth2 tab**: Add redirect URL: `http://<VM_PUBLIC_IP>:3000/auth/callback`
6. **OAuth2 URL Generator**: scope=bot+applications.commands, permissions=Send Messages+Manage Messages+Read Message History+Moderate Members → use generated URL to invite bot to server

---

## Ports Summary
| Service | Port | Purpose |
|---------|------|---------|
| Discord Bot | N/A | Connects to Discord via websocket |
| Dashboard API | 8000 | FastAPI backend |
| Dashboard Frontend | 3000 | Next.js web UI |
