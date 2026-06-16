# Rica Tests - User Memory Module

import os
import sys
import asyncio
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import storage.markdown_hooks  # noqa: F401  (install patches first)

from storage.gcs_client import gcs_client
from memory.user_memory import (
    ensure_file, read, append_known_fact, rewrite_section,
    build_context_for_responder, extract_and_store, _user_path, SECTIONS,
)


def test_ensure_file_creates_with_schema():
    server = "test_um_create"
    if gcs_client.file_exists(server, _user_path("u1")):
        gcs_client.delete_file(server, _user_path("u1"))
    path = ensure_file(server, "u1", "Alice")
    assert path == "users/u1.md"
    content = gcs_client.read_file(server, _user_path("u1"))
    assert content is not None
    # Schema headers all present
    for section in SECTIONS:
        assert f"## {section}" in content, f"missing {section}"
    assert "Alice" in content and "u1" in content


def test_append_known_fact_creates_dated_bullet():
    server = "test_um_facts"
    ensure_file(server, "u2", "Bob")
    append_known_fact(server, "u2", "Bob", "Studying mechanical engineering")
    append_known_fact(server, "u2", "Bob", "Loves playing chess")
    content = gcs_client.read_file(server, _user_path("u2"))
    # Both facts present, dated, in the Known facts section
    assert "Studying mechanical engineering" in content
    assert "Loves playing chess" in content
    # Newest at the top of the section
    known_idx = content.index("## Known facts")
    loves_idx = content.index("Loves playing chess")
    studying_idx = content.index("Studying mechanical engineering")
    assert loves_idx < studying_idx, "newest fact should appear first"


def test_rewrite_section_replaces_body():
    server = "test_um_rewrite"
    ensure_file(server, "u3", "Carol")
    rewrite_section(server, "u3", "Carol", "Profile", "- Display name: Carol\n- Location: Delhi")
    content = gcs_client.read_file(server, _user_path("u3"))
    assert "Display name: Carol" in content
    assert "Location: Delhi" in content
    # Rewrite again — old content should be gone
    rewrite_section(server, "u3", "Carol", "Profile", "- Display name: Carol")
    content = gcs_client.read_file(server, _user_path("u3"))
    assert "Location: Delhi" not in content


def test_rewrite_unknown_section_rejected():
    server = "test_um_invalid"
    ensure_file(server, "u4", "Dave")
    try:
        rewrite_section(server, "u4", "Dave", "Hobbies", "- fishing")
    except ValueError:
        return
    raise AssertionError("expected ValueError for unknown section")


def test_build_context_short_file_returns_full():
    server = "test_um_ctx_short"
    ensure_file(server, "u5", "Eve")
    append_known_fact(server, "u5", "Eve", "First fact")
    ctx = build_context_for_responder(server, "u5", "Eve")
    assert "Eve" in ctx
    assert "First fact" in ctx


def test_build_context_long_file_uses_search():
    server = "test_um_ctx_long"
    ensure_file(server, "u6", "Frank")
    # Stuff many facts to blow past MAX_CONTEXT_CHARS
    for i in range(80):
        append_known_fact(server, "u6", "Frank", f"Fact number {i} about Frank's interests in topic {i}")
    ctx = build_context_for_responder(server, "u6", "Frank")
    # Should have a header and an FTS5-derived snippet block
    assert "Frank" in ctx
    assert "[Relevant past facts]" in ctx


def test_extract_and_store_async():
    """End-to-end: an LLM-shaped provider returns JSON, items land in the file."""
    server = "test_um_extract"
    ensure_file(server, "u7", "Grace")

    class FakeProvider:
        async def generate(self, *, messages, system_prompt, json_mode, temperature, max_tokens):
            return json.dumps({
                "remember": [
                    {"section": "Profile", "text": "Studying physics at MIT"},
                    {"section": "Known facts", "text": "Mentioned thesis is on quantum computing"},
                    {"section": "Preferences", "text": "Prefers metric units"},
                ]
            })

    stored = asyncio.run(extract_and_store(
        server, "u7", "Grace",
        "I study physics at MIT and my thesis is on quantum computing. I always use metric.",
        "Got it! Physics and quantum — fun. Anything specific I can help with?",
        extractor_provider=FakeProvider(),
    ))
    assert stored == 3
    content = gcs_client.read_file(server, _user_path("u7"))
    assert "Studying physics at MIT" in content
    assert "Mentioned thesis is on quantum computing" in content
    assert "Prefers metric units" in content


def test_extract_handles_empty_remember():
    server = "test_um_empty"
    ensure_file(server, "u8", "Hank")

    class FakeProvider:
        async def generate(self, *, messages, system_prompt, json_mode, temperature, max_tokens):
            return json.dumps({"remember": []})

    stored = asyncio.run(extract_and_store(
        server, "u8", "Hank",
        "what's 2 + 2?", "4",
        extractor_provider=FakeProvider(),
    ))
    assert stored == 0


def test_extract_handles_bad_json():
    server = "test_um_badjson"
    ensure_file(server, "u9", "Ivy")
    before = gcs_client.read_file(server, _user_path("u9"))

    class FakeProvider:
        async def generate(self, *, messages, system_prompt, json_mode, temperature, max_tokens):
            return "this is not json at all"

    stored = asyncio.run(extract_and_store(
        server, "u9", "Ivy",
        "hello", "hi",
        extractor_provider=FakeProvider(),
    ))
    assert stored == 0
    after = gcs_client.read_file(server, _user_path("u9"))
    # File should be unchanged (or at least not corrupted)
    assert after is not None
    assert "Ivy" in after
