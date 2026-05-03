"""Audio / conversation transcript contracts (server-side only)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TranscriptRole(StrEnum):
    """Who produced a transcript line."""

    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class TranscriptItem(BaseModel):
    """One line in the conversation transcript."""

    id: str
    timestamp_utc: datetime
    role: TranscriptRole
    text: str
    is_final: bool = True
    source: str = Field(default="elevenlabs", description="Origin label for UIs.")
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationStatus(BaseModel):
    """High-level ElevenLabs / audio backend state for dashboards."""

    enabled: bool = False
    active: bool = False
    agent_id: str | None = None
    last_error: str | None = None
    transcript_count: int = 0


class DetectedRobotCommand(BaseModel):
    """Locally parsed robot intent from user speech or text."""

    command: str
    distance_m: float | None = None
    raw_text: str = ""
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: str = Field(default="user_transcript", description="Where the parse came from.")


class TranscriptListResponse(BaseModel):
    """API wrapper for transcript polling."""

    items: list[TranscriptItem] = Field(default_factory=list)
