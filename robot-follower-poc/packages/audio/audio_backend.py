"""Pluggable audio / conversation backends."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from contracts.audio import ConversationStatus


@runtime_checkable
class AudioBackend(Protocol):
    """Voice UX backend (console stub or ElevenLabs agent)."""

    def start(self) -> None:
        """Begin capture / conversation (may spawn background threads)."""

    def stop(self) -> None:
        """Stop background activity."""

    def is_active(self) -> bool:
        """Whether the backend currently holds live resources."""

    def status(self) -> ConversationStatus:
        """Snapshot for ``GET /audio/status``."""
