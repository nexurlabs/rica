# Rica - Dashboard Auth Routes (Local Mode)
# Self-hosted: No Discord OAuth2 needed. Auto-authenticate on localhost.

import os
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request
from jose import jwt, JWTError
from pydantic import BaseModel

router = APIRouter()

# Local-only JWT secret — auto-generated if not provided
JWT_SECRET = os.getenv("JWT_SECRET", "")
if not JWT_SECRET:
    JWT_SECRET = "rica-local-" + secrets.token_urlsafe(32)

# =========================================================================
# HELPERS
# =========================================================================

def create_jwt(user_data: dict) -> str:
    """Create a JWT token for dashboard session."""
    payload = {
        "sub": user_data.get("id", "local_owner"),
        "username": user_data.get("username", "Owner"),
        "exp": datetime.utcnow() + timedelta(days=30),  # Long-lived for local use
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verify_jwt(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def get_current_user(request: Request) -> dict:
    """Extract user from Authorization header.
    In local mode, auto-authenticate if no token provided.
    """
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        # Local mode: auto-authenticate as owner
        return {"sub": "local_owner", "username": "Owner"}
    return verify_jwt(auth.split(" ")[1])


# =========================================================================
# ROUTES
# =========================================================================

@router.get("/login")
async def login():
    """In local mode, auto-login and return a token directly."""
    user_data = {"id": "local_owner", "username": "Owner"}
    token = create_jwt(user_data)
    return {
        "access_token": token,
        "user": {
            "id": "local_owner",
            "username": "Owner",
            "avatar": None,
            "guilds": [],  # Will be populated from bot connection
        },
        "local_mode": True,
    }


@router.get("/me")
async def get_me(request: Request):
    """Get current user info."""
    user = await get_current_user(request)
    return user


class TokenResponse(BaseModel):
    access_token: str
    user: dict


@router.post("/callback")
async def callback(code: str = ""):
    """In local mode, callback just returns auto-login."""
    return await login()
