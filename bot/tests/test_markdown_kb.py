# Rica Tests - Markdown Knowledge Base (FTS5)

import os
import sys
import shutil
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import storage.markdown_hooks  # noqa: F401  (install patches first)

from storage.markdown_kb import markdown_kb, _safe_table_name
from storage.gcs_client import gcs_client


def test_safe_table_name_strips_non_alnum():
    assert _safe_table_name("12345") == "kb_srv_12345"
    assert _safe_table_name("abc-DEF_42") == "kb_abc_DEF_42"
    assert _safe_table_name("with spaces") == "kb_with_spaces"


def test_index_and_search():
    server = "test_kb_search"
    # Clean any leftover state from a previous run.
    gcs_client.write_file(
        server, "knowledge/main.md",
        "# Server Rules\nNo spamming in #general.\n"
        "# Chess Club\nWe play blitz on Saturdays.\n"
    )
    gcs_client.write_file(
        server, "users/u1.md",
        "# Profile\nPrefers dark roast coffee.\n"
        "Loves playing the Sicilian Defence in chess.\n"
    )

    # Search for words that are in the indexed content
    hits = markdown_kb.search(server, "chess Sicilian", limit=5)
    assert len(hits) >= 1, f"expected chess hits, got {hits}"
    paths = [h[0] for h in hits]
    assert any("u1" in p for p in paths), paths

    hits = markdown_kb.search(server, "server rules", limit=5)
    assert len(hits) >= 1, f"expected rules hits, got {hits}"

    # Search for something that doesn't exist
    hits = markdown_kb.search(server, "nonexistentquantumwidget", limit=5)
    assert hits == []

    # Stats
    s = markdown_kb.stats(server)
    assert s["indexed_files"] >= 2, s


def test_search_handles_special_characters():
    """Special chars in the query should not crash FTS5."""
    server = "test_kb_special"
    gcs_client.write_file(
        server, "knowledge/main.md",
        "Some content about programming in Python and C++.\n"
    )
    # If this doesn't raise, the test passes.
    hits = markdown_kb.search(server, "C++ programming (advanced)", limit=3)
    assert isinstance(hits, list)


def test_remove_clears_index():
    server = "test_kb_remove"
    gcs_client.write_file(
        server, "users/u9.md",
        "Temporary content about gardening tips.\n"
    )
    assert len(markdown_kb.search(server, "gardening", limit=5)) >= 1
    gcs_client.delete_file(server, "users/u9.md")
    assert markdown_kb.search(server, "gardening", limit=5) == []


def test_remove_prefix_clears_folder():
    server = "test_kb_prefix"
    gcs_client.write_file(server, "custom/a.md", "alpha")
    gcs_client.write_file(server, "custom/b.md", "beta")
    assert len(markdown_kb.search(server, "alpha", limit=5)) >= 1
    gcs_client.delete_folder(server, "custom")
    assert markdown_kb.search(server, "alpha", limit=5) == []
    assert markdown_kb.search(server, "beta", limit=5) == []


def test_non_markdown_files_not_indexed():
    server = "test_kb_filter"
    gcs_client.write_file(
        server, "knowledge/data.json", '{"hello": "world"}'
    )
    # .json should not be indexed
    s = markdown_kb.stats(server)
    paths_in_index = [h[0] for h in markdown_kb.search(server, "world", limit=10)]
    assert not any("data.json" in p for p in paths_in_index), s


def test_append_updates_index():
    server = "test_kb_append"
    gcs_client.write_file(server, "knowledge/log.md", "Initial entry.\n")
    assert len(markdown_kb.search(server, "initial", limit=5)) >= 1
    gcs_client.append_file(
        server, "knowledge/log.md", "## 2026-06-16\nNew event.\n"
    )
    # Old content still searchable
    assert len(markdown_kb.search(server, "initial", limit=5)) >= 1
    # New content also searchable
    assert len(markdown_kb.search(server, "2026-06-16", limit=5)) >= 1
