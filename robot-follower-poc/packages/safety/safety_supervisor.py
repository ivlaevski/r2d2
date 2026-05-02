"""Last-line motion filtering for emergency and invalid states."""

from __future__ import annotations

from contracts.robot_state import RobotMode
from contracts.telemetry import MotionCommand, MotionCommandType
from infrastructure.config import Settings


class SafetySupervisor:
    """
    Enforces safety invariants on proposed motion.

    Cloud and optional AI must not bypass this layer for motion output.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def filter_motion(
        self,
        *,
        proposed: MotionCommand,
        mode: RobotMode,
        emergency_latched: bool,
    ) -> MotionCommand:
        """Clamp motion to STOP when emergency or non-operational mode."""

        if emergency_latched or mode == RobotMode.EMERGENCY_STOP:
            return MotionCommand(command=MotionCommandType.STOP, intensity=0.0)
        if mode in (RobotMode.STAY, RobotMode.IDLE, RobotMode.TARGET_LOST, RobotMode.STOPPED):
            return MotionCommand(command=MotionCommandType.STOP, intensity=0.0)
        return proposed
