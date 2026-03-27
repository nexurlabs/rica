# Rica - Dashboard Usage Stats + Error Logs Routes (Local Mode)

from fastapi import APIRouter, HTTPException, Request

# Imports from bot/ — path setup is centralized in dashboard/api/main.py
from storage.firestore_client import firestore_client

router = APIRouter()


@router.get("/{server_id}/usage")
async def get_usage(server_id: str, request: Request = None):
    """Get token usage stats."""
    stats = firestore_client.get_usage_stats(server_id)
    return {"server_id": server_id, "usage": stats or {}}


@router.get("/{server_id}/errors")
async def get_errors(server_id: str, limit: int = 50, request: Request = None):
    """Get recent error logs."""
    errors = firestore_client.get_error_logs(server_id, limit)
    return {"server_id": server_id, "errors": errors}


@router.delete("/{server_id}/errors")
async def clear_errors(server_id: str, request: Request = None):
    """Clear error logs."""
    # Use SQLite to delete errors
    firestore_client.conn.execute(
        "DELETE FROM errors WHERE server_id = ?", (server_id,)
    )
    firestore_client.conn.commit()
    return {"message": "Error logs cleared"}
