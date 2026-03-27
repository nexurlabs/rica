# Rica - Bot Configuration
# Loads config from ~/.rica/config.yaml (local self-hosted mode)

import os
from pathlib import Path

# Try loading from dotenv for backward compatibility
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# =========================================================================
# RICA HOME DIRECTORY
# =========================================================================
RICA_HOME = Path(os.environ.get("RICA_HOME", Path.home() / ".rica"))
CONFIG_PATH = RICA_HOME / "config.yaml"

# =========================================================================
# LOAD CONFIG
# =========================================================================
_config = {}

if CONFIG_PATH.exists():
    import yaml
    with open(CONFIG_PATH) as f:
        _config = yaml.safe_load(f) or {}

# =========================================================================
# DISCORD
# =========================================================================
DISCORD_BOT_TOKEN = (
    os.getenv("DISCORD_BOT_TOKEN")
    or _config.get("discord", {}).get("token", "")
)

# =========================================================================
# AI PROVIDER (from config.yaml)
# =========================================================================
DEFAULT_PROVIDER = _config.get("provider", {}).get("name", "google_ai")
DEFAULT_API_KEY = _config.get("provider", {}).get("api_key", "")

# =========================================================================
# DEFAULTS
# =========================================================================
DEFAULT_TRIGGER_WORD = _config.get("trigger_word", "Rica")

# Session timeouts (minutes)
RESPONDER_SESSION_TIMEOUT = 30
AGENT_SESSION_TIMEOUT = 30
MODERATOR_SESSION_TIMEOUT = 10
DB_MANAGER_SESSION_TIMEOUT = 10

# Context limits
SESSION_CONTEXT_WORDS = 1000
