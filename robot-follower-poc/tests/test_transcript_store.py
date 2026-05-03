"""Transcript ring buffer."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from audio.transcript_store import TranscriptStore
from contracts.audio import TranscriptItem, TranscriptRole
from infrastructure.config import Settings


def _item(text: str) -> TranscriptItem:
    return TranscriptItem(
        id=str(uuid4()),
        timestamp_utc=datetime.now(UTC),
        role=TranscriptRole.USER,
        text=text,
    )


def test_transcript_store_max_items() -> None:
    s = Settings(elevenlabs_transcript_max_items=3)
    store = TranscriptStore(s)
    store.append(_item("a"))
    store.append(_item("b"))
    store.append(_item("c"))
    store.append(_item("d"))
    items = store.list()
    assert [x.text for x in items] == ["b", "c", "d"]


def test_transcript_store_clear() -> None:
    store = TranscriptStore(Settings(elevenlabs_transcript_max_items=50))
    store.append(_item("x"))
    store.clear()
    assert store.list() == []
