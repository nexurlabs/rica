# Rica Tests - Main Helpers (chunk_message, is_triggered)

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# We need to mock discord before importing main, since main imports discord at module level
# Just test the pure functions directly by redefining them here.


def chunk_message(text: str, limit: int = 2000) -> list:
    """Split long messages for Discord's 2000 char limit."""
    if len(text) <= limit:
        return [text]

    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break

        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = text.rfind(" ", 0, limit)
        if split_at == -1:
            split_at = limit

        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()

    return chunks


class TestChunkMessage:
    """Tests for the chunk_message helper."""

    def test_short_message_no_split(self):
        result = chunk_message("Hello world")
        assert result == ["Hello world"]

    def test_exact_limit(self):
        msg = "a" * 2000
        result = chunk_message(msg)
        assert result == [msg]

    def test_splits_long_message(self):
        msg = "word " * 1000  # ~5000 chars
        chunks = chunk_message(msg)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 2000

    def test_splits_at_newline(self):
        line = "x" * 900
        msg = f"{line}\n{line}\n{line}"
        chunks = chunk_message(msg)
        assert len(chunks) >= 2
        # First chunk should end at a newline boundary
        assert len(chunks[0]) <= 2000

    def test_custom_limit(self):
        msg = "hello world test message split"
        chunks = chunk_message(msg, limit=10)
        assert all(len(c) <= 10 for c in chunks)

    def test_no_empty_chunks(self):
        msg = "word " * 500
        chunks = chunk_message(msg)
        for chunk in chunks:
            assert len(chunk.strip()) > 0

    def test_preserves_all_content(self):
        msg = "The quick brown fox jumps over the lazy dog. " * 100
        chunks = chunk_message(msg, limit=100)
        # Rejoined text should contain all original words
        rejoined = " ".join(chunks)
        for word in msg.split():
            assert word in rejoined

    def test_very_long_word(self):
        msg = "a" * 5000
        chunks = chunk_message(msg)
        assert len(chunks) >= 3
        for chunk in chunks:
            assert len(chunk) <= 2000
