"""Speech / text command recognition abstraction (local-first)."""

from __future__ import annotations

import re
import threading
import time
from collections.abc import Callable
from typing import Protocol, runtime_checkable

from contracts.commands import HighLevelCommand, HighLevelCommandType
from infrastructure.logging import get_logger

_LOG = get_logger(__name__)


@runtime_checkable
class CommandRecognizerProtocol(Protocol):
    """Hook for Whisper, Vosk, Azure, Windows SAPI, etc."""

    def on_command(self, handler: Callable[[HighLevelCommand], None]) -> None:
        """Register a callback invoked for each parsed command."""

    def start(self) -> None:
        """Begin capture / recognition loop (may use background thread)."""

    def stop(self) -> None:
        """Stop background activity."""


def parse_command_line(line: str) -> HighLevelCommand | None:
    """
    Parse a single line from console or future ASR text.

    Supported forms::

        FOLLOW
        STAY
        STOP
        RESET
        CHANGE_DISTANCE 2.0
        EMERGENCY_STOP
    """

    raw = line.strip()
    if not raw:
        return None
    upper = raw.upper()
    if upper.startswith("CHANGE_DISTANCE"):
        m = re.match(r"CHANGE_DISTANCE\s+([0-9]*\.?[0-9]+)", upper)
        if not m:
            _LOG.warning("CHANGE_DISTANCE requires a numeric distance, got: %r", raw)
            return None
        return HighLevelCommand(
            command=HighLevelCommandType.CHANGE_DISTANCE,
            distance_m=float(m.group(1)),
        )
    try:
        cmd = HighLevelCommandType[upper]
    except KeyError:
        _LOG.warning("Unknown command: %r", raw)
        return None
    return HighLevelCommand(command=cmd)


class ConsoleCommandRecognizer:
    """
    Blocking console input recognizer (PoC).

    Replace with streaming ASR later; ``STOP`` is handled locally on this machine.
    """

    def __init__(self) -> None:
        self._handlers: list[Callable[[HighLevelCommand], None]] = []
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def on_command(self, handler: Callable[[HighLevelCommand], None]) -> None:
        self._handlers.append(handler)

    def _emit(self, cmd: HighLevelCommand) -> None:
        for h in self._handlers:
            h(cmd)

    def _loop(self) -> None:
        _LOG.info("Console command recognizer: type commands (blank line to exit).")
        while not self._stop.is_set():
            try:
                line = input("command> ")
            except EOFError:
                break
            if self._stop.is_set():
                break
            cmd = parse_command_line(line)
            if cmd is None and line.strip() == "":
                break
            if cmd is not None:
                self._emit(cmd)
            time.sleep(0)

    def start(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="console-commands", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
