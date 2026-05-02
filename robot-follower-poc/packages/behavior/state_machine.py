"""Explicit robot behavior state machine."""

from __future__ import annotations

import time

from contracts.commands import HighLevelCommandType
from contracts.robot_state import RobotMode
from infrastructure.config import Settings


class RobotBehaviorStateMachine:
    """
    Transitions:

    - IDLE -> FOLLOW on FOLLOW
    - FOLLOW -> STAY on STAY
    - FOLLOW -> TARGET_LOST if target missing for timeout
    - any -> EMERGENCY_STOP on STOP / EMERGENCY_STOP
    - EMERGENCY_STOP -> IDLE on RESET (clears latch)
    - STAY / TARGET_LOST / STOPPED: FOLLOW resumes follow mode
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._mode = RobotMode.IDLE
        self._emergency_latched = False
        self._last_target_seen_s: float | None = None

    @property
    def mode(self) -> RobotMode:
        return self._mode

    @property
    def emergency_latched(self) -> bool:
        return self._emergency_latched

    def seconds_since_target(self, now_s: float) -> float:
        if self._last_target_seen_s is None:
            return float("inf")
        return max(0.0, now_s - self._last_target_seen_s)

    def update_target_presence(self, *, target_detected: bool, now_s: float) -> None:
        """Call each tick with perception truth."""

        if target_detected:
            self._last_target_seen_s = now_s

        if self._emergency_latched:
            self._mode = RobotMode.EMERGENCY_STOP
            return

        if self._mode == RobotMode.TARGET_LOST and target_detected:
            self._mode = RobotMode.FOLLOW
            return

        if (
            self._mode == RobotMode.FOLLOW
            and not target_detected
            and self.seconds_since_target(now_s) >= self._settings.target_lost_timeout_s
        ):
            self._mode = RobotMode.TARGET_LOST

    def handle_command(self, cmd: HighLevelCommandType, desired_distance_m: float) -> None:
        """Apply a high-level command (API / voice / stub)."""

        if cmd in (HighLevelCommandType.STOP, HighLevelCommandType.EMERGENCY_STOP):
            self._emergency_latched = True
            self._mode = RobotMode.EMERGENCY_STOP
            return

        if cmd == HighLevelCommandType.RESET:
            self._emergency_latched = False
            self._mode = RobotMode.IDLE
            self._last_target_seen_s = time.monotonic()
            return

        if self._emergency_latched:
            # Must RESET before normal operation
            return

        if cmd == HighLevelCommandType.FOLLOW:
            self._mode = RobotMode.FOLLOW
            self._last_target_seen_s = time.monotonic()
            return

        if cmd == HighLevelCommandType.STAY:
            self._mode = RobotMode.STAY
            return

        if cmd == HighLevelCommandType.CHANGE_DISTANCE:
            # distance applied by RobotApplication; mode unchanged
            return
