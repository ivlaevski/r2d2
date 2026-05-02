"""Simulated motor: logs commands, enforces timeouts and emergency override."""

from __future__ import annotations

import time

from contracts.telemetry import MotionCommand, MotionCommandType
from infrastructure.config import Settings
from infrastructure.logging import get_logger

_LOG = get_logger(__name__)


class SimulatedMotorController:
    """
    Receives motion commands and logs them.

    Enforces max speed (intensity cap), command staleness (STOP if stale),
    and immediate STOP when emergency is active (caller passes STOP after safety).
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._last_applied: MotionCommand = MotionCommand(command=MotionCommandType.STOP)
        self._last_apply_s: float = 0.0
        self._last_log_s: float = 0.0
        self._emergency_override = False

    @property
    def last_command(self) -> MotionCommand:
        return self._last_applied

    def set_emergency_override(self, active: bool) -> None:
        """When True, all non-STOP commands are clamped to STOP."""

        self._emergency_override = active

    def apply(self, cmd: MotionCommand, *, now_s: float | None = None) -> MotionCommand:
        """Apply a command with staleness and speed checks."""

        t = time.monotonic() if now_s is None else now_s
        if self._emergency_override and cmd.command != MotionCommandType.STOP:
            cmd = MotionCommand(command=MotionCommandType.STOP, intensity=0.0)

        age = t - self._last_apply_s
        if self._last_apply_s > 0 and age > self._settings.motor_command_timeout_s:
            cmd = MotionCommand(command=MotionCommandType.STOP, intensity=0.0)

        intensity = min(cmd.intensity, self._settings.motor_max_speed)
        capped = MotionCommand(command=cmd.command, intensity=intensity)

        if t - self._last_log_s >= self._settings.motor_log_interval_s:
            _LOG.info("motor(sim): %s intensity=%.2f", capped.command.value, capped.intensity)
            self._last_log_s = t

        self._last_applied = capped
        self._last_apply_s = t
        return capped
