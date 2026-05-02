"""Low-level motion and telemetry contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class MotionCommandType(StrEnum):
    """Simulated motor / planner output primitives."""

    STOP = "STOP"
    MOVE_FORWARD = "MOVE_FORWARD"
    MOVE_BACKWARD = "MOVE_BACKWARD"
    TURN_LEFT = "TURN_LEFT"
    TURN_RIGHT = "TURN_RIGHT"


class MotionCommand(BaseModel):
    """Motion primitive with optional intensity (0..1) for future motor mapping."""

    command: MotionCommandType
    intensity: float = Field(default=1.0, ge=0.0, le=1.0)
