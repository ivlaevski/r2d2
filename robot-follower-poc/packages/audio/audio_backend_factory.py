"""Construct ``AudioBackend`` from ``Settings``."""

from __future__ import annotations

import importlib.util
from typing import TYPE_CHECKING

from audio.console_audio_backend import ConsoleAudioBackend
from audio.elevenlabs_audio_backend import ElevenLabsAudioBackend
from infrastructure.config import Settings

if TYPE_CHECKING:
    from audio.audio_backend import AudioBackend
    from infrastructure.robot_application import RobotApplication


_MISSING_ELEVENLABS = (
    "ElevenLabs audio backend requested but optional dependency is not installed. "
    "Run: pip install -e .[audio-elevenlabs]"
)


def build_audio_backend(settings: Settings, robot: RobotApplication) -> AudioBackend:
    """Return console stub or ElevenLabs backend."""

    if not settings.elevenlabs_audio_enabled:
        return ConsoleAudioBackend(settings, robot.transcript_store)

    if importlib.util.find_spec("elevenlabs") is None:
        raise RuntimeError(_MISSING_ELEVENLABS)

    if settings.elevenlabs_requires_auth and not (settings.elevenlabs_api_key or "").strip():
        raise ValueError(
            "ELEVENLABS_REQUIRES_AUTH=true but ELEVENLABS_API_KEY is missing. "
            "Set the key in .env (server-side only; never exposed to the dashboard).",
        )

    return ElevenLabsAudioBackend(
        settings,
        robot.transcript_store,
        robot.command_dispatcher,
    )
