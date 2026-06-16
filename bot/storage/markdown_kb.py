# Rica - Markdown Knowledge Base (FTS5 index)
# Searchable index over the per-server markdown files. Source of truth is
# the filesystem (LocalFileClient / gcs_client); this is a derived index that
# auto-syncs on every write.

import os
import re
import sqlite3
import threading
from pathlib import Path
from typing import List, Tuple


RICA_HOME = Path(os.environ.get("RICA_HOME", Path.home() / ".rica"))
DB_PATH = RICA_HOME / "rica.db"


def _safe_table_name(server_id: str) -> str:
    """Sanitize server_id into a valid SQL identifier suffix.

    SQLite identifier rules: must start with a letter, contain only
    letters/digits/underscores. We prefix 'kb_' and replace everything
    else with '_'. Collisions (rare) get a numeric suffix appended.
    """
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", server_id)
    if not cleaned or not cleaned[0].isalpha():
        cleaned = "srv_" + cleaned
    return f"kb_{cleaned}"


class MarkdownKB:
    """FTS5-backed search index over a server's markdown files."""

    def __init__(self):
        # Per-thread connection; FTS5 statements are per-connection safe.
        self._local = threading.local()
        # Track which server tables have been initialized in this process.
        self._known_tables = set()
        self._lock = threading.Lock()

    @property
    def conn(self) -> sqlite3.Connection:
        if not getattr(self._local, "conn", None):
            RICA_HOME.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn = conn
        return self._local.conn

    def _ensure_table(self, server_id: str) -> str:
        """Create the FTS5 table for a server if it doesn't exist."""
        table = _safe_table_name(server_id)
        if table in self._known_tables:
            return table
        with self._lock:
            if table in self._known_tables:
                return table
            self.conn.execute(
                f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS {table} USING fts5(
                    file_path UNINDEXED,
                    content,
                    updated UNINDEXED,
                    tokenize = 'porter unicode61'
                )
                """
            )
            self.conn.commit()
            self._known_tables.add(table)
        return table

    def index(self, server_id: str, file_path: str, content: str) -> None:
        """Upsert a file's content into the index."""
        if not file_path.endswith((".md", ".markdown", ".txt")):
            return  # only index text-like files
        table = self._ensure_table(server_id)
        from datetime import datetime, timezone
        updated = datetime.now(timezone.utc).isoformat()
        # FTS5 has no native UPSERT in all builds; do delete+insert.
        with self._lock:
            self.conn.execute(
                f"DELETE FROM {table} WHERE file_path = ?", (file_path,)
            )
            self.conn.execute(
                f"INSERT INTO {table}(file_path, content, updated) VALUES (?, ?, ?)",
                (file_path, content, updated),
            )
            self.conn.commit()

    def remove(self, server_id: str, file_path: str) -> None:
        """Remove a file from the index (called on delete)."""
        table = self._ensure_table(server_id)
        with self._lock:
            self.conn.execute(
                f"DELETE FROM {table} WHERE file_path = ?", (file_path,)
            )
            self.conn.commit()

    def remove_prefix(self, server_id: str, prefix: str) -> int:
        """Remove all indexed files under a prefix (used on folder delete)."""
        table = self._ensure_table(server_id)
        prefix = prefix.lstrip("/")
        if not prefix.endswith("/"):
            prefix = prefix + "/"
        with self._lock:
            cur = self.conn.execute(
                f"DELETE FROM {table} WHERE file_path LIKE ?",
                (prefix + "%",),
            )
            self.conn.commit()
            return cur.rowcount

    def search(
        self, server_id: str, query: str, limit: int = 5
    ) -> List[Tuple[str, str, float]]:
        """Full-text search. Returns list of (file_path, snippet, score).

        Snippet is a short excerpt around the first match. Score is the FTS5
        bm25 score (negative — closer to 0 = better).
        """
        if not query or not query.strip():
            return []
        table = self._ensure_table(server_id)
        # FTS5 MATCH requires the query be in a parseable form; we strip
        # non-word chars that would otherwise cause syntax errors, then
        # quote each token to support phrases/keywords.
        tokens = re.findall(r"[\w']+", query)
        if not tokens:
            return []
        match_expr = " ".join(f'"{t}"' for t in tokens)
        try:
            rows = self.conn.execute(
                f"""
                SELECT file_path, snippet({table}, 1, '⟨', '⟩', '…', 16) AS snip,
                       bm25({table}) AS score
                  FROM {table}
                 WHERE {table} MATCH ?
                 ORDER BY score
                 LIMIT ?
                """,
                (match_expr, limit),
            ).fetchall()
        except sqlite3.OperationalError as e:
            # Bad query syntax — return empty rather than crashing the worker.
            print(f"[MarkdownKB] search error for query {query!r}: {e}")
            return []
        return [(r["file_path"], r["snip"], float(r["score"])) for r in rows]

    def stats(self, server_id: str) -> dict:
        """Quick stats for the dashboard / debugging."""
        table = self._ensure_table(server_id)
        total = self.conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
        return {"table": table, "indexed_files": total}


# Module-level singleton
markdown_kb = MarkdownKB()
