"""Ultralytics result conversion without loading YOLO weights."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
from integrations.ultralytics_yolo_botsort.ultralytics_person_tracker import (
    tracked_people_from_track_result,
)

from infrastructure.config import Settings
from perception.distance_estimator import DistanceEstimator


class _FakeBoxes:
    def __init__(self) -> None:
        rows = [[100.0, 50.0, 200.0, 400.0], [10.0, 10.0, 30.0, 40.0]]
        self.xyxy = np.array(rows, dtype=np.float32)
        self.conf = np.array([0.9, 0.8], dtype=np.float32)
        self.cls = np.array([0.0, 15.0], dtype=np.float32)
        self.id = np.array([2.0, 9.0], dtype=np.float32)

    def __len__(self) -> int:
        return int(self.xyxy.shape[0])


def test_tracked_people_from_fake_track_result_filters_non_person() -> None:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    res = SimpleNamespace(boxes=_FakeBoxes())
    out = tracked_people_from_track_result(
        frame_bgr=frame,
        track_result=res,
        backend_label="ultralytics_yolo_botsort",
        distance=DistanceEstimator(Settings()),
    )
    assert len(out) == 1
    assert out[0].track_id == 2
    assert out[0].bbox.width > 0
    assert out[0].backend == "ultralytics_yolo_botsort"
