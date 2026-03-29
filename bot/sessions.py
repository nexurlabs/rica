# Rica - Session Manager
# Per-channel sessions for Responder/Moderator/DB Manager, global session for Agent

from datetime import datetime, timedelta, timezone
from config import (
    RESPONDER_SESSION_TIMEOUT,
    AGENT_SESSION_TIMEOUT,
    MODERATOR_SESSION_TIMEOUT,
    DB_MANAGER_SESSION_TIMEOUT,
    SESSION_CONTEXT_WORDS,
)


# Session timeout mapping per worker type
TIMEOUTS = {
    "responder": RESPONDER_SESSION_TIMEOUT,
    "agent": AGENT_SESSION_TIMEOUT,
    "moderator": MODERATOR_SESSION_TIMEOUT,
    "db_manager": DB_MANAGER_SESSION_TIMEOUT,
}

# Workers that get history context on new session
CONTEXT_WORKERS = {"responder", "agent"}


def _to_utc(dt: datetime) -> datetime:
    """Normalize naive/legacy datetimes to UTC-aware ones."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class Session:
    """A single chat session with history."""

    def __init__(self, worker_type: str, channel_id: str = None):
        self.worker_type = worker_type
        self.channel_id = channel_id
        self.history = []  # List of {"role": "user"/"assistant", "content": "..."}
        self.last_used = datetime.now(timezone.utc)
        self.created_at = datetime.now(timezone.utc)

    def is_expired(self) -> bool:
        timeout = TIMEOUTS.get(self.worker_type, 30)
        return datetime.now(timezone.utc) - _to_utc(self.last_used) > timedelta(minutes=timeout)

    def touch(self):
        self.last_used = datetime.now(timezone.utc)

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        self.touch()

    def get_history(self) -> list:
        return self.history

    def to_dict(self) -> dict:
        """Serialize session for persistence."""
        return {
            "worker_type": self.worker_type,
            "channel_id": self.channel_id,
            "history": self.history,
            "last_used": self.last_used.isoformat(),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Deserialize session from persistence."""
        session = cls(data["worker_type"], data.get("channel_id"))
        session.history = data.get("history", [])
        session.last_used = _to_utc(datetime.fromisoformat(data["last_used"]))
        session.created_at = _to_utc(datetime.fromisoformat(data["created_at"]))
        return session


class SessionManager:
    """
    Manage sessions for all workers across all servers.

    Structure:
    - Responder: per-server, per-channel  → sessions[server_id]["responder"][channel_id]
    - Moderator: per-server, per-channel  → sessions[server_id]["moderator"][channel_id]
    - DB Manager: per-server, per-channel → sessions[server_id]["db_manager"][channel_id]
    - Agent: per-server, ONE global       → sessions[server_id]["agent"]["global"]
    """

    def __init__(self):
        # {server_id: {worker_type: {channel_id_or_global: Session}}}
        self.sessions = {}

    def _ensure_server(self, server_id: str):
        if server_id not in self.sessions:
            self.sessions[server_id] = {
                "responder": {},
                "moderator": {},
                "db_manager": {},
                "agent": {},
            }

    def get_or_create(self, server_id: str, worker_type: str, channel_id: str) -> tuple:
        """
        Get existing session or create new one.

        Returns: (session: Session, is_new: bool)
        """
        self._ensure_server(server_id)

        # Agent uses ONE global session (not per-channel)
        key = "global" if worker_type == "agent" else str(channel_id)

        worker_sessions = self.sessions[server_id][worker_type]

        # Check existing session
        if key in worker_sessions:
            session = worker_sessions[key]
            if not session.is_expired():
                session.touch()
                return session, False
            else:
                # Expired — remove it
                del worker_sessions[key]

        # Create new session
        session = Session(worker_type, channel_id if worker_type != "agent" else None)
        worker_sessions[key] = session
        return session, True

    def clear_expired(self):
        """Clean up all expired sessions across all servers."""
        cleaned = 0
        for server_id in list(self.sessions.keys()):
            for worker_type in list(self.sessions[server_id].keys()):
                expired_keys = [
                    k for k, s in self.sessions[server_id][worker_type].items()
                    if s.is_expired()
                ]
                for key in expired_keys:
                    del self.sessions[server_id][worker_type][key]
                    cleaned += 1

        if cleaned > 0:
            print(f"[Sessions] Cleaned up {cleaned} expired sessions")
        return cleaned

    def get_stats(self) -> dict:
        """Get session counts per worker type across all servers."""
        stats = {"responder": 0, "moderator": 0, "db_manager": 0, "agent": 0}
        for server_id in self.sessions:
            for worker_type in stats:
                stats[worker_type] += len(self.sessions[server_id].get(worker_type, {}))
        return stats

    def export_sessions(self) -> dict:
        """Serialize all active (non-expired) sessions for persistence."""
        data = {}
        for server_id, workers in self.sessions.items():
            server_data = {}
            for worker_type, sessions in workers.items():
                worker_data = {}
                for key, session in sessions.items():
                    if not session.is_expired():
                        worker_data[key] = session.to_dict()
                if worker_data:
                    server_data[worker_type] = worker_data
            if server_data:
                data[server_id] = server_data
        return data

    def import_sessions(self, data: dict):
        """Restore sessions from a persistence dict. Skips expired sessions."""
        restored = 0
        for server_id, workers in data.items():
            self._ensure_server(server_id)
            for worker_type, sessions in workers.items():
                if worker_type not in self.sessions[server_id]:
                    continue
                for key, session_data in sessions.items():
                    try:
                        session = Session.from_dict(session_data)
                        if not session.is_expired():
                            self.sessions[server_id][worker_type][key] = session
                            restored += 1
                    except Exception as e:
                        print(f"[Sessions] Failed to restore session {server_id}/{worker_type}/{key}: {e}")
        print(f"[Sessions] Restored {restored} sessions from persistence")
        return restored


def build_initial_context(messages: list, max_words: int = SESSION_CONTEXT_WORDS) -> str:
    """
    Build initial context string from recent Discord messages.
    Takes list of discord.Message objects, returns last N words as a string.
    Only used for Responder and Agent on NEW sessions.
    """
    if not messages:
        return ""

    # Build text from messages (newest last)
    lines = []
    for msg in reversed(messages):
        author = msg.author.display_name
        content = msg.content
        if content:
            lines.append(f"{author}: {content}")

    full_text = "\n".join(lines)

    # Trim to max_words from the END (most recent)
    words = full_text.split()
    if len(words) > max_words:
        words = words[-max_words:]

    return " ".join(words)


# Global instance
session_manager = SessionManager()
