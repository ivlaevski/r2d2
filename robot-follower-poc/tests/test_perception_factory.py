"""Perception factory and optional backend wiring."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from infrastructure.config import Settings
from infrastructure.perception_factory import create_person_tracker
from perception.hog_person_tracker import HOGPersonTracker


def test_hog_backend_returns_hog_tracker() -> None:
    t = create_person_tracker(Settings(vision_backend="hog"))
    assert isinstance(t, HOGPersonTracker)


def test_ultralytics_backend_missing_dependency_message() -> None:
    with (
        patch(
            "integrations.ultralytics_yolo_botsort.ultralytics_person_tracker.UltralyticsPersonTracker",
            side_effect=ImportError("simulated missing ultralytics"),
        ),
        pytest.raises(RuntimeError, match="Ultralytics backend requested"),
    ):
        create_person_tracker(Settings(vision_backend="ultralytics_yolo_botsort"))


def test_settings_default_vision_backend_is_hog() -> None:
    assert Settings().vision_backend == "hog"
