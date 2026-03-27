# Rica - Dashboard Data Browser Routes (Local file explorer)

from fastapi import APIRouter, HTTPException, Request

# Imports from bot/ — path setup is centralized in dashboard/api/main.py
from storage.gcs_client import gcs_client

router = APIRouter()


@router.get("/{server_id}/files")
async def list_files(server_id: str, prefix: str = "", request: Request = None):
    """List files in a directory (read-only)."""
    files = gcs_client.list_files(server_id, prefix)
    folders = gcs_client.list_folders(server_id, prefix)

    return {
        "prefix": prefix,
        "folders": folders,
        "files": files,
    }


@router.get("/{server_id}/file")
async def read_file(server_id: str, path: str, request: Request = None):
    """Read a specific file (read-only)."""
    content = gcs_client.read_file(server_id, path)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")

    return {
        "path": path,
        "content": content,
    }
