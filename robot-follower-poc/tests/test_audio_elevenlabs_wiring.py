"""Audio backend wiring without the ElevenLabs SDK."""

from __future__ import annotations

import importlib.util

import pytest

from infrastructure.config import Settings
from infrastructure.robot_application import RobotApplication


def test_robot_application_default_without_elevenlabs() -> None:
    robot = RobotApplication(Settings())
    assert robot.settings.elevenlabs_audio_enabled is False
    assert robot.audio_backend.is_active() is False


@pytest.mark.skipif(
    importlib.util.find_spec("elevenlabs") is not None,
    reason="elevenlabs installed; optional dependency is present.",
)
def test_elevenlabs_enabled_without_package_raises() -> None:
    with pytest.raises(RuntimeError, match="audio-elevenlabs"):
        RobotApplication(Settings(elevenlabs_audio_enabled=True, elevenlabs_api_key="test-key"))


@pytest.mark.skipif(
    importlib.util.find_spec("elevenlabs") is None,
    reason="elevenlabs not installed; API key guard is tested when the extra is present.",
)
def test_elevenlabs_requires_auth_missing_key_raises() -> None:
    with pytest.raises(ValueError, match="ELEVENLABS_API_KEY"):
        RobotApplication(
            Settings(
                elevenlabs_audio_enabled=True,
                elevenlabs_requires_auth=True,
                elevenlabs_api_key="",
            ),
        )
