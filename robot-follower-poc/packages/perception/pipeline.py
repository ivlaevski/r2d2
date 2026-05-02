"""Compose camera, detector, tracker, and distance into ``PerceptionFrameResult``."""

from __future__ import annotations

import time

import numpy as np
from numpy.typing import NDArray

from contracts.perception import PerceptionFrameResult, TargetObservation
from infrastructure.config import Settings
from perception.distance_estimator import DistanceEstimator
from perception.person_detector import PersonDetector
from perception.tracker import select_primary_target


class PerceptionPipeline:
    """Runs one frame through detector + geometry helpers."""

    def __init__(
        self,
        settings: Settings,
        detector: PersonDetector,
    ) -> None:
        self._settings = settings
        self._detector = detector
        self._distance = DistanceEstimator(settings)
        self._frame_id = 0

    def process_frame(self, frame_bgr: NDArray[np.uint8]) -> PerceptionFrameResult:
        """Detect person, estimate offset and distance."""

        h, w = frame_bgr.shape[:2]
        dets = self._detector.detect(frame_bgr)
        primary = select_primary_target(dets)

        if primary is None:
            obs = TargetObservation(target_detected=False)
        else:
            cx = primary.x + primary.width / 2.0
            norm = (cx - (w / 2.0)) / (w / 2.0)
            norm = float(max(-1.0, min(1.0, norm)))
            dist = self._distance.estimate(primary.height)
            obs = TargetObservation(
                target_detected=True,
                bbox_x=primary.x,
                bbox_y=primary.y,
                bbox_width=primary.width,
                bbox_height=primary.height,
                confidence=primary.confidence,
                horizontal_offset=norm,
                approximate_distance_m=dist,
            )

        self._frame_id += 1
        return PerceptionFrameResult(
            frame_id=self._frame_id,
            timestamp_s=time.monotonic(),
            frame_width=int(w),
            frame_height=int(h),
            primary_target=obs,
        )
