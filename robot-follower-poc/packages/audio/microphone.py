"""Microphone capture abstraction (sounddevice-based, optional for PoC)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class MicrophoneStream(Protocol):
    """Future streaming interface for wake-word / ASR pipelines."""

    def read_chunk(self) -> np.ndarray:
        """Return a short PCM chunk (shape depends on implementation)."""


class StubMicrophoneStream:
    """No-op stream for environments without audio hardware."""

    def read_chunk(self) -> np.ndarray:
        return np.zeros((0,), dtype=np.int16)
