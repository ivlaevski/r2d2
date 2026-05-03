"""HOG ``PersonTracker`` adapter tests."""

from __future__ import annotations

import numpy as np

from infrastructure.config import Settings
from perception.hog_person_tracker import HOGPersonTracker


def test_hog_tracker_returns_list_and_hog_metadata() -> None:
    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    tracker = HOGPersonTracker(Settings())
    tracks = tracker.update(frame)
    assert isinstance(tracks, list)
    for t in tracks:
        assert t.backend == "hog"
        assert t.track_id is None
        assert 0.0 <= t.confidence <= 1.0
