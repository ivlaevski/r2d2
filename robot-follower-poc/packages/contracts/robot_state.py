"""Robot mode and aggregate status contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from contracts.commands import HighLevelCommandType
from contracts.perception import TargetObservation
from contracts.telemetry import MotionCommandType


class RobotMode(StrEnum):
    """High-level behavioral mode for the follower robot."""

    IDLE = "IDLE"
    FOLLOW = "FOLLOW"
    STAY = "STAY"
    STOPPED = "STOPPED"
    TARGET_LOST = "TARGET_LOST"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class RobotStatus(BaseModel):
    """Snapshot of robot state for APIs and logging."""

    mode: RobotMode = RobotMode.IDLE
    last_high_level_command: HighLevelCommandType | None = None
    desired_distance_m: float = Field(default=2.0, ge=0.1, le=50.0)
    target: TargetObservation | None = None
    last_motion_command: MotionCommandType = MotionCommandType.STOP
    emergency_latched: bool = False
    target_lost_seconds: float = 0.0
    frame_timestamp_s: float = 0.0
    # Console / future ASR ingress (updated by ``audio_service`` heartbeats)
    microphone_listening: bool = False
    # Human-readable echo so UIs can show “CONFIRMED: …” after each accepted command
    command_receipt_echo: str | None = None
    command_receipt_at_s: float = 0.0
