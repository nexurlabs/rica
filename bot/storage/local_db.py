# Rica - Local Database Client (SQLite)
# Drop-in replacement for firestore_client — same interface, local SQLite backend

import os
import json
import time
import sqlite3
from pathlib import Path
from datetime import datetime
from storage.encryption import encryption


RICA_HOME = Path(os.environ.get("RICA_HOME", Path.home() / ".rica"))
DB_PATH = RICA_HOME / "rica.db"


class LocalDB:
    """SQLite-backed storage replacing Firestore. Same interface as FirestoreClient."""

    def __init__(self):
        self._conn = None
        self._cache = {}
        self._cache_ttl_seconds = 10

    @property
    def conn(self):
        if self._conn is None:
            RICA_HOME.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._init_tables()
        return self._conn

    # Alias for dashboard API compatibility (replaces firestore_client.db references)
    @property
    def db(self):
        return self

    def _init_tables(self):
        """Create tables if they don't exist."""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS channels (
                server_id TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                config TEXT NOT NULL DEFAULT '{}',
                PRIMARY KEY (server_id, channel_id)
            );

            CREATE TABLE IF NOT EXISTS usage (
                server_id TEXT NOT NULL,
                worker TEXT NOT NULL,
                tokens INTEGER DEFAULT 0,
                calls INTEGER DEFAULT 0,
                last_updated TEXT,
                PRIMARY KEY (server_id, worker)
            );

            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id TEXT NOT NULL,
                worker TEXT NOT NULL,
                error TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                key TEXT PRIMARY KEY,
                data TEXT NOT NULL
            );
        """)
        self._conn.commit()

    def _get_config_data(self) -> dict:
        """Load the full config dict from the config table."""
        row = self.conn.execute(
            "SELECT value FROM config WHERE key = 'server_config'"
        ).fetchone()
        if row:
            return json.loads(row["value"])
        return None

    def _save_config_data(self, data: dict):
        """Save the full config dict to the config table."""
        self.conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            ("server_config", json.dumps(data))
        )
        self.conn.commit()
        # Invalidate cache
        self._cache = {}

    # =========================================================================
    # SERVER CONFIG
    # =========================================================================

    def get_server_config(self, server_id: str = None) -> dict:
        """Get full server config (cached with short TTL).
        server_id is accepted for API compatibility but ignored (single-instance).
        """
        now = time.time()
        cached = self._cache.get("config")
        if cached and (now - cached.get("ts", 0) < self._cache_ttl_seconds):
            return cached.get("data")

        config = self._get_config_data()
        if config:
            self._cache["config"] = {"data": config, "ts": now}
        return config

    def create_server_config(self, server_id: str = None, owner_id: str = "",
                             server_name: str = "Local") -> dict:
        """Create default server config on first setup."""
        config = {
            "server_id": server_id or "local",
            "server_name": server_name,
            "owner_id": owner_id,
            "trigger_word": "Rica",
            "created_at": datetime.utcnow().isoformat(),

            "workers": {
                "db_manager": {"enabled": False, "api_key": ""},
                "moderator": {"enabled": False, "api_key": ""},
                "responder": {"enabled": True, "api_key": ""},
                "agent": {"enabled": False, "api_key": ""},
            },

            "api_keys": {
                "global_key": "",
                "provider": "google_ai",
            },

            "search_config": {
                "enabled": False,
                "serper_api_key": "",
            },

            "creative_config": {
                "imagen": {"enabled": False, "api_key": ""},
                "lyria": {"enabled": False, "api_key": ""},
                "veo": {"enabled": False, "api_key": ""},
            },

            "prompts": {
                "db_manager": "",
                "moderator": "",
                "responder": "",
                "agent": "",
            },

            "agent_users": [owner_id] if owner_id else [],
            "setup_complete": False,
        }

        self._save_config_data(config)
        return config

    def update_server_config(self, server_id: str, updates: dict):
        """Update specific fields in server config.
        Supports dotted keys like 'api_keys.provider' for nested updates.
        """
        config = self._get_config_data()
        if not config:
            config = self.create_server_config(server_id)

        for key, value in updates.items():
            parts = key.split(".")
            target = config
            for part in parts[:-1]:
                if part not in target:
                    target[part] = {}
                target = target[part]
            target[parts[-1]] = value

        self._save_config_data(config)

    def invalidate_cache(self, server_id: str = None):
        """Force cache refresh."""
        self._cache = {}

    # =========================================================================
    # API KEYS (encrypted)
    # =========================================================================

    def save_api_key(self, server_id: str, key_name: str, plaintext_key: str):
        """Encrypt and save an API key."""
        encrypted = encryption.encrypt(plaintext_key)
        if key_name in ["db_manager", "moderator", "responder", "agent"]:
            self.update_server_config(server_id, {f"workers.{key_name}.api_key": encrypted})
        else:
            self.update_server_config(server_id, {f"api_keys.{key_name}": encrypted})

    def get_global_api_key(self, server_id: str = None) -> str:
        """Get and decrypt the global API key."""
        config = self.get_server_config(server_id)
        if not config:
            return ""
        global_key = config.get("api_keys", {}).get("global_key", "")
        if not global_key:
            return ""
        return encryption.decrypt(global_key)

    def get_worker_config(self, server_id: str, worker_name: str,
                          channel_id: str = None) -> dict:
        """Get the full config for a specific worker (merging channel -> worker -> global)."""
        config = self.get_server_config(server_id)
        if not config:
            return {"api_key": "", "provider": "google_ai", "model": "", "prompt": ""}

        result = {
            "api_key": "",
            "provider": config.get("api_keys", {}).get("provider", "google_ai"),
            "model": config.get("api_keys", {}).get("model", ""),
            "prompt": config.get("prompts", {}).get(worker_name, ""),
        }

        # 1. Global config
        global_key = config.get("api_keys", {}).get("global_key", "")
        if global_key:
            result["api_key"] = encryption.decrypt(global_key)

        # 2. Worker config
        worker_config = config.get("workers", {}).get(worker_name, {})
        if worker_config.get("api_key"):
            result["api_key"] = encryption.decrypt(worker_config["api_key"])
        if worker_config.get("provider"):
            result["provider"] = worker_config["provider"]
        if worker_config.get("model"):
            result["model"] = worker_config["model"]

        # 3. Channel override
        if channel_id and worker_name != "agent":
            ch_config = self.get_channel_config(server_id, str(channel_id))
            if ch_config and "workers" in ch_config:
                ch_worker = ch_config["workers"].get(worker_name)
                if ch_worker is not None:
                    if ch_worker.get("api_key"):
                        result["api_key"] = encryption.decrypt(ch_worker["api_key"])
                    if ch_worker.get("provider"):
                        result["provider"] = ch_worker["provider"]
                    if ch_worker.get("model"):
                        result["model"] = ch_worker["model"]
                    if ch_worker.get("prompt"):
                        result["prompt"] = ch_worker["prompt"]

        return result

    def get_api_provider(self, server_id: str = None) -> str:
        """Get the configured API provider."""
        config = self.get_server_config(server_id)
        if not config:
            return "google_ai"
        return config.get("api_keys", {}).get("provider", "google_ai")

    # =========================================================================
    # CHANNEL CONFIG
    # =========================================================================

    def get_channel_config(self, server_id: str, channel_id: str) -> dict:
        """Get per-channel config overrides."""
        row = self.conn.execute(
            "SELECT config FROM channels WHERE server_id = ? AND channel_id = ?",
            (server_id, channel_id)
        ).fetchone()
        if row:
            return json.loads(row["config"])
        return None

    def set_channel_config(self, server_id: str, channel_id: str, config: dict):
        """Set per-channel config overrides."""
        existing = self.get_channel_config(server_id, channel_id)
        if existing:
            existing.update(config)
            config = existing

        self.conn.execute(
            "INSERT OR REPLACE INTO channels (server_id, channel_id, config) VALUES (?, ?, ?)",
            (server_id, channel_id, json.dumps(config))
        )
        self.conn.commit()

    # =========================================================================
    # SEARCH CONFIG
    # =========================================================================

    def get_search_config(self, server_id: str = None) -> dict:
        """Get search configuration."""
        config = self.get_server_config(server_id)
        if not config:
            return {"enabled": False, "serper_api_key": ""}

        search = config.get("search_config", {})
        if search.get("serper_api_key"):
            search["serper_api_key"] = encryption.decrypt(search["serper_api_key"])
        return search

    # =========================================================================
    # CREATIVE CONFIG
    # =========================================================================

    def get_creative_config(self, server_id: str = None) -> dict:
        """Get creative tools configuration."""
        config = self.get_server_config(server_id)
        if not config:
            return {}

        creative = config.get("creative_config", {})
        for tool in ["imagen", "lyria", "veo"]:
            if tool in creative and creative[tool].get("api_key"):
                creative[tool]["api_key"] = encryption.decrypt(creative[tool]["api_key"])
        return creative

    # =========================================================================
    # USAGE STATS
    # =========================================================================

    def increment_usage(self, server_id: str, worker_name: str, tokens: int):
        """Increment token usage for a worker."""
        self.conn.execute("""
            INSERT INTO usage (server_id, worker, tokens, calls, last_updated)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT (server_id, worker) DO UPDATE SET
                tokens = tokens + ?,
                calls = calls + 1,
                last_updated = ?
        """, (server_id, worker_name, tokens, datetime.utcnow().isoformat(),
              tokens, datetime.utcnow().isoformat()))
        self.conn.commit()

    def get_usage_stats(self, server_id: str) -> dict:
        """Get usage statistics."""
        rows = self.conn.execute(
            "SELECT worker, tokens, calls, last_updated FROM usage WHERE server_id = ?",
            (server_id,)
        ).fetchall()

        if not rows:
            return {}

        result = {}
        for row in rows:
            result[f"{row['worker']}_tokens"] = row["tokens"]
            result[f"{row['worker']}_calls"] = row["calls"]
            result["last_updated"] = row["last_updated"]
        return result

    # =========================================================================
    # ERROR LOGS
    # =========================================================================

    def log_error(self, server_id: str, worker_name: str, error_msg: str):
        """Log an error."""
        self.conn.execute(
            "INSERT INTO errors (server_id, worker, error, timestamp) VALUES (?, ?, ?, ?)",
            (server_id, worker_name, error_msg[:500], datetime.utcnow().isoformat())
        )
        self.conn.commit()

    def get_error_logs(self, server_id: str, limit: int = 50) -> list:
        """Get recent error logs."""
        rows = self.conn.execute(
            "SELECT worker, error, timestamp FROM errors WHERE server_id = ? ORDER BY timestamp DESC LIMIT ?",
            (server_id, limit)
        ).fetchall()
        return [{"worker": r["worker"], "error": r["error"], "timestamp": r["timestamp"]} for r in rows]

    # =========================================================================
    # AGENT USERS
    # =========================================================================

    def is_agent_user(self, server_id: str, user_id: str) -> bool:
        """Check if a user is in the agent users list."""
        config = self.get_server_config(server_id)
        if not config:
            return False
        return user_id in config.get("agent_users", [])

    # =========================================================================
    # PROMPTS
    # =========================================================================

    def get_prompt(self, server_id: str, worker_name: str) -> str:
        """Get the system prompt for a worker."""
        config = self.get_server_config(server_id)
        if not config:
            return ""
        return config.get("prompts", {}).get(worker_name, "")

    # =========================================================================
    # SESSION PERSISTENCE (replaces Firestore system/sessions doc)
    # =========================================================================

    def save_sessions(self, data: dict):
        """Save session data for crash recovery."""
        self.conn.execute(
            "INSERT OR REPLACE INTO sessions (key, data) VALUES (?, ?)",
            ("active_sessions", json.dumps(data))
        )
        self.conn.commit()

    def load_sessions(self) -> dict:
        """Load persisted session data."""
        row = self.conn.execute(
            "SELECT data FROM sessions WHERE key = 'active_sessions'"
        ).fetchone()
        if row:
            return json.loads(row["data"])
        return {}


# Global instance — drop-in replacement for firestore_client
firestore_client = LocalDB()
