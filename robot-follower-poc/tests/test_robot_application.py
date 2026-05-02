"""RobotApplication wiring tests."""

from __future__ import annotations

from contracts.commands import HighLevelCommand, HighLevelCommandType
from infrastructure.config import Settings
from infrastructure.robot_application import RobotApplication


def test_command_receipt_echo_after_apply() -> None:
    robot = RobotApplication(Settings())
    robot.apply_high_level_command(HighLevelCommand(command=HighLevelCommandType.FOLLOW))
    st = robot.get_status()
    assert st.command_receipt_echo == "CONFIRMED: FOLLOW"
    assert st.command_receipt_at_s > 0.0


def test_microphone_listening_requires_heartbeat() -> None:
    robot = RobotApplication(Settings())
    assert robot.get_status().microphone_listening is False
    robot.set_microphone_listening(True)
    assert robot.get_status().microphone_listening is True
    robot.set_microphone_listening(False)
    assert robot.get_status().microphone_listening is False
