# Rica - Dashboard API Main Entry Point (Local Mode)

import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# =============================================================================
# CENTRALIZED PATH SETUP
# =============================================================================
_api_path = os.path.abspath(os.path.dirname(__file__))
_bot_path = os.path.join(os.path.dirname(__file__), "..", "..", "bot")
_bot_path = os.path.abspath(_bot_path)
for path in (_api_path, _bot_path):
    if path not in sys.path:
        sys.path.insert(0, path)

app = FastAPI(
    title="Rica Dashboard API",
    description="Local dashboard API for Rica Discord Bot",
    version="1.0.0",
)

# CORS — localhost only for self-hosted mode
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Rica Dashboard API is running 🚀", "mode": "local"}


@app.get("/health")
async def health():
    return {"status": "ok", "mode": "local"}


# Import and register routes
from routes.auth import router as auth_router
from routes.servers import router as servers_router
from routes.keys import router as keys_router
from routes.data import router as data_router
from routes.stats import router as stats_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(servers_router, prefix="/api/v1/servers", tags=["Servers"])
app.include_router(keys_router, prefix="/api/v1/keys", tags=["API Keys"])
app.include_router(data_router, prefix="/api/v1/data", tags=["Data Browser"])
app.include_router(stats_router, prefix="/api/v1/stats", tags=["Stats"])
