"""Shared Pydantic contracts for robot follower PoC services."""

from contracts.audio import (
    ConversationStatus,
    DetectedRobotCommand,
    TranscriptItem,
    TranscriptListResponse,
    TranscriptRole,
)
from contracts.commands import HighLevelCommand, HighLevelCommandType
from contracts.perception import (
    BoundingBox,
    PerceptionFrameResult,
    TargetLock,
    TargetObservation,
    TrackedPerson,
)
from contracts.telemetry import MotionCommand, MotionCommandType
from contracts.motor_history import MotorCommandHistoryItem
from contracts.robot_state import DashboardTargetSnapshot, RobotMode, RobotStatus

__all__ = [
    "BoundingBox",
    "ConversationStatus",
    "DashboardTargetSnapshot",
    "DetectedRobotCommand",
    "HighLevelCommand",
    "HighLevelCommandType",
    "MotionCommand",
    "MotionCommandHistoryItem",
    "MotionCommandType",
    "PerceptionFrameResult",
    "RobotMode",
    "RobotStatus",
    "TranscriptItem",
    "TranscriptListResponse",
    "TranscriptRole",
    "TargetLock",
    "TargetObservation",
    "TrackedPerson",
]
