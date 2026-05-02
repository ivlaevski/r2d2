"""Monocular distance estimation from bounding box height."""

from __future__ import annotations

from infrastructure.config import Settings


class DistanceEstimator:
    """
    Simple calibrated inverse relation:

    ``distance_m = calibration_constant_m_px / bbox_height_pixels``
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def estimate(self, bbox_height_px: int) -> float | None:
        """Return distance in meters or None if height is invalid."""

        if bbox_height_px <= 0:
            return None
        return float(self._settings.calibration_constant_m_px) / float(bbox_height_px)
