"""Local transcript → robot command parsing."""

from __future__ import annotations

from audio.robot_command_parser import parse_robot_command_from_transcript


def test_follow() -> None:
    cmd = parse_robot_command_from_transcript("Please follow me now")
    assert cmd is not None
    assert cmd.command == "FOLLOW"


def test_stay() -> None:
    cmd = parse_robot_command_from_transcript("stay here")
    assert cmd is not None
    assert cmd.command == "STAY"


def test_stop_prioritized_over_follow() -> None:
    cmd = parse_robot_command_from_transcript("follow me but stop immediately")
    assert cmd is not None
    assert cmd.command == "STOP"


def test_change_distance_two_meters() -> None:
    cmd = parse_robot_command_from_transcript("change distance to 2 meters")
    assert cmd is not None
    assert cmd.command == "CHANGE_DISTANCE"
    assert cmd.distance_m == 2.0


def test_change_distance_decimal() -> None:
    cmd = parse_robot_command_from_transcript("keep 1.5 m")
    assert cmd is not None
    assert cmd.command == "CHANGE_DISTANCE"
    assert cmd.distance_m == 1.5


def test_reset() -> None:
    cmd = parse_robot_command_from_transcript("clear emergency please")
    assert cmd is not None
    assert cmd.command == "RESET"


def test_come_closer() -> None:
    cmd = parse_robot_command_from_transcript("come closer")
    assert cmd is not None
    assert cmd.command == "COME_CLOSER"


def test_move_back() -> None:
    cmd = parse_robot_command_from_transcript("please back up")
    assert cmd is not None
    assert cmd.command == "MOVE_BACK"


def test_slower_faster() -> None:
    s = parse_robot_command_from_transcript("slow down")
    assert s is not None and s.command == "SLOWER"
    f = parse_robot_command_from_transcript("speed up")
    assert f is not None and f.command == "FASTER"


def test_no_command() -> None:
    assert parse_robot_command_from_transcript("hello world") is None
