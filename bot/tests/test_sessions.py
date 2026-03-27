# Rica Tests - Session Manager

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timedelta
from sessions import Session, SessionManager, build_initial_context
from config import RESPONDER_SESSION_TIMEOUT


class TestSession:
    """Tests for the Session class."""

    def test_create_session(self):
        s = Session("responder", "chan123")
        assert s.worker_type == "responder"
        assert s.channel_id == "chan123"
        assert s.history == []
        assert not s.is_expired()

    def test_add_message(self):
        s = Session("responder")
        s.add_message("user", "hello")
        s.add_message("assistant", "hi!")
        assert len(s.history) == 2
        assert s.history[0] == {"role": "user", "content": "hello"}
        assert s.history[1] == {"role": "assistant", "content": "hi!"}

    def test_expired_session(self):
        s = Session("moderator")
        # Manually set last_used to the past
        s.last_used = datetime.now() - timedelta(minutes=60)
        assert s.is_expired()

    def test_touch_resets_timer(self):
        s = Session("moderator")
        s.last_used = datetime.now() - timedelta(minutes=60)
        assert s.is_expired()
        s.touch()
        assert not s.is_expired()

    def test_to_dict_and_from_dict(self):
        s = Session("responder", "chan456")
        s.add_message("user", "test message")
        s.add_message("assistant", "test reply")

        data = s.to_dict()
        assert data["worker_type"] == "responder"
        assert data["channel_id"] == "chan456"
        assert len(data["history"]) == 2

        restored = Session.from_dict(data)
        assert restored.worker_type == "responder"
        assert restored.channel_id == "chan456"
        assert len(restored.history) == 2
        assert restored.history[0]["content"] == "test message"


class TestSessionManager:
    """Tests for the SessionManager class."""

    def test_get_or_create_new(self):
        mgr = SessionManager()
        session, is_new = mgr.get_or_create("server1", "responder", "chan1")
        assert is_new
        assert session.worker_type == "responder"

    def test_get_existing_session(self):
        mgr = SessionManager()
        s1, new1 = mgr.get_or_create("server1", "responder", "chan1")
        s1.add_message("user", "hello")
        s2, new2 = mgr.get_or_create("server1", "responder", "chan1")
        assert not new2
        assert s2 is s1
        assert len(s2.history) == 1

    def test_agent_uses_global_key(self):
        mgr = SessionManager()
        s1, _ = mgr.get_or_create("server1", "agent", "chan1")
        s2, _ = mgr.get_or_create("server1", "agent", "chan2")
        # Agent sessions are global — same session regardless of channel
        assert s1 is s2

    def test_different_channels_different_sessions(self):
        mgr = SessionManager()
        s1, _ = mgr.get_or_create("server1", "responder", "chan1")
        s2, _ = mgr.get_or_create("server1", "responder", "chan2")
        assert s1 is not s2

    def test_expired_session_replaced(self):
        mgr = SessionManager()
        s1, _ = mgr.get_or_create("server1", "moderator", "chan1")
        s1.last_used = datetime.now() - timedelta(minutes=60)
        s2, is_new = mgr.get_or_create("server1", "moderator", "chan1")
        assert is_new
        assert s2 is not s1

    def test_clear_expired(self):
        mgr = SessionManager()
        s1, _ = mgr.get_or_create("server1", "responder", "chan1")
        s2, _ = mgr.get_or_create("server1", "responder", "chan2")
        s1.last_used = datetime.now() - timedelta(minutes=60)  # Expire s1
        cleaned = mgr.clear_expired()
        assert cleaned == 1
        stats = mgr.get_stats()
        assert stats["responder"] == 1

    def test_get_stats(self):
        mgr = SessionManager()
        mgr.get_or_create("server1", "responder", "chan1")
        mgr.get_or_create("server1", "moderator", "chan1")
        mgr.get_or_create("server1", "agent", "chan1")
        stats = mgr.get_stats()
        assert stats["responder"] == 1
        assert stats["moderator"] == 1
        assert stats["agent"] == 1
        assert stats["db_manager"] == 0

    def test_export_import_sessions(self):
        mgr = SessionManager()
        s1, _ = mgr.get_or_create("server1", "responder", "chan1")
        s1.add_message("user", "hello")
        s1.add_message("assistant", "world")

        exported = mgr.export_sessions()
        assert "server1" in exported
        assert "responder" in exported["server1"]

        # Import into a fresh manager
        mgr2 = SessionManager()
        restored = mgr2.import_sessions(exported)
        assert restored == 1
        s2, is_new = mgr2.get_or_create("server1", "responder", "chan1")
        assert not is_new  # Should find the restored session
        assert len(s2.history) == 2


class TestBuildInitialContext:
    """Tests for build_initial_context (uses mock message objects)."""

    def test_empty_messages(self):
        assert build_initial_context([]) == ""

    def test_trims_to_max_words(self):
        class FakeMsg:
            def __init__(self, name, content):
                self.author = type("Author", (), {"display_name": name})()
                self.content = content

        msgs = [FakeMsg("User", "word " * 600)]
        result = build_initial_context(msgs, max_words=100)
        assert len(result.split()) <= 100
