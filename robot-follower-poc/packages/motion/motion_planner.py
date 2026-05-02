"""Maps mode + target observation to motion primitives."""

from __future__ import annotations

from contracts.perception import TargetObservation
from contracts.robot_state import RobotMode
from contracts.telemetry import MotionCommand, MotionCommandType
from infrastructure.config import Settings


class MotionPlanner:
    """Rule-based planner with configurable thresholds."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def plan(
        self,
        *,
        mode: RobotMode,
        observation: TargetObservation,
        desired_distance_m: float,
    ) -> MotionCommand:
        """
        Produce a motion command.

        Priority: inactive modes -> no target -> distance -> horizontal alignment.
        """

        if mode in (
            RobotMode.STAY,
            RobotMode.STOPPED,
            RobotMode.IDLE,
            RobotMode.TARGET_LOST,
            RobotMode.EMERGENCY_STOP,
        ):
            return MotionCommand(command=MotionCommandType.STOP, intensity=0.0)

        if mode != RobotMode.FOLLOW:
            return MotionCommand(command=MotionCommandType.STOP, intensity=0.0)

        if not observation.target_detected:
            return MotionCommand(command=MotionCommandType.STOP, intensity=0.0)

        dist = observation.approximate_distance_m
        if dist is not None:
            far_limit = max(self._settings.distance_too_far_m, desired_distance_m)
            close_limit = min(self._settings.distance_too_close_m, desired_distance_m)
            if close_limit >= far_limit:
                far_limit = desired_distance_m + 0.25
                close_limit = desired_distance_m - 0.25
            if dist > far_limit:
                return MotionCommand(command=MotionCommandType.MOVE_FORWARD)
            if dist < close_limit:
                return MotionCommand(command=MotionCommandType.MOVE_BACKWARD)

        off = observation.horizontal_offset
        h_thr = self._settings.horizontal_offset_threshold
        if off < -h_thr:
            return MotionCommand(command=MotionCommandType.TURN_LEFT)
        if off > h_thr:
            return MotionCommand(command=MotionCommandType.TURN_RIGHT)

        return MotionCommand(command=MotionCommandType.STOP)
