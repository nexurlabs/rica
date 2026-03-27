# Rica Tests - Error Handling

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from errors import safe_error_message, _generate_error_id, BotError


class TestErrorId:
    """Tests for error ID generation."""

    def test_generates_8_char_hex(self):
        eid = _generate_error_id()
        assert len(eid) == 8
        assert all(c in "0123456789abcdef" for c in eid)

    def test_generates_unique_ids(self):
        ids = {_generate_error_id() for _ in range(100)}
        # Should be highly unique (allow a few collisions at most)
        assert len(ids) >= 95


class TestSafeErrorMessage:
    """Tests for safe_error_message."""

    def test_returns_generic_message(self):
        err = RuntimeError("Internal database connection failed at port 5432")
        msg = safe_error_message(err, "responder", "server123")
        # Should NOT contain the actual error details
        assert "5432" not in msg
        assert "database" not in msg
        # Should contain a reference ID
        assert "ref:" in msg

    def test_includes_error_ref_id(self):
        err = ValueError("test error")
        msg = safe_error_message(err, "moderator", "server123")
        assert "ref:" in msg
        # Extract ref ID and verify format
        ref_start = msg.index("ref: `") + 6
        ref_end = msg.index("`", ref_start)
        ref_id = msg[ref_start:ref_end]
        assert len(ref_id) == 8

    def test_logs_to_firestore_client(self):
        """Test that errors are logged when a firestore client is provided."""
        logged = []

        class MockFirestore:
            def log_error(self, server_id, worker, error_msg):
                logged.append((server_id, worker, error_msg))

        err = RuntimeError("secret_internal_error")
        mock_fs = MockFirestore()
        msg = safe_error_message(err, "agent", "srv999", firestore_client=mock_fs)

        assert len(logged) == 1
        assert logged[0][0] == "srv999"
        assert logged[0][1] == "agent"
        assert "secret_internal_error" in logged[0][2]
        # But the Discord message should NOT contain the raw error
        assert "secret_internal_error" not in msg

    def test_handles_firestore_failure_gracefully(self):
        """If Firestore logging itself fails, safe_error_message should not crash."""

        class BrokenFirestore:
            def log_error(self, *args):
                raise ConnectionError("Firestore is down")

        err = RuntimeError("some error")
        msg = safe_error_message(err, "responder", "srv1", firestore_client=BrokenFirestore())
        # Should still return a message without crashing
        assert "Something went wrong" in msg


class TestBotError:
    """Tests for the BotError exception class."""

    def test_bot_error_attributes(self):
        err = BotError("Test error", worker="responder")
        assert err.message == "Test error"
        assert err.worker == "responder"
        assert str(err) == "Test error"
