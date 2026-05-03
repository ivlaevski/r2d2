"""Thread-safe in-memory transcript ring buffer."""

from __future__ import annotations

import threading
from collections import deque

from contracts.audio import TranscriptItem
from infrastructure.config import Settings


class TranscriptStore:
    """Append-only store with a hard cap; oldest rows are dropped."""

    def __init__(self, settings: Settings) -> None:
        self._max = settings.elevenlabs_transcript_max_items
        self._lock = threading.Lock()
        self._items: deque[TranscriptItem] = deque()

    def append(self, item: TranscriptItem) -> None:
        with self._lock:
            self._items.append(item)
            while len(self._items) > self._max:
                self._items.popleft()

    def list(self, limit: int | None = None) -> list[TranscriptItem]:
        with self._lock:
            items = list(self._items)
        if limit is None or limit >= len(items):
            return items
        return items[-limit:]

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)
