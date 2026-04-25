# Dashboard

Rica includes a local dashboard with two parts:

- **Dashboard API**: FastAPI, usually on `http://localhost:8000`
- **Dashboard UI**: Next.js, usually on `http://localhost:3000`

Start both with:

```bash
rica start --with-frontend
```

## Dashboard areas

The current web app includes pages for:

- Server overview
- Initial setup
- Worker configuration
- Channel configuration
- API keys and model management
- Agent users
- Search settings
- Creative tools settings
- Data browser
- Usage stats
- Error logs

## API health check

```bash
curl http://localhost:8000/health
```

Expected:

```json
{"status":"ok","mode":"local"}
```

## API routes

Main route groups:

```text
/api/v1/auth
/api/v1/servers
/api/v1/keys
/api/v1/data
/api/v1/stats
```

## Security notes

- Keep the dashboard on localhost unless you put it behind HTTPS and access control.
- Do not expose `localhost:8000` or `localhost:3000` directly to the public internet on a VPS.
- API keys are sensitive. Prefer managing them through the dashboard or keep `~/.rica/config.yaml` readable only by your user.

## Development commands

```bash
# API
uvicorn dashboard.api.main:app --host 127.0.0.1 --port 8000

# Web UI
cd dashboard/web
npm run dev
npm run build
npm run start
```
