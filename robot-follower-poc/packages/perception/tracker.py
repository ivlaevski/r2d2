"""Select a primary target from per-frame detections (PoC: largest area)."""

from __future__ import annotations

from perception.person_detector import Detection


def select_primary_target(detections: list[Detection]) -> Detection | None:
    """Pick the detection with largest bounding-box area."""

    if not detections:
        return None
    return max(detections, key=lambda d: d.width * d.height)
