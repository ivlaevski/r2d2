"""Construct ``PersonTracker`` implementations from ``Settings`` (lazy optional backends)."""

from __future__ import annotations

from infrastructure.config import Settings
from perception.hog_person_tracker import HOGPersonTracker
from perception.person_tracker import PersonTracker

_MISSING_ULTRALYTICS_MSG = (
    "Ultralytics backend requested but optional dependency is not installed. "
    "Run: pip install -e .[vision-ultralytics]"
)


def _default_tracker_for_backend(backend: str) -> str:
    if backend == "ultralytics_yolo_bytetrack":
        return "bytetrack.yaml"
    return "botsort.yaml"


def create_person_tracker(settings: Settings) -> PersonTracker:
    """Build the configured tracker; Ultralytics backends import lazily."""

    backend = settings.vision_backend
    if backend == "hog":
        return HOGPersonTracker(settings)

    if backend in ("ultralytics_yolo_botsort", "ultralytics_yolo_bytetrack"):
        tracker_yaml = settings.yolo_tracker or _default_tracker_for_backend(backend)
        try:
            from integrations.ultralytics_yolo_botsort.ultralytics_person_tracker import (
                UltralyticsPersonTracker,
            )

            return UltralyticsPersonTracker(settings, tracker_yaml=tracker_yaml)
        except ImportError as exc:
            raise RuntimeError(_MISSING_ULTRALYTICS_MSG) from exc

    raise ValueError(f"Unknown vision backend: {backend!r}")
