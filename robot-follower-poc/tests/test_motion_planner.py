"""Motion planner unit tests."""

from __future__ import annotations

from contracts.perception import TargetObservation
from contracts.robot_state import RobotMode
from contracts.telemetry import MotionCommandType
from infrastructure.config import Settings
from motion.motion_planner import MotionPlanner


def _planner() -> MotionPlanner:
    s = Settings(
        distance_too_far_m=2.5,
        distance_too_close_m=1.2,
        horizontal_offset_threshold=0.15,
    )
    return MotionPlanner(s)


def test_follow_no_target_stops() -> None:
    p = _planner()
    obs = TargetObservation(target_detected=False)
    m = p.plan(mode=RobotMode.FOLLOW, observation=obs, desired_distance_m=2.0)
    assert m.command == MotionCommandType.STOP


def test_stay_always_stops() -> None:
    p = _planner()
    obs = TargetObservation(
        target_detected=True,
        bbox_width=50,
        bbox_height=100,
        confidence=0.9,
        horizontal_offset=0.0,
        approximate_distance_m=3.0,
    )
    m = p.plan(mode=RobotMode.STAY, observation=obs, desired_distance_m=2.0)
    assert m.command == MotionCommandType.STOP


def test_forward_when_far() -> None:
    p = _planner()
    obs = TargetObservation(
        target_detected=True,
        bbox_width=40,
        bbox_height=80,
        confidence=0.8,
        horizontal_offset=0.0,
        approximate_distance_m=3.0,
    )
    m = p.plan(mode=RobotMode.FOLLOW, observation=obs, desired_distance_m=2.0)
    assert m.command == MotionCommandType.MOVE_FORWARD


def test_backward_when_close() -> None:
    p = _planner()
    obs = TargetObservation(
        target_detected=True,
        bbox_width=80,
        bbox_height=200,
        confidence=0.8,
        horizontal_offset=0.0,
        approximate_distance_m=0.8,
    )
    m = p.plan(mode=RobotMode.FOLLOW, observation=obs, desired_distance_m=2.0)
    assert m.command == MotionCommandType.MOVE_BACKWARD


def test_turn_left_when_offset_left() -> None:
    p = _planner()
    obs = TargetObservation(
        target_detected=True,
        bbox_width=40,
        bbox_height=80,
        confidence=0.8,
        horizontal_offset=-0.5,
        approximate_distance_m=2.0,
    )
    m = p.plan(mode=RobotMode.FOLLOW, observation=obs, desired_distance_m=2.0)
    assert m.command == MotionCommandType.TURN_LEFT
