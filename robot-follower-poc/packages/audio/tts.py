"""Text-to-speech abstraction (stub for PoC)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class TextToSpeechProtocol(Protocol):
    """Hook for pyttsx3, Azure TTS, Piper, etc."""

    def speak(self, text: str) -> None:
        """Speak text using platform TTS."""


class NullTextToSpeech:
    """Logs intended speech without playing audio."""

    def speak(self, text: str) -> None:
        return
