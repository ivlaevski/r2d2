"""Lightweight in-process pub/sub for PoC service boundaries."""

from __future__ import annotations

import threading
from collections import defaultdict
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class EventBus:
    """Thread-safe publish/subscribe bus (single machine, single process)."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._subs: dict[str, list[Callable[[object], None]]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Callable[[object], None]) -> None:
        """Register a callback for a topic."""

        with self._lock:
            self._subs[topic].append(handler)

    def publish(self, topic: str, payload: object) -> None:
        """Invoke all handlers for a topic."""

        with self._lock:
            handlers = list(self._subs.get(topic, []))
        for h in handlers:
            h(payload)
