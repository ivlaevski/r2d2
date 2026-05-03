"""Motor command ring buffer and de-duplication."""

from __future__ import annotations

from contracts.telemetry import MotionCommand, MotionCommandType
from infrastructure.config import Settings
from motion.simulated_motor_controller import SimulatedMotorController


def test_motor_history_dedupes_identical_commands() -> None:
    motor = SimulatedMotorController(Settings(motor_command_history_max=10))
    t = 0.0
    motor.apply(MotionCommand(command=MotionCommandType.STOP, intensity=0.0), now_s=t)
    motor.apply(MotionCommand(command=MotionCommandType.STOP, intensity=0.0), now_s=t + 0.01)
    motor.apply(MotionCommand(command=MotionCommandType.STOP, intensity=0.0), now_s=t + 0.02)
    assert len(motor.command_history) == 1


def test_motor_history_newest_first_and_cap() -> None:
    motor = SimulatedMotorController(Settings(motor_command_history_max=3))
    motor.apply(MotionCommand(command=MotionCommandType.STOP), now_s=0.0)
    motor.apply(MotionCommand(command=MotionCommandType.MOVE_FORWARD, intensity=0.5), now_s=0.1)
    motor.apply(MotionCommand(command=MotionCommandType.TURN_LEFT, intensity=0.3), now_s=0.2)
    motor.apply(MotionCommand(command=MotionCommandType.MOVE_BACKWARD, intensity=0.2), now_s=0.3)
    hist = motor.command_history
    assert len(hist) == 3
    assert hist[0].command == MotionCommandType.MOVE_BACKWARD
    assert hist[1].command == MotionCommandType.TURN_LEFT
    assert hist[2].command == MotionCommandType.MOVE_FORWARD
