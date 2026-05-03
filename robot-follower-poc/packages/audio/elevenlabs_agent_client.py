"""ElevenLabs Conversational AI client (lazy SDK imports)."""

from __future__ import annotations

import threading
import urllib.parse
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from infrastructure.config import Settings
from infrastructure.logging import get_logger

if TYPE_CHECKING:
    from audio.robot_command_dispatcher import RobotCommandDispatcher
    from audio.transcript_store import TranscriptStore

_LOG = get_logger(__name__)


class ElevenLabsAgentClient:
    """
    Wraps the ElevenLabs ``Conversation`` session on a worker thread.

    SDK imports happen only in ``start()`` so the repo runs without ``elevenlabs`` installed.
    """

    def __init__(
        self,
        settings: Settings,
        transcript_store: TranscriptStore,
        dispatcher: RobotCommandDispatcher,
        *,
        on_error: Callable[[str], None],
    ) -> None:
        self._settings = settings
        self._transcript_store = transcript_store
        self._dispatcher = dispatcher
        self._on_error = on_error
        self._conversation: Any = None
        self._worker: threading.Thread | None = None
        self._stop = threading.Event()
        self._started = False
        self._lock = threading.Lock()

    def is_active(self) -> bool:
        with self._lock:
            if self._conversation is None:
                return False
            th = getattr(self._conversation, "_thread", None)
            return bool(th and th.is_alive())

    def start(self) -> None:
        with self._lock:
            if self._started and self.is_active():
                return
            self._stop.clear()
            self._started = True
            self._worker = threading.Thread(
                target=self._run_worker,
                name="elevenlabs-conversation",
                daemon=True,
            )
            self._worker.start()

    def stop(self) -> None:
        self._stop.set()
        conv = None
        with self._lock:
            conv = self._conversation
        if conv is not None:
            try:
                conv.end_session()
            except Exception:
                _LOG.exception("end_session failed")
        w = self._worker
        if w is not None and w.is_alive():
            w.join(timeout=10.0)
        with self._lock:
            self._conversation = None
            self._started = False
            self._worker = None

    def _run_worker(self) -> None:
        try:
            self._start_conversation_blocking()
        except Exception as exc:
            _LOG.exception("ElevenLabs worker failed")
            self._on_error(str(exc))

    def _start_conversation_blocking(self) -> None:
        from contracts.audio import TranscriptItem, TranscriptRole

        try:
            from elevenlabs.client import ElevenLabs
            from elevenlabs.conversational_ai.conversation import Conversation
            from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface
        except ImportError as exc:
            raise RuntimeError(
                "ElevenLabs audio backend requested but optional dependency is not installed. "
                "Run: pip install -e .[audio-elevenlabs]",
            ) from exc

        client = ElevenLabs(api_key=self._settings.elevenlabs_api_key or None)

        if self._settings.elevenlabs_use_signed_url and self._settings.elevenlabs_requires_auth:
            try:
                signed = client.conversational_ai.conversations.get_signed_url(
                    agent_id=self._settings.elevenlabs_agent_id,
                )
                surl = getattr(signed, "signed_url", None)
                if surl:
                    _LOG.debug(
                        "Prefetched signed conversation URL (host=%s)",
                        urllib.parse.urlparse(str(surl)).hostname,
                    )
            except Exception:
                _LOG.exception("Signed URL prefetch failed (continuing; SDK may retry)")

        def on_user(transcript: str) -> None:
            text = (transcript or "").strip()
            if not text:
                return
            item = TranscriptItem(
                id=str(uuid4()),
                timestamp_utc=datetime.now(UTC),
                role=TranscriptRole.USER,
                text=text,
                is_final=True,
                source="elevenlabs",
                metadata={},
            )
            self._transcript_store.append(item)
            from audio.robot_command_parser import parse_robot_command_from_transcript

            detected = parse_robot_command_from_transcript(text)
            if detected is not None:
                self._dispatcher.dispatch(detected)

        def on_agent(response: str) -> None:
            text = (response or "").strip()
            if not text:
                return
            item = TranscriptItem(
                id=str(uuid4()),
                timestamp_utc=datetime.now(UTC),
                role=TranscriptRole.AGENT,
                text=text,
                is_final=True,
                source="elevenlabs",
                metadata={},
            )
            self._transcript_store.append(item)

        def on_correction(original: str, corrected: str) -> None:
            item = TranscriptItem(
                id=str(uuid4()),
                timestamp_utc=datetime.now(UTC),
                role=TranscriptRole.AGENT,
                text=corrected,
                is_final=True,
                source="elevenlabs",
                metadata={"original": original, "correction": True},
            )
            self._transcript_store.append(item)

        def on_latency(ms: int) -> None:
            _LOG.debug("ElevenLabs latency measurement: %sms", ms)

        audio_interface = DefaultAudioInterface()
        requires_auth = self._settings.elevenlabs_requires_auth
        if self._settings.elevenlabs_use_signed_url and self._settings.elevenlabs_requires_auth:
            requires_auth = True

        conversation = Conversation(
            client=client,
            agent_id=self._settings.elevenlabs_agent_id,
            requires_auth=requires_auth,
            audio_interface=audio_interface,
            callback_user_transcript=on_user,
            callback_agent_response=on_agent,
            callback_agent_response_correction=on_correction,
            callback_latency_measurement=on_latency,
        )

        with self._lock:
            self._conversation = conversation

        conversation.start_session()
        self._stop.wait()
