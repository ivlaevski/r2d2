"""Default audio backend: no ElevenLabs session (console / HTTP ingress unchanged)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.audio import ConversationStatus
from infrastructure.config import Settings

if TYPE_CHECKING:
    from audio.transcript_store import TranscriptStore


class ConsoleAudioBackend:
    """No-op conversation backend; robot control stays via buttons / ``audio_service``."""

    def __init__(self, settings: Settings, transcript_store: TranscriptStore | None = None) -> None:
        self._settings = settings
        self._transcript_store = transcript_store

    def start(self) -> None:
        return

    def stop(self) -> None:
        return

    def is_active(self) -> bool:
        return False

    def status(self) -> ConversationStatus:
        n = len(self._transcript_store) if self._transcript_store is not None else 0
        return ConversationStatus(
            enabled=False,
            active=False,
            agent_id=None,
            last_error=None,
            transcript_count=n,
        )
