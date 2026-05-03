"""Compose camera, tracker, target selection, and distance into ``PerceptionFrameResult``."""

from __future__ import annotations

import time

import numpy as np
from numpy.typing import NDArray

from contracts.perception import PerceptionFrameResult, TrackedPerson
from infrastructure.config import Settings
from perception.person_tracker import PersonTracker
from perception.target_selector import TargetSelector
from perception.thumbnails import upper_body_thumbnail_jpeg_b64


class PerceptionPipeline:
    """Runs one frame through tracker + target lock + contracts."""

    def __init__(
        self,
        settings: Settings,
        person_tracker: PersonTracker,
        target_selector: TargetSelector | None = None,
    ) -> None:
        self._settings = settings
        self._tracker = person_tracker
        self._selector = target_selector or TargetSelector(settings)
        self._frame_id = 0

    def reset_target_lock(self) -> None:
        """Clear target lock (e.g. after mode changes)."""

        self._selector.reset()

    def process_frame(self, frame_bgr: NDArray[np.uint8]) -> PerceptionFrameResult:
        """Run tracker and primary-target selection."""

        h, w = frame_bgr.shape[:2]
        tracks = self._tracker.update(frame_bgr)
        obs, lock = self._selector.select(tracks, frame_width=int(w), frame_height=int(h))

        sorted_tracks = sorted(tracks, key=lambda p: p.bbox.x + p.bbox.width * 0.5)
        tracked_with_thumbs: list[TrackedPerson] = []
        max_thumb = int(self._settings.dashboard_max_thumbnail_tracks)
        for i, person in enumerate(sorted_tracks):
            b64: str | None = None
            if (
                max_thumb > 0
                and i < max_thumb
                and self._settings.dashboard_target_thumbnails_enabled
            ):
                b64 = upper_body_thumbnail_jpeg_b64(frame_bgr, person.bbox)
            tracked_with_thumbs.append(person.model_copy(update={"face_thumbnail_jpeg_b64": b64}))

        self._frame_id += 1
        return PerceptionFrameResult(
            frame_id=self._frame_id,
            timestamp_s=time.monotonic(),
            frame_width=int(w),
            frame_height=int(h),
            primary_target=obs,
            target_lock=lock,
            tracked_people=tracked_with_thumbs,
        )
