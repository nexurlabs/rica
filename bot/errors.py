# Rica - Error Handling
# Generic user-facing errors + structured logging to Firestore

import hashlib
import time


class BotError(Exception):
    """Base exception for Rica bot errors."""

    def __init__(self, message: str, worker: str = "unknown"):
        self.message = message
        self.worker = worker
        super().__init__(message)


def _generate_error_id() -> str:
    """Generate a short, unique error ID for traceability."""
    raw = f"{time.time():.6f}"
    return hashlib.sha256(raw.encode()).hexdigest()[:8]


def safe_error_message(
    error: Exception,
    worker_name: str,
    server_id: str,
    firestore_client=None,
) -> str:
    """
    Return a generic, user-friendly error message for Discord.

    Logs the full error details to Firestore for debugging and returns
    a safe message with an error ID so the owner can look it up.
    """
    error_id = _generate_error_id()

    # Log full details to Firestore (if available)
    if firestore_client:
        try:
            firestore_client.log_error(
                server_id,
                worker_name,
                f"[{error_id}] {type(error).__name__}: {error}",
            )
        except Exception:
            pass  # Don't let logging failures cascade

    # Print full error to stdout for dev/log inspection
    print(f"[{worker_name}] Error {error_id}: {type(error).__name__}: {error}")

    return (
        f"⚠️ Something went wrong (ref: `{error_id}`). "
        f"Server owner can check error logs in the dashboard for details."
    )
