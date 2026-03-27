# Rica - Dashboard API Key Routes

import re
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Tuple

# Imports from bot/ — path setup is centralized in dashboard/api/main.py
from storage.firestore_client import firestore_client
from storage.encryption import encryption
from routes.auth import get_current_user

router = APIRouter()


class SetKeyRequest(BaseModel):
    key_name: str    # global_key, db_manager, moderator, responder, agent
    api_key: Optional[str] = ""     # Plaintext key
    provider: Optional[str] = None  # google_ai, openrouter, openai, anthropic
    model: Optional[str] = None     # Specific model override


class ValidateKeyRequest(BaseModel):
    api_key: str
    provider: str


class SetProviderRequest(BaseModel):
    provider: str


class GetModelsRequest(BaseModel):
    api_key: str
    provider: str


# =========================================================================
# ROUTES
# =========================================================================

@router.get("/{server_id}")
async def list_keys(server_id: str, request: Request):
    """List configured keys (shows which are set, never the actual key)."""
    # Local mode: no access checks needed
    config = firestore_client.get_server_config(server_id)
    if not config:
        config = firestore_client.create_server_config(server_id)

    keys = config.get("api_keys", {})
    workers = config.get("workers", {})
    result = {
        "provider": keys.get("provider", "google_ai"),
        "keys": {
            "global_key": {
                "configured": bool(keys.get("global_key", "")),
                "masked": _mask_key(keys.get("global_key", "")),
                "provider": keys.get("provider", "google_ai"),
                "model": keys.get("model", ""),
            }
        }
    }

    for key_name in ["db_manager", "moderator", "responder", "agent"]:
        w_key = workers.get(key_name, {}).get("api_key", "")
        result["keys"][key_name] = {
            "configured": bool(w_key),
            "masked": _mask_key(w_key),
            "provider": workers.get(key_name, {}).get("provider", ""),
            "model": workers.get(key_name, {}).get("model", ""),
        }

    # Search key
    search = config.get("search_config", {})
    result["search"] = {
        "enabled": search.get("enabled", False),
        "configured": bool(search.get("serper_api_key", "")),
    }

    # Creative keys
    creative = config.get("creative_config", {})
    result["creative"] = {}
    for tool in ["imagen", "lyria", "veo"]:
        tool_conf = creative.get(tool, {})
        result["creative"][tool] = {
            "enabled": tool_conf.get("enabled", False),
            "configured": bool(tool_conf.get("api_key", "")),
        }

    return result


@router.post("/{server_id}/set")
async def set_key(server_id: str, req: SetKeyRequest, request: Request):
    """Set an API key config (encrypts and validates key if provided)."""
    # Local mode: no owner check needed
    config = firestore_client.get_server_config(server_id)
    if not config:
        config = firestore_client.create_server_config(server_id)

    provider = req.provider or config.get("api_keys", {}).get("provider", "google_ai")

    # Validate and save key if provided
    if req.api_key:
        is_valid, reason = await _validate_key(req.api_key, provider)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid API key for provider '{provider}': {reason}")
        
        # Encrypt and save
        firestore_client.save_api_key(server_id, req.key_name, req.api_key)

    # Update provider and model if specified
    updates = {}
    if req.provider:
        if req.key_name == "global_key":
            updates["api_keys.provider"] = req.provider
        elif req.key_name in ["db_manager", "moderator", "responder", "agent"]:
            updates[f"workers.{req.key_name}.provider"] = req.provider
            
    if req.model:
        if req.key_name == "global_key":
            updates["api_keys.model"] = req.model
        elif req.key_name in ["db_manager", "moderator", "responder", "agent"]:
            updates[f"workers.{req.key_name}.model"] = req.model
            
    if updates:
        firestore_client.update_server_config(server_id, updates)

    return {"message": f"Key '{req.key_name}' saved successfully ✅", "provider": provider}


@router.post("/validate")
async def validate_key(req: ValidateKeyRequest):
    """Validate an API key without saving it."""
    is_valid, reason = await _validate_key(req.api_key, req.provider)
    return {"valid": is_valid, "provider": req.provider, "message": reason}
    

@router.post("/models")
async def get_provider_models(req: GetModelsRequest):
    """Fetch available models for a given provider and API key."""
    from providers.factory import get_provider
    try:
        provider = get_provider(req.provider, req.api_key)
        models = await provider.get_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{server_id}/models/{key_name}")
async def get_saved_key_models(server_id: str, key_name: str, request: Request):
    """Fetch available models for an already configured key."""
    config = firestore_client.get_server_config(server_id)
    if not config:
        config = firestore_client.create_server_config(server_id)

    if key_name == "global_key":
        api_key = firestore_client.get_global_api_key(server_id)
        provider = config.get("api_keys", {}).get("provider", "google_ai")
    elif key_name in ["db_manager", "moderator", "responder", "agent"]:
        w_conf = firestore_client.get_worker_config(server_id, key_name)
        api_key = w_conf["api_key"]
        provider = w_conf["provider"]
    else:
        raise HTTPException(status_code=400, detail="Unknown key name")

    if not api_key:
        raise HTTPException(status_code=400, detail=f"{key_name} is not configured yet")

    from providers.factory import get_provider
    try:
        provider_inst = get_provider(provider, api_key)
        models = await provider_inst.get_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{server_id}/provider")
async def set_provider(server_id: str, req: SetProviderRequest, request: Request):
    """Set active provider without changing keys."""
    config = firestore_client.get_server_config(server_id)
    if not config:
        config = firestore_client.create_server_config(server_id)

    if req.provider not in ["google_ai", "openrouter", "openai", "anthropic", "groq"]:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    firestore_client.update_server_config(server_id, {"api_keys.provider": req.provider})
    return {"message": "Provider updated", "provider": req.provider}


@router.delete("/{server_id}/{key_name}")
async def delete_key(server_id: str, key_name: str, request: Request):
    """Remove an API key."""
    config = firestore_client.get_server_config(server_id)
    if not config:
        config = firestore_client.create_server_config(server_id)

    if key_name in ["db_manager", "moderator", "responder", "agent"]:
        firestore_client.update_server_config(server_id, {f"workers.{key_name}.api_key": ""})
    else:
        firestore_client.update_server_config(server_id, {f"api_keys.{key_name}": ""})
    return {"message": f"Key '{key_name}' removed"}


# =========================================================================
# HELPERS
# =========================================================================

def _mask_key(encrypted_key: str) -> str:
    """Mask an encrypted key for display (show last 4 chars of decrypted)."""
    if not encrypted_key:
        return ""
    try:
        decrypted = encryption.decrypt(encrypted_key)
        if len(decrypted) > 4:
            return "•" * 8 + decrypted[-4:]
        return "•" * 8
    except Exception:
        return "•" * 8


def _precheck_key_format(api_key: str, provider: str) -> Tuple[bool, str]:
    """Format-check an API key. Ordered most-specific-prefix first to avoid
    ambiguous matches (e.g. 'sk-ant-' must be checked before 'sk-')."""
    k = (api_key or "").strip()
    if not k:
        return False, "Key is empty"
    if len(k) < 16:
        return False, "Key looks too short"
    if re.search(r"\s", k):
        return False, "Key contains whitespace"

    # Ordered most-specific first to prevent false positives
    _PREFIX_MAP = [
        ("anthropic",  "sk-ant-"),
        ("openrouter", "sk-or-"),
        ("groq",       "gsk_"),
        ("google_ai",  "AIza"),
        ("openai",     "sk-"),
    ]

    # Cross-provider mismatch detection
    for prov_name, prefix in _PREFIX_MAP:
        if k.startswith(prefix) and prov_name != provider:
            return False, (
                f"This key looks like a {prov_name} key (starts with '{prefix}'), "
                f"but you selected '{provider}'."
            )

    # Expected prefix check
    expected = dict(_PREFIX_MAP).get(provider, "")
    if expected and not k.startswith(expected):
        return False, f"{provider} keys should start with '{expected}'"

    return True, "Format check passed"


async def _validate_key(api_key: str, provider: str) -> Tuple[bool, str]:
    """Validate a key by format precheck + provider API call."""
    ok, msg = _precheck_key_format(api_key, provider)
    if not ok:
        return False, msg

    from providers.factory import validate_provider_key
    try:
        valid = await validate_provider_key(provider, api_key.strip())
        if valid:
            return True, "Key validated successfully"
        return False, "Provider authentication failed (wrong key, revoked key, quota/billing, or provider-side issue)"
    except ValueError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Validation error: {e}"
