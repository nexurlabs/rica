# Rica Tests - Rate Limiter

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rate_limiter import RateLimiter, _Bucket


class TestBucket:
    """Tests for the _Bucket fixed-window rate limiter."""

    def test_allows_within_limit(self):
        bucket = _Bucket(limit=5, window=60)
        for _ in range(5):
            assert bucket.allow()

    def test_blocks_over_limit(self):
        bucket = _Bucket(limit=3, window=60)
        for _ in range(3):
            assert bucket.allow()
        assert not bucket.allow()

    def test_resets_after_window(self):
        bucket = _Bucket(limit=2, window=1)
        assert bucket.allow()
        assert bucket.allow()
        assert not bucket.allow()
        # Simulate window expiry
        bucket.window_start = time.monotonic() - 2
        assert bucket.allow()  # Should reset

    def test_retry_after(self):
        bucket = _Bucket(limit=1, window=10)
        bucket.allow()
        retry = bucket.retry_after()
        assert 0 < retry <= 10

    def test_is_stale(self):
        bucket = _Bucket(limit=5, window=1)
        assert not bucket.is_stale()
        bucket.window_start = time.monotonic() - 10
        assert bucket.is_stale()


class TestRateLimiter:
    """Tests for the RateLimiter class."""

    def test_allows_normal_usage(self):
        rl = RateLimiter(user_limit=5, user_window=60, channel_limit=10, channel_window=60)
        allowed, msg = rl.check("user1", "chan1")
        assert allowed
        assert msg == ""

    def test_blocks_user_spam(self):
        rl = RateLimiter(user_limit=3, user_window=60, channel_limit=100, channel_window=60)
        for _ in range(3):
            allowed, _ = rl.check("user1", "chan1")
            assert allowed
        allowed, msg = rl.check("user1", "chan1")
        assert not allowed
        assert "Slow down" in msg

    def test_different_users_independent(self):
        rl = RateLimiter(user_limit=2, user_window=60, channel_limit=100, channel_window=60)
        rl.check("user1", "chan1")
        rl.check("user1", "chan1")
        # user1 is at limit
        allowed, _ = rl.check("user1", "chan1")
        assert not allowed
        # user2 is fine
        allowed, _ = rl.check("user2", "chan1")
        assert allowed

    def test_blocks_channel_spam(self):
        rl = RateLimiter(user_limit=100, user_window=60, channel_limit=2, channel_window=60)
        rl.check("user1", "chan1")
        rl.check("user2", "chan1")
        allowed, msg = rl.check("user3", "chan1")
        assert not allowed
        assert "channel is busy" in msg

    def test_different_channels_independent(self):
        rl = RateLimiter(user_limit=100, user_window=60, channel_limit=1, channel_window=60)
        rl.check("user1", "chan1")
        allowed, _ = rl.check("user1", "chan1")
        assert not allowed
        # Different channel should be fine
        allowed, _ = rl.check("user1", "chan2")
        assert allowed
