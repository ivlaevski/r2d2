"""Dispatch locally parsed voice commands to the robot (in-process or HTTP)."""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import httpx

from contracts.audio import DetectedRobotCommand, TranscriptItem, TranscriptRole
from contracts.commands import HighLevelCommand, HighLevelCommandType
from infrastructure.config import Settings
from infrastructure.logging import get_logger

if TYPE_CHECKING:
    from audio.transcript_store import TranscriptStore
    from infrastructure.robot_application import RobotApplication

_LOG = get_logger(__name__)


class RobotCommandDispatcher:
    """
    Applies ``DetectedRobotCommand`` to ``RobotApplication`` or POSTs to the local API.

    COME_CLOSER / MOVE_BACK / SLOWER / FASTER adjust ``CHANGE_DISTANCE`` relative to the
    current desired follow distance (PoC semantics).
    """

    def __init__(
        self,
        *,
        settings: Settings,
        robot: RobotApplication | None = None,
        transcript_store: TranscriptStore | None = None,
    ) -> None:
        self._settings = settings
        self._robot = robot
        self._transcript_store = transcript_store
        self._lock = threading.Lock()

    def _append_system(self, text: str) -> None:
        if self._transcript_store is None:
            return
        item = TranscriptItem(
            id=str(uuid4()),
            timestamp_utc=datetime.now(UTC),
            role=TranscriptRole.SYSTEM,
            text=text,
            is_final=True,
            source="command_dispatcher",
            metadata={},
        )
        self._transcript_store.append(item)

    def dispatch(self, detected: DetectedRobotCommand) -> None:
        """Map parsed intent to ``HighLevelCommand`` and apply or POST."""

        if (
            detected.command != "STOP"
            and detected.confidence < self._settings.elevenlabs_command_confidence_threshold
        ):
            _LOG.debug("Skipping dispatch (below confidence): %s", detected)
            return

        cmd = self._to_high_level(detected)
        if cmd is None:
            return

        label = cmd.command.value
        if cmd.distance_m is not None:
            label = f"{label} {cmd.distance_m} m"

        with self._lock:
            if self._robot is not None:
                self._robot.apply_high_level_command(cmd)
                _LOG.info("Dispatched voice command in-process: %s", label)
            else:
                self._post_http(cmd)
                _LOG.info("Dispatched voice command via HTTP: %s", label)

        self._append_system(f"Triggered robot command: {cmd.command.value}")

    def _to_high_level(self, d: DetectedRobotCommand) -> HighLevelCommand | None:
        c = d.command.upper()
        if c == "STOP":
            return HighLevelCommand(command=HighLevelCommandType.STOP)
        if c == "RESET":
            return HighLevelCommand(command=HighLevelCommandType.RESET)
        if c == "FOLLOW":
            return HighLevelCommand(command=HighLevelCommandType.FOLLOW)
        if c == "STAY":
            return HighLevelCommand(command=HighLevelCommandType.STAY)
        if c == "CHANGE_DISTANCE":
            if d.distance_m is None:
                return None
            return HighLevelCommand(
                command=HighLevelCommandType.CHANGE_DISTANCE,
                distance_m=d.distance_m,
            )

        robot = self._robot
        base = self._settings.desired_distance_m if robot is None else robot.desired_distance_m

        if c == "COME_CLOSER":
            new_m = max(0.1, round(base - 0.35, 2))
            return HighLevelCommand(command=HighLevelCommandType.CHANGE_DISTANCE, distance_m=new_m)
        if c == "MOVE_BACK":
            new_m = min(50.0, round(base + 0.35, 2))
            return HighLevelCommand(command=HighLevelCommandType.CHANGE_DISTANCE, distance_m=new_m)
        if c == "SLOWER":
            new_m = min(50.0, round(base + 0.25, 2))
            return HighLevelCommand(command=HighLevelCommandType.CHANGE_DISTANCE, distance_m=new_m)
        if c == "FASTER":
            new_m = max(0.1, round(base - 0.25, 2))
            return HighLevelCommand(command=HighLevelCommandType.CHANGE_DISTANCE, distance_m=new_m)

        return None

    def _post_http(self, cmd: HighLevelCommand) -> None:
        base = self._settings.robot_api_base.rstrip("/")
        payload: dict[str, object] = {"command": cmd.command.value}
        if cmd.distance_m is not None:
            payload["distance_m"] = cmd.distance_m
        with httpx.Client(timeout=5.0) as client:
            r = client.post(f"{base}/commands", json=payload)
            r.raise_for_status()
