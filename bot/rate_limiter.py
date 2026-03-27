# Rica - Rate Limiter
# Token-bucket rate limiting for per-user and per-channel message throttling

import time
from collections import defaultdict


# =============================================================================
# DEFAULTS
# =============================================================================
DEFAULT_USER_LIMIT = 10       # messages per window
DEFAULT_USER_WINDOW = 60      # seconds
DEFAULT_CHANNEL_LIMIT = 30    # messages per window
DEFAULT_CHANNEL_WINDOW = 60   # seconds
CLEANUP_INTERVAL = 300        # seconds between stale bucket cleanup


class _Bucket:
    """Fixed-window rate limit bucket."""

    __slots__ = ("tokens", "window_start", "limit", "window")

    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window
        self.tokens = 0
        self.window_start = time.monotonic()

    def allow(self) -> bool:
        """Return True if the request is allowed, False if rate-limited."""
        now = time.monotonic()
        # Reset window if expired
        if now - self.window_start >= self.window:
            self.tokens = 0
            self.window_start = now

        if self.tokens < self.limit:
            self.tokens += 1
            return True
        return False

    def is_stale(self) -> bool:
        """Return True if this bucket hasn't been used for 2 windows."""
        return time.monotonic() - self.window_start >= self.window * 2

    def retry_after(self) -> float:
        """Seconds until the current window resets."""
        elapsed = time.monotonic() - self.window_start
        return max(0.0, self.window - elapsed)


class RateLimiter:
    """Per-user and per-channel rate limiter."""

    def __init__(
        self,
        user_limit: int = DEFAULT_USER_LIMIT,
        user_window: int = DEFAULT_USER_WINDOW,
        channel_limit: int = DEFAULT_CHANNEL_LIMIT,
        channel_window: int = DEFAULT_CHANNEL_WINDOW,
    ):
        self.user_limit = user_limit
        self.user_window = user_window
        self.channel_limit = channel_limit
        self.channel_window = channel_window

        # {key: _Bucket}
        self._user_buckets: dict[str, _Bucket] = {}
        self._channel_buckets: dict[str, _Bucket] = {}
        self._last_cleanup = time.monotonic()

    def check(self, user_id: str, channel_id: str) -> tuple[bool, str]:
        """
        Check if a message is allowed.

        Returns:
            (allowed: bool, reason: str)
            If not allowed, reason contains a user-friendly message.
        """
        self._maybe_cleanup()

        # Check user limit
        user_key = f"{user_id}"
        if user_key not in self._user_buckets:
            self._user_buckets[user_key] = _Bucket(self.user_limit, self.user_window)
        user_bucket = self._user_buckets[user_key]

        if not user_bucket.allow():
            retry = int(user_bucket.retry_after()) + 1
            return False, f"🕐 Slow down! Try again in {retry}s."

        # Check channel limit
        ch_key = f"{channel_id}"
        if ch_key not in self._channel_buckets:
            self._channel_buckets[ch_key] = _Bucket(
                self.channel_limit, self.channel_window
            )
        ch_bucket = self._channel_buckets[ch_key]

        if not ch_bucket.allow():
            retry = int(ch_bucket.retry_after()) + 1
            return False, f"🕐 This channel is busy. Try again in {retry}s."

        return True, ""

    def _maybe_cleanup(self):
        """Periodically remove stale buckets to prevent memory growth."""
        now = time.monotonic()
        if now - self._last_cleanup < CLEANUP_INTERVAL:
            return
        self._last_cleanup = now

        for store in (self._user_buckets, self._channel_buckets):
            stale = [k for k, b in store.items() if b.is_stale()]
            for k in stale:
                del store[k]

        total = len(self._user_buckets) + len(self._channel_buckets)
        if total > 0:
            print(f"[RateLimiter] Cleanup done, {total} active buckets remaining")


# Global instance
rate_limiter = RateLimiter()
