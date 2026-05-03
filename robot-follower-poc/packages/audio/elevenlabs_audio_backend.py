"""Audio backend backed by ElevenLabs Conversational AI."""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from audio.elevenlabs_agent_client import ElevenLabsAgentClient
from contracts.audio import ConversationStatus, TranscriptItem, TranscriptRole
from infrastructure.config import Settings

if TYPE_CHECKING:
    from audio.robot_command_dispatcher import RobotCommandDispatcher
    from audio.transcript_store import TranscriptStore


class ElevenLabsAudioBackend:
    """Owns ``ElevenLabsAgentClient`` and exposes ``AudioBackend`` status."""

    def __init__(
        self,
        settings: Settings,
        transcript_store: TranscriptStore,
        dispatcher: RobotCommandDispatcher,
    ) -> None:
        self._settings = settings
        self._transcript_store = transcript_store
        self._dispatcher = dispatcher
        self._last_error: str | None = None
        self._err_lock = threading.Lock()
        self._client = ElevenLabsAgentClient(
            settings,
            transcript_store,
            dispatcher,
            on_error=self._set_error,
        )

    def _set_error(self, msg: str) -> None:
        with self._err_lock:
            self._last_error = msg
        self._transcript_store.append(
            TranscriptItem(
                id=str(uuid4()),
                timestamp_utc=datetime.now(UTC),
                role=TranscriptRole.SYSTEM,
                text=f"ElevenLabs error: {msg}",
                is_final=True,
                source="elevenlabs",
                metadata={},
            ),
        )

    def start(self) -> None:
        with self._err_lock:
            self._last_error = None
        self._client.start()

    def stop(self) -> None:
        self._client.stop()

    def is_active(self) -> bool:
        return self._client.is_active()

    def status(self) -> ConversationStatus:
        with self._err_lock:
            err = self._last_error
        return ConversationStatus(
            enabled=True,
            active=self.is_active(),
            agent_id=self._settings.elevenlabs_agent_id,
            last_error=err,
            transcript_count=len(self._transcript_store),
        )
