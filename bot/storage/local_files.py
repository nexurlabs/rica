# Rica - Local File Storage
# Drop-in replacement for gcs_client — same interface, local filesystem backend

import os
import shutil
from pathlib import Path
from datetime import datetime


RICA_HOME = Path(os.environ.get("RICA_HOME", Path.home() / ".rica"))
FILES_DIR = RICA_HOME / "files"


class LocalFileClient:
    """Local filesystem storage replacing GCS. Same interface as GCSClient."""

    def __init__(self):
        FILES_DIR.mkdir(parents=True, exist_ok=True)

    def _path(self, server_id: str, file_path: str) -> Path:
        """Build full local path: ~/.rica/files/{server_id}/{file_path}"""
        file_path = file_path.lstrip("/")
        return FILES_DIR / server_id / file_path

    # =========================================================================
    # FILE OPERATIONS
    # =========================================================================

    def read_file(self, server_id: str, file_path: str) -> str:
        """Read a file. Returns content string or None if not found."""
        p = self._path(server_id, file_path)
        try:
            if p.exists():
                return p.read_text(encoding="utf-8")
            return None
        except Exception as e:
            print(f"[LocalFS] Read error: {e}")
            return None

    def write_file(self, server_id: str, file_path: str, content: str):
        """Write/overwrite a file."""
        p = self._path(server_id, file_path)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            print(f"[LocalFS] Written: {p}")
        except Exception as e:
            print(f"[LocalFS] Write error: {e}")
            raise e

    def append_file(self, server_id: str, file_path: str, content: str):
        """Append content to an existing file (or create new)."""
        p = self._path(server_id, file_path)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            if p.exists():
                existing = p.read_text(encoding="utf-8")
                p.write_text(existing + content, encoding="utf-8")
            else:
                p.write_text(content, encoding="utf-8")
        except Exception as e:
            print(f"[LocalFS] Append error: {e}")
            raise e

    def delete_file(self, server_id: str, file_path: str):
        """Delete a file."""
        p = self._path(server_id, file_path)
        try:
            if p.exists():
                p.unlink()
                print(f"[LocalFS] Deleted: {p}")
        except Exception as e:
            print(f"[LocalFS] Delete error: {e}")

    def file_exists(self, server_id: str, file_path: str) -> bool:
        """Check if a file exists."""
        return self._path(server_id, file_path).exists()

    # =========================================================================
    # DIRECTORY OPERATIONS
    # =========================================================================

    def list_files(self, server_id: str, prefix: str = "") -> list:
        """List all files under a prefix.
        Returns list of dicts: [{path, size, updated}]
        """
        base = self._path(server_id, prefix)
        if not base.exists():
            return []

        files = []
        for p in base.rglob("*"):
            if p.is_file() and p.name != ".keep":
                relative = str(p.relative_to(FILES_DIR / server_id))
                stat = p.stat()
                files.append({
                    "path": relative.replace("\\", "/"),
                    "size": stat.st_size,
                    "updated": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
        return files

    def list_folders(self, server_id: str, prefix: str = "") -> list:
        """List folders under a path."""
        base = self._path(server_id, prefix)
        if not base.exists():
            return []

        folders = []
        for p in base.iterdir():
            if p.is_dir():
                folders.append(p.name)
        return folders

    def delete_folder(self, server_id: str, prefix: str):
        """Delete all files under a prefix (folder)."""
        p = self._path(server_id, prefix)
        if p.exists() and p.is_dir():
            shutil.rmtree(p)
            print(f"[LocalFS] Deleted folder: {p}")

    # =========================================================================
    # INITIALIZATION
    # =========================================================================

    def init_server_storage(self, server_id: str):
        """Create default folder structure for a server."""
        default_dirs = [
            "users/.keep",
            "knowledge/.keep",
            "conversations/.keep",
            "custom/.keep",
        ]
        for path in default_dirs:
            if not self.file_exists(server_id, path):
                self.write_file(server_id, path, "")

        print(f"[LocalFS] Initialized storage for server {server_id}")


# Global instance — drop-in replacement for gcs_client
gcs_client = LocalFileClient()
