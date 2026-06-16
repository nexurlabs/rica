import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from text_sanitizer import strip_reasoning


class TestStripReasoning:
    def test_removes_complete_think_block(self):
        text = "<think>private notes</think>\nhello again rose"
        assert strip_reasoning(text) == "hello again rose"

    def test_removes_multiline_reasoning_block(self):
        text = "before\n<reasoning>\nsecret\nnotes\n</reasoning>\nafter"
        assert strip_reasoning(text) == "before\nafter"

    def test_removes_orphan_closing_from_old_history(self):
        text = "private notes leaked earlier\n</think>\nvisible answer"
        assert strip_reasoning(text) == "visible answer"

    def test_removes_fenced_thinking_block(self):
        text = "```thinking\nprivate\n```\npublic"
        assert strip_reasoning(text) == "public"

    def test_unclosed_think_is_not_published(self):
        assert strip_reasoning("<think>private notes") == ""
