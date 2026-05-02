"""Stub for future cloud-based command interpretation (never required for safety)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from contracts.commands import HighLevelCommand


@runtime_checkable
class CloudCommandProvider(Protocol):
    """Optional remote NLP / intent service."""

    def fetch_interpretation(self, transcript: str) -> HighLevelCommand | None:
        """Map free-form text to a structured command, or None if unavailable."""


class NullCloudCommandProvider:
    """Explicit no-cloud implementation for local-first PoC."""

    def fetch_interpretation(self, _transcript: str) -> HighLevelCommand | None:
        return None
