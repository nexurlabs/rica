# Rica - Dashboard Server Config Routes

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional

# Imports from bot/ — path setup is centralized in dashboard/api/main.py
from storage.firestore_client import firestore_client
from storage.gcs_client import gcs_client
from routes.auth import get_current_user
from prompts import DEFAULT_PERSONAS

router = APIRouter()


# =========================================================================
# MODELS
# =========================================================================

class WorkerConfig(BaseModel):
    enabled: bool
    api_key: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    prompt: Optional[str] = None


class UpdateWorkersRequest(BaseModel):
    db_manager: Optional[WorkerConfig] = None
    moderator: Optional[WorkerConfig] = None
    responder: Optional[WorkerConfig] = None
    agent: Optional[WorkerConfig] = None


class UpdatePromptsRequest(BaseModel):
    db_manager: Optional[str] = None
    moderator: Optional[str] = None
    responder: Optional[str] = None
    agent: Optional[str] = None


class UpdateConfigRequest(BaseModel):
    trigger_word: Optional[str] = None
    bot_name: Optional[str] = None


class AgentUsersRequest(BaseModel):
    user_ids: list[str]  # Max 5


class SearchConfigRequest(BaseModel):
    enabled: bool
    serper_api_key: Optional[str] = None


class CreativeToolConfig(BaseModel):
    enabled: bool
    api_key: Optional[str] = None


class CreativeConfigRequest(BaseModel):
    imagen: Optional[CreativeToolConfig] = None
    lyria: Optional[CreativeToolConfig] = None
    veo: Optional[CreativeToolConfig] = None


class ChannelConfigRequest(BaseModel):
    workers: Optional[UpdateWorkersRequest] = None
    api_keys: Optional[dict] = None
    prompts: Optional[UpdatePromptsRequest] = None
    search_config: Optional[SearchConfigRequest] = None
    creative_config: Optional[CreativeConfigRequest] = None


class SetupWizardRequest(BaseModel):
    trigger_word: str
    provider: str  # google_ai, openrouter, openai, anthropic, groq
    all_key: Optional[str] = None
    model: Optional[str] = None
    db_manager_enabled: bool = True
    moderator_enabled: bool = True
    responder_enabled: bool = True
    agent_enabled: bool = False


# =========================================================================
# ROUTES
# =========================================================================

@router.get("/")
async def list_servers(request: Request):
    """List all servers the authenticated user owns."""
    user = await get_current_user(request)
    user_id = user["sub"]

    # Get all servers where this user is the owner
    servers = firestore_client.db.collection("servers").where(
        "owner_id", "==", user_id
    ).stream()

    result = []
    for doc in servers:
        data = doc.to_dict()
        result.append({
            "server_id": data["server_id"],
            "server_name": data.get("server_name", "Unknown"),
            "setup_complete": data.get("setup_complete", False),
            "trigger_word": data.get("trigger_word", "Rica"),
            "workers": data.get("workers", {}),
        })

    # Also check if user is an agent_user in any server
    all_servers = firestore_client.db.collection("servers").stream()
    for doc in all_servers:
        data = doc.to_dict()
        if user_id in data.get("agent_users", []) and data["server_id"] not in [s["server_id"] for s in result]:
            result.append({
                "server_id": data["server_id"],
                "server_name": data.get("server_name", "Unknown"),
                "setup_complete": data.get("setup_complete", False),
                "trigger_word": data.get("trigger_word", "Rica"),
                "workers": data.get("workers", {}),
                "role": "agent_user",
            })

    return {"servers": result}


@router.get("/{server_id}")
async def get_server(server_id: str, request: Request):
    """Get full server config."""
    user = await get_current_user(request)
    config = _check_access(server_id, user["sub"])

    # Remove encrypted keys from response
    safe_config = {k: v for k, v in config.items() if k != "api_keys"}
    
    # Strip worker API keys
    for w in safe_config.get("workers", {}).values():
        w.pop("api_key", None)
        
    global_key = config.get("api_keys", {}).get("global_key", "")
    safe_config["api_keys_configured"] = {"global_key": bool(global_key)}
    safe_config["api_keys_configured"]["provider"] = config.get("api_keys", {}).get("provider", "google_ai")

    return safe_config


@router.post("/{server_id}/setup")
async def setup_wizard(server_id: str, setup: SetupWizardRequest, request: Request):
    """Complete first-time setup wizard."""
    user = await get_current_user(request)
    config = _check_access(server_id, user["sub"])

    from storage.encryption import encryption

    updates = {
        "trigger_word": setup.trigger_word,
        "setup_complete": True,
        "workers.db_manager.enabled": setup.db_manager_enabled,
        "workers.moderator.enabled": setup.moderator_enabled,
        "workers.responder.enabled": setup.responder_enabled,
        "workers.agent.enabled": setup.agent_enabled,
        "api_keys.provider": setup.provider,
        "prompts": DEFAULT_PERSONAS,
    }

    if setup.all_key:
        updates["api_keys.global_key"] = encryption.encrypt(setup.all_key)
    if setup.model is not None:
        updates["api_keys.model"] = setup.model

    firestore_client.update_server_config(server_id, updates)
    gcs_client.init_server_storage(server_id)

    _trigger_restart()

    return {"message": "Setup complete! Bot is restarting.", "server_id": server_id}


@router.patch("/{server_id}/config")
async def update_config(server_id: str, config_update: UpdateConfigRequest, request: Request):
    """Update basic server config (trigger word, bot name)."""
    user = await get_current_user(request)
    _check_access(server_id, user["sub"])

    updates = {}
    if config_update.trigger_word:
        updates["trigger_word"] = config_update.trigger_word
    if config_update.bot_name:
        updates["bot_name"] = config_update.bot_name

    if updates:
        firestore_client.update_server_config(server_id, updates)
    return {"message": "Config updated"}


@router.patch("/{server_id}/workers")
async def update_workers(server_id: str, workers: UpdateWorkersRequest, request: Request):
    """Enable/disable workers."""
    user = await get_current_user(request)
    _check_access(server_id, user["sub"])

    updates = {}
    for worker_name in ["db_manager", "moderator", "responder", "agent"]:
        worker_conf = getattr(workers, worker_name, None)
        if worker_conf is not None:
            updates[f"workers.{worker_name}.enabled"] = worker_conf.enabled

    if updates:
        firestore_client.update_server_config(server_id, updates)
    return {"message": "Workers updated"}


@router.patch("/{server_id}/prompts")
async def update_prompts(server_id: str, prompts: UpdatePromptsRequest, request: Request):
    """Update worker system prompts."""
    user = await get_current_user(request)
    _check_access(server_id, user["sub"])

    updates = {}
    for worker_name in ["db_manager", "moderator", "responder", "agent"]:
        prompt = getattr(prompts, worker_name, None)
        if prompt is not None:
            updates[f"prompts.{worker_name}"] = prompt

    if updates:
        firestore_client.update_server_config(server_id, updates)
    return {"message": "Prompts updated"}


@router.get("/{server_id}/prompts/defaults")
async def get_default_prompts():
    """Get default prompts for reference."""
    return DEFAULT_PERSONAS


@router.put("/{server_id}/agent-users")
async def update_agent_users(server_id: str, agents: AgentUsersRequest, request: Request):
    """Update agent user IDs (max 5 including owner)."""
    user = await get_current_user(request)
    config = _check_access(server_id, user["sub"])

    if len(agents.user_ids) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 agent users allowed")

    # Ensure owner is always included
    owner_id = config.get("owner_id")
    if owner_id and owner_id not in agents.user_ids:
        agents.user_ids.insert(0, owner_id)

    firestore_client.update_server_config(server_id, {"agent_users": agents.user_ids[:5]})
    return {"message": "Agent users updated", "agent_users": agents.user_ids[:5]}


@router.patch("/{server_id}/search")
async def update_search_config(server_id: str, search: SearchConfigRequest, request: Request):
    """Update search configuration."""
    user = await get_current_user(request)
    _check_access(server_id, user["sub"])

    from storage.encryption import encryption

    updates = {"search_config.enabled": search.enabled}
    if search.serper_api_key:
        updates["search_config.serper_api_key"] = encryption.encrypt(search.serper_api_key)

    firestore_client.update_server_config(server_id, updates)
    return {"message": "Search config updated"}


@router.patch("/{server_id}/creative")
async def update_creative_config(server_id: str, creative: CreativeConfigRequest, request: Request):
    """Update creative tools configuration."""
    user = await get_current_user(request)
    _check_access(server_id, user["sub"])

    from storage.encryption import encryption

    updates = {}
    for tool_name in ["imagen", "lyria", "veo"]:
        tool_conf = getattr(creative, tool_name, None)
        if tool_conf is not None:
            updates[f"creative_config.{tool_name}.enabled"] = tool_conf.enabled
            if tool_conf.api_key:
                updates[f"creative_config.{tool_name}.api_key"] = encryption.encrypt(tool_conf.api_key)

    if updates:
        firestore_client.update_server_config(server_id, updates)
    return {"message": "Creative config updated"}


# =========================================================================
# CHANNEL CONFIG
# =========================================================================

@router.get("/{server_id}/channels/{channel_id}")
async def get_channel_config(server_id: str, channel_id: str, request: Request):
    """Get per-channel config overrides."""
    user = await get_current_user(request)
    _check_access(server_id, user["sub"])

    config = firestore_client.get_channel_config(server_id, channel_id)
    return config or {}


@router.put("/{server_id}/channels/{channel_id}")
async def set_channel_config(server_id: str, channel_id: str,
                              config: ChannelConfigRequest, request: Request):
    """Set per-channel config overrides."""
    user = await get_current_user(request)
    _check_access(server_id, user["sub"])

    firestore_client.set_channel_config(server_id, channel_id, config.model_dump(exclude_none=True))
    firestore_client.invalidate_cache(server_id)
    return {"message": f"Channel {channel_id} config updated"}


# =========================================================================
# HELPERS
# =========================================================================

def _check_access(server_id: str, user_id: str | None = None) -> dict:
    """Get server config. In local mode, always grants access (you own the instance)."""
    config = firestore_client.get_server_config(server_id)
    if not config:
        # Auto-create config for this server
        config = firestore_client.create_server_config(server_id)
    return config

def _trigger_restart():
    """Restarts the Rica bot process to apply configuration changes."""
    import subprocess
    import sys
    import os
    # Detached python process that waits 1s, stops the daemon, and starts it again
    cmd = f'{sys.executable} -c "import time, os; time.sleep(1); os.system(\'{sys.executable} -m cli.main stop\'); os.system(\'{sys.executable} -m cli.main start -d\')"'
    subprocess.Popen(cmd, shell=True, start_new_session=True if os.name != 'nt' else False)
