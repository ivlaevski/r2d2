"""Target lock and selection from per-frame tracked people."""

from __future__ import annotations

from contracts.perception import BoundingBox, TargetLock, TargetObservation, TrackedPerson
from infrastructure.config import Settings


def _bbox_iou(a: BoundingBox, b: BoundingBox) -> float:
    ax2, ay2 = a.x + a.width, a.y + a.height
    bx2, by2 = b.x + b.width, b.y + b.height
    inter_x1 = max(a.x, b.x)
    inter_y1 = max(a.y, b.y)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    iw = max(0, inter_x2 - inter_x1)
    ih = max(0, inter_y2 - inter_y1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(1, a.width * a.height)
    area_b = max(1, b.width * b.height)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _score_center_weighted(person: TrackedPerson) -> float:
    """Higher is better: confident hypotheses near the optical center."""

    return float(person.confidence) / (1.0 + abs(person.horizontal_offset))


def _tracked_to_observation(person: TrackedPerson) -> TargetObservation:
    return TargetObservation(
        target_detected=True,
        bbox=person.bbox.model_copy(),
        confidence=person.confidence,
        horizontal_offset=person.horizontal_offset,
        approximate_distance_m=person.approximate_distance_m,
        track_id=person.track_id,
        backend=person.backend,
    )


class TargetSelector:
    """
    Picks and locks a primary target.

    With persistent ``track_id`` (e.g. Ultralytics), locks by id. With only
    ``track_id is None`` (HOG), locks by best IoU overlap with the last locked box.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._locked_track_id: int | None = None
        self._lock_by_bbox_only: bool = False
        self._lost_frames: int = 0
        self._last_good: TargetObservation | None = None
        self._bbox_iou_threshold: float = 0.12

    def reset(self) -> None:
        self._locked_track_id = None
        self._lock_by_bbox_only = False
        self._lost_frames = 0
        self._last_good = None

    def select(
        self,
        tracks: list[TrackedPerson],
        *,
        frame_width: int,
        frame_height: int,
    ) -> tuple[TargetObservation, TargetLock]:
        """Return primary observation and lock state for this frame."""

        _ = frame_width, frame_height  # reserved for future geometry rules

        if not tracks:
            return self._handle_no_detections()

        if self._last_good is None:
            return self._pick_initial_or_unlocked(tracks)

        matched = self._find_locked_match(tracks)
        if matched is not None:
            self._lost_frames = 0
            obs = _tracked_to_observation(matched)
            self._last_good = obs
            lock = TargetLock(
                locked_track_id=self._locked_track_id,
                lost_frames=0,
                locked=True,
            )
            return obs, lock

        self._lost_frames += 1
        if self._lost_frames >= self._settings.target_lock_max_lost_frames:
            self.reset()
            return (
                TargetObservation(target_detected=False),
                TargetLock(locked=False, lost_frames=0, locked_track_id=None),
            )

        assert self._last_good is not None
        grace = self._last_good.model_copy(update={"target_detected": True})
        lock = TargetLock(
            locked_track_id=self._locked_track_id,
            lost_frames=self._lost_frames,
            locked=True,
        )
        return grace, lock

    def _handle_no_detections(self) -> tuple[TargetObservation, TargetLock]:
        if self._last_good is None or not self._last_good.target_detected:
            return (
                TargetObservation(target_detected=False),
                TargetLock(locked=False, lost_frames=0, locked_track_id=None),
            )

        self._lost_frames += 1
        if self._lost_frames >= self._settings.target_lock_max_lost_frames:
            self.reset()
            return (
                TargetObservation(target_detected=False),
                TargetLock(locked=False, lost_frames=0, locked_track_id=None),
            )

        assert self._last_good is not None
        grace = self._last_good.model_copy(update={"target_detected": True})
        lock = TargetLock(
            locked_track_id=self._locked_track_id,
            lost_frames=self._lost_frames,
            locked=True,
        )
        return grace, lock

    def _pick_initial_or_unlocked(
        self,
        tracks: list[TrackedPerson],
    ) -> tuple[TargetObservation, TargetLock]:
        best = max(tracks, key=_score_center_weighted)
        obs = _tracked_to_observation(best)
        self._last_good = obs
        self._locked_track_id = best.track_id
        self._lock_by_bbox_only = best.track_id is None
        self._lost_frames = 0
        lock = TargetLock(locked_track_id=self._locked_track_id, lost_frames=0, locked=True)
        return obs, lock

    def _find_locked_match(self, tracks: list[TrackedPerson]) -> TrackedPerson | None:
        if self._lock_by_bbox_only or self._locked_track_id is None:
            if self._last_good is None:
                return None
            ref = self._last_good.bbox
            best_p: TrackedPerson | None = None
            best_iou = 0.0
            for p in tracks:
                iou = _bbox_iou(ref, p.bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_p = p
            if best_p is not None and best_iou >= self._bbox_iou_threshold:
                return best_p
            return None

        for p in tracks:
            if p.track_id == self._locked_track_id:
                return p
        return None
