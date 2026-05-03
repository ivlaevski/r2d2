"""Target lock and selection tests."""

from __future__ import annotations

from contracts.perception import BoundingBox, TrackedPerson
from infrastructure.config import Settings
from perception.target_selector import TargetSelector


def _tp(
    *,
    tid: int | None,
    x: int,
    w: int,
    h: int,
    conf: float,
    off: float,
    backend: str = "test",
) -> TrackedPerson:
    return TrackedPerson(
        track_id=tid,
        bbox=BoundingBox(x=x, y=0, width=w, height=h),
        confidence=conf,
        horizontal_offset=off,
        approximate_distance_m=2.0,
        backend=backend,
    )


def test_selects_center_weighted_person() -> None:
    s = Settings(target_lock_max_lost_frames=15)
    sel = TargetSelector(s)
    left = _tp(tid=1, x=50, w=40, h=100, conf=0.9, off=-0.7)
    center = _tp(tid=2, x=300, w=40, h=100, conf=0.6, off=0.05)
    obs, lock = sel.select([left, center], frame_width=640, frame_height=480)
    assert obs.target_detected is True
    assert obs.track_id == 2
    assert lock.locked is True


def test_keeps_locked_track() -> None:
    s = Settings(target_lock_max_lost_frames=15)
    sel = TargetSelector(s)
    a = _tp(tid=10, x=100, w=50, h=120, conf=0.5, off=-0.4)
    b = _tp(tid=20, x=400, w=50, h=120, conf=0.99, off=0.5)
    sel.select([a, b], frame_width=640, frame_height=480)
    obs2, _ = sel.select([a, b], frame_width=640, frame_height=480)
    assert obs2.track_id == 20


def test_does_not_switch_to_higher_score_while_locked() -> None:
    s = Settings(target_lock_max_lost_frames=15)
    sel = TargetSelector(s)
    locked = _tp(tid=1, x=150, w=40, h=100, conf=0.95, off=0.0)
    other = _tp(tid=2, x=310, w=40, h=100, conf=0.5, off=0.0)
    sel.select([locked, other], frame_width=640, frame_height=480)
    boosted = _tp(tid=2, x=310, w=40, h=100, conf=0.99, off=0.0)
    obs, _ = sel.select([locked, boosted], frame_width=640, frame_height=480)
    assert obs.track_id == 1


def test_marks_target_lost_after_max_frames() -> None:
    s = Settings(target_lock_max_lost_frames=3)
    sel = TargetSelector(s)
    p = _tp(tid=5, x=200, w=50, h=100, conf=0.9, off=0.0)
    sel.select([p], frame_width=640, frame_height=480)
    obs1, _ = sel.select([], frame_width=640, frame_height=480)
    obs2, _ = sel.select([], frame_width=640, frame_height=480)
    assert obs1.target_detected is True
    assert obs2.target_detected is True
    obs_final, lock_final = sel.select([], frame_width=640, frame_height=480)
    assert obs_final.target_detected is False
    assert lock_final.locked is False


def test_reset_clears_lock() -> None:
    s = Settings(target_lock_max_lost_frames=15)
    sel = TargetSelector(s)
    t1 = _tp(tid=1, x=100, w=40, h=90, conf=0.8, off=-0.2)
    sel.select([t1], frame_width=640, frame_height=480)
    sel.reset()
    t2 = _tp(tid=2, x=300, w=40, h=90, conf=0.7, off=0.0)
    obs, _ = sel.select([t2], frame_width=640, frame_height=480)
    assert obs.track_id == 2
