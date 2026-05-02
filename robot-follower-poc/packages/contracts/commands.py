"""Human / API / voice high-level commands."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class HighLevelCommandType(StrEnum):
    """Commands that influence behavior and safety."""

    FOLLOW = "FOLLOW"
    STAY = "STAY"
    STOP = "STOP"
    RESET = "RESET"
    CHANGE_DISTANCE = "CHANGE_DISTANCE"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class HighLevelCommand(BaseModel):
    """A single high-level command with optional parameters."""

    command: HighLevelCommandType
    distance_m: float | None = Field(default=None, ge=0.1, le=50.0)
