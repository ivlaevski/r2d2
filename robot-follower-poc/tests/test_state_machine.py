"""Behavior state machine unit tests."""

from __future__ import annotations

import time

import pytest

from behavior.state_machine import RobotBehaviorStateMachine
from contracts.commands import HighLevelCommandType
from contracts.robot_state import RobotMode
from infrastructure.config import Settings


def _settings(**kwargs: float) -> Settings:
    return Settings(
        target_lost_timeout_s=kwargs.get("target_lost_timeout_s", 0.5),
        desired_distance_m=2.0,
    )


def test_idle_to_follow() -> None:
    sm = RobotBehaviorStateMachine(_settings())
    sm.handle_command(HighLevelCommandType.FOLLOW, 2.0)
    assert sm.mode == RobotMode.FOLLOW


def test_follow_to_stay() -> None:
    sm = RobotBehaviorStateMachine(_settings())
    sm.handle_command(HighLevelCommandType.FOLLOW, 2.0)
    sm.handle_command(HighLevelCommandType.STAY, 2.0)
    assert sm.mode == RobotMode.STAY


def test_emergency_requires_reset() -> None:
    sm = RobotBehaviorStateMachine(_settings())
    sm.handle_command(HighLevelCommandType.FOLLOW, 2.0)
    sm.handle_command(HighLevelCommandType.STOP, 2.0)
    assert sm.mode == RobotMode.EMERGENCY_STOP
    assert sm.emergency_latched is True
    sm.handle_command(HighLevelCommandType.FOLLOW, 2.0)
    assert sm.mode == RobotMode.EMERGENCY_STOP
    sm.handle_command(HighLevelCommandType.RESET, 2.0)
    assert sm.emergency_latched is False
    assert sm.mode == RobotMode.IDLE


def test_follow_target_lost_timeout() -> None:
    sm = RobotBehaviorStateMachine(_settings(target_lost_timeout_s=0.05))
    sm.handle_command(HighLevelCommandType.FOLLOW, 2.0)
    t0 = time.monotonic()
    sm.update_target_presence(target_detected=False, now_s=t0)
    sm.update_target_presence(target_detected=False, now_s=t0 + 0.2)
    assert sm.mode == RobotMode.TARGET_LOST


def test_target_lost_recovery() -> None:
    sm = RobotBehaviorStateMachine(_settings(target_lost_timeout_s=0.05))
    sm.handle_command(HighLevelCommandType.FOLLOW, 2.0)
    t0 = time.monotonic()
    sm.update_target_presence(target_detected=False, now_s=t0 + 1.0)
    assert sm.mode == RobotMode.TARGET_LOST
    sm.update_target_presence(target_detected=True, now_s=t0 + 1.1)
    assert sm.mode == RobotMode.FOLLOW


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
