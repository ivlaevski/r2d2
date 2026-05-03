"""HOG-based person tracker implementing ``PersonTracker`` (no persistent IDs)."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from contracts.perception import BoundingBox, TrackedPerson
from infrastructure.config import Settings
from perception.distance_estimator import DistanceEstimator
from perception.person_detector import HOGPersonDetector


class HOGPersonTracker:
    """Adapts ``HOGPersonDetector`` to the ``PersonTracker`` protocol."""

    def __init__(self, settings: Settings) -> None:
        self._detector = HOGPersonDetector(settings)
        self._distance = DistanceEstimator(settings)

    def update(self, frame: NDArray[np.uint8]) -> list[TrackedPerson]:
        h, w = frame.shape[:2]
        cx_frame = w / 2.0
        half_w = w / 2.0
        out: list[TrackedPerson] = []
        for det in self._detector.detect(frame):
            cx = det.x + det.width / 2.0
            norm = float((cx - cx_frame) / half_w) if half_w > 0 else 0.0
            norm = max(-1.0, min(1.0, norm))
            dist = self._distance.estimate(det.height)
            out.append(
                TrackedPerson(
                    track_id=None,
                    bbox=BoundingBox(
                        x=det.x,
                        y=det.y,
                        width=det.width,
                        height=det.height,
                    ),
                    confidence=det.confidence,
                    horizontal_offset=norm,
                    approximate_distance_m=dist,
                    backend="hog",
                ),
            )
        return out


class PlaceholderPersonTracker:
    """No-op tracker for headless runs or missing camera."""

    def update(self, frame: NDArray[np.uint8]) -> list[TrackedPerson]:
        return []
