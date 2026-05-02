"""Safety supervisor unit tests."""

from __future__ import annotations

from contracts.robot_state import RobotMode
from contracts.telemetry import MotionCommand, MotionCommandType
from infrastructure.config import Settings
from safety.safety_supervisor import SafetySupervisor


def test_emergency_forces_stop() -> None:
    s = SafetySupervisor(Settings())
    proposed = MotionCommand(command=MotionCommandType.MOVE_FORWARD)
    out = s.filter_motion(
        proposed=proposed,
        mode=RobotMode.FOLLOW,
        emergency_latched=True,
    )
    assert out.command == MotionCommandType.STOP


def test_follow_allows_forward() -> None:
    s = SafetySupervisor(Settings())
    proposed = MotionCommand(command=MotionCommandType.MOVE_FORWARD)
    out = s.filter_motion(
        proposed=proposed,
        mode=RobotMode.FOLLOW,
        emergency_latched=False,
    )
    assert out.command == MotionCommandType.MOVE_FORWARD
