"""Wires behavior, motion, safety, and shared runtime state (single-process PoC)."""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING

from behavior.state_machine import RobotBehaviorStateMachine
from contracts.commands import HighLevelCommand, HighLevelCommandType
from contracts.perception import PerceptionFrameResult, TargetObservation
from contracts.robot_state import RobotStatus
from infrastructure.config import Settings
from motion.motion_planner import MotionPlanner
from motion.simulated_motor_controller import SimulatedMotorController
from safety.safety_supervisor import SafetySupervisor

if TYPE_CHECKING:
    from audio.command_recognizer import CommandRecognizerProtocol


def _format_command_receipt_echo(cmd: HighLevelCommand) -> str:
    """Repeatable confirmation line for dashboards and logs."""

    if cmd.command == HighLevelCommandType.CHANGE_DISTANCE and cmd.distance_m is not None:
        return f"CONFIRMED: CHANGE_DISTANCE {cmd.distance_m} m"
    return f"CONFIRMED: {cmd.command.value}"


class RobotApplication:
    """
    Application facade: owns state machine, planner, motor stub, and safety.

    API and orchestrator share one instance when run with ``--with-api``.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._lock = threading.RLock()
        self._state_machine = RobotBehaviorStateMachine(settings)
        self._planner = MotionPlanner(settings)
        self._motor = SimulatedMotorController(settings)
        self._safety = SafetySupervisor(settings)
        self._last_perception: PerceptionFrameResult | None = None
        self._last_command: HighLevelCommand | None = None
        self._desired_distance_m = settings.desired_distance_m
        self._last_status_log_s = 0.0
        self._audio_ingress_active = False
        self._audio_last_heartbeat_m = 0.0
        self._command_receipt_echo: str | None = None
        self._command_receipt_at_s = 0.0

    @property
    def settings(self) -> Settings:
        return self._settings

    def set_microphone_listening(self, listening: bool) -> None:
        """Mark console / mic ingress active; refresh heartbeat timestamp when true."""

        with self._lock:
            self._audio_ingress_active = listening
            if listening:
                self._audio_last_heartbeat_m = time.monotonic()

    def apply_high_level_command(self, cmd: HighLevelCommand) -> None:
        """Enqueue or apply a command from HTTP or local recognizer."""

        with self._lock:
            self._last_command = cmd
            if cmd.command == HighLevelCommandType.CHANGE_DISTANCE and cmd.distance_m is not None:
                self._desired_distance_m = cmd.distance_m
            self._state_machine.handle_command(cmd.command, self._desired_distance_m)
            self._command_receipt_echo = _format_command_receipt_echo(cmd)
            self._command_receipt_at_s = time.time()

    def _microphone_listening_effective(self, now_m: float) -> bool:
        if not self._audio_ingress_active:
            return False
        return (now_m - self._audio_last_heartbeat_m) <= self._settings.audio_listening_ttl_s

    def ingest_perception(self, frame: PerceptionFrameResult) -> None:
        """Update last perception snapshot (from camera thread or perception service)."""

        with self._lock:
            self._last_perception = frame

    def tick(self, now_s: float | None = None) -> RobotStatus:
        """
        One control cycle: safety, behavior, planning, motor.

        Returns current ``RobotStatus`` for APIs and logging.
        """

        t = time.monotonic() if now_s is None else now_s
        with self._lock:
            perception = self._last_perception
            target = perception.primary_target if perception else TargetObservation()
            self._state_machine.update_target_presence(
                target_detected=target.target_detected,
                now_s=t,
            )

            mode = self._state_machine.mode
            self._motor.set_emergency_override(self._state_machine.emergency_latched)
            motion = self._planner.plan(
                mode=mode,
                observation=target,
                desired_distance_m=self._desired_distance_m,
            )
            motion = self._safety.filter_motion(
                proposed=motion,
                mode=mode,
                emergency_latched=self._state_machine.emergency_latched,
            )
            self._motor.apply(motion, now_s=t)

            status = RobotStatus(
                mode=mode,
                last_high_level_command=self._last_command.command if self._last_command else None,
                desired_distance_m=self._desired_distance_m,
                target=target if target.target_detected else None,
                last_motion_command=motion.command,
                emergency_latched=self._state_machine.emergency_latched,
                target_lost_seconds=self._state_machine.seconds_since_target(t),
                frame_timestamp_s=perception.timestamp_s if perception else 0.0,
                microphone_listening=self._microphone_listening_effective(t),
                command_receipt_echo=self._command_receipt_echo,
                command_receipt_at_s=self._command_receipt_at_s,
            )

            if t - self._last_status_log_s >= self._settings.status_log_interval_s:
                self._last_status_log_s = t

            return status

    def get_status(self) -> RobotStatus:
        """Return status without advancing motor timeouts (read-only-ish)."""

        with self._lock:
            perception = self._last_perception
            target = perception.primary_target if perception else TargetObservation()
            now_m = time.monotonic()
            return RobotStatus(
                mode=self._state_machine.mode,
                last_high_level_command=self._last_command.command if self._last_command else None,
                desired_distance_m=self._desired_distance_m,
                target=target if target.target_detected else None,
                last_motion_command=self._motor.last_command.command,
                emergency_latched=self._state_machine.emergency_latched,
                target_lost_seconds=self._state_machine.seconds_since_target(now_m),
                frame_timestamp_s=perception.timestamp_s if perception else 0.0,
                microphone_listening=self._microphone_listening_effective(now_m),
                command_receipt_echo=self._command_receipt_echo,
                command_receipt_at_s=self._command_receipt_at_s,
            )

    def emergency_stop_from_audio(self) -> None:
        """Local path for voice STOP — must not depend on cloud."""

        self.apply_high_level_command(
            HighLevelCommand(command=HighLevelCommandType.EMERGENCY_STOP),
        )

    def wire_audio_recognizer(self, recognizer: CommandRecognizerProtocol) -> None:
        """Optional: connect recognizer callbacks to ``apply_high_level_command``."""

        recognizer.on_command(self.apply_high_level_command)
