"""Simple heartbeat watchdog for control loops."""

from __future__ import annotations

import time
from collections.abc import Callable


class Watchdog:
    """
    Invokes ``on_timeout`` if ``feed`` is not called within ``timeout_s``.

    Used by services to detect stalled loops (extension point).
    """

    def __init__(self, timeout_s: float, on_timeout: Callable[[], None]) -> None:
        self._timeout_s = timeout_s
        self._on_timeout = on_timeout
        self._last_feed_s = time.monotonic()

    def feed(self) -> None:
        """Mark the loop as healthy."""

        self._last_feed_s = time.monotonic()

    def check(self, now_s: float | None = None) -> None:
        """Call periodically; triggers callback if starved."""

        t = time.monotonic() if now_s is None else now_s
        if t - self._last_feed_s > self._timeout_s:
            self._on_timeout()
            self._last_feed_s = t
