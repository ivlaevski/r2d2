"""Motor command history rows (kept separate from ``telemetry`` to avoid import cycles)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from contracts.telemetry import MotionCommandType


class MotorCommandHistoryItem(BaseModel):
    """One applied motor primitive (ring buffer tail for dashboards)."""

    command: MotionCommandType
    intensity: float = Field(default=0.0, ge=0.0, le=1.0)
    applied_at_s: float = Field(
        default=0.0,
        description="Wall-clock epoch seconds when the command was applied.",
    )
