"""Wires behavior, motion, safety, and shared runtime state (single-process PoC)."""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING

from audio.audio_backend import AudioBackend
from behavior.state_machine import RobotBehaviorStateMachine
from contracts.commands import HighLevelCommand, HighLevelCommandType
from contracts.perception import BoundingBox, PerceptionFrameResult, TargetObservation, TrackedPerson
from contracts.robot_state import DashboardTargetSnapshot, RobotStatus
from infrastructure.config import Settings
from motion.motion_planner import MotionPlanner
from motion.simulated_motor_controller import SimulatedMotorController
from safety.safety_supervisor import SafetySupervisor

if TYPE_CHECKING:
    from audio.command_recognizer import CommandRecognizerProtocol
    from audio.robot_command_dispatcher import RobotCommandDispatcher
    from audio.transcript_store import TranscriptStore


def _bbox_iou(a: BoundingBox, b: BoundingBox) -> float:
    ax2, ay2 = a.x + a.width, a.y + a.height
    bx2, by2 = b.x + b.width, b.y + b.height
    inter_x1 = max(a.x, b.x)
    inter_y1 = max(a.y, b.y)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    iw = max(0, inter_x2 - inter_x1)
    ih = max(0, inter_y2 - inter_y1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(1, a.width * a.height)
    area_b = max(1, b.width * b.height)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _is_followed_target(primary: TargetObservation, person: TrackedPerson) -> bool:
    if not primary.target_detected:
        return False
    if primary.track_id is not None and person.track_id is not None:
        return int(primary.track_id) == int(person.track_id)
    return _bbox_iou(primary.bbox, person.bbox) >= 0.2


def _dashboard_targets(
    perception: PerceptionFrameResult | None,
    primary: TargetObservation,
) -> list[DashboardTargetSnapshot]:
    if perception is None or not perception.tracked_people:
        return []
    return [
        DashboardTargetSnapshot(
            track_id=p.track_id,
            approximate_distance_m=p.approximate_distance_m,
            confidence=p.confidence,
            is_followed=_is_followed_target(primary, p),
            face_thumbnail_jpeg_b64=p.face_thumbnail_jpeg_b64,
        )
        for p in perception.tracked_people
    ]


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

        from audio.audio_backend_factory import build_audio_backend
        from audio.robot_command_dispatcher import RobotCommandDispatcher
        from audio.transcript_store import TranscriptStore

        self._transcript_store = TranscriptStore(settings)
        self._command_dispatcher = RobotCommandDispatcher(
            settings=settings,
            robot=self,
            transcript_store=self._transcript_store,
        )
        self._audio_backend = build_audio_backend(settings, self)

    @property
    def settings(self) -> Settings:
        return self._settings

    @property
    def transcript_store(self) -> TranscriptStore:
        return self._transcript_store

    @property
    def command_dispatcher(self) -> RobotCommandDispatcher:
        return self._command_dispatcher

    @property
    def audio_backend(self) -> AudioBackend:
        """Console or ElevenLabs audio backend."""

        return self._audio_backend

    @property
    def desired_distance_m(self) -> float:
        with self._lock:
            return self._desired_distance_m

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

            targets = _dashboard_targets(perception, target)
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
                targets_count=len(targets),
                targets=targets,
                motor_command_history=self._motor.command_history,
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
            targets = _dashboard_targets(perception, target)
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
                targets_count=len(targets),
                targets=targets,
                motor_command_history=self._motor.command_history,
            )

    def emergency_stop_from_audio(self) -> None:
        """Local path for voice STOP — must not depend on cloud."""

        self.apply_high_level_command(
            HighLevelCommand(command=HighLevelCommandType.EMERGENCY_STOP),
        )

    def wire_audio_recognizer(self, recognizer: CommandRecognizerProtocol) -> None:
        """Optional: connect recognizer callbacks to ``apply_high_level_command``."""

        recognizer.on_command(self.apply_high_level_command)
