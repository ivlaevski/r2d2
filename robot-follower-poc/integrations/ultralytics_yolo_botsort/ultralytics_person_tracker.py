"""Ultralytics YOLO + BoT-SORT / ByteTrack ``PersonTracker`` (optional AGPL dependency)."""

from __future__ import annotations

import logging
import math
import os
from typing import Any

import numpy as np
from numpy.typing import NDArray

from contracts.perception import BoundingBox, TrackedPerson
from infrastructure.config import Settings
from perception.distance_estimator import DistanceEstimator

_LOG = logging.getLogger(__name__)

_COCO_PERSON_CLASS_ID = 0


def tracked_people_from_track_result(
    *,
    frame_bgr: NDArray[np.uint8],
    track_result: object,
    backend_label: str,
    distance: DistanceEstimator,
) -> list[TrackedPerson]:
    """
    Convert a single ultralytics ``track`` result to ``TrackedPerson`` rows.

    ``track_result`` is expected to expose a ``boxes`` attribute compatible with
    Ultralytics (xyxy, conf, cls, id tensors). Used by tests with lightweight fakes.
    """

    _h, w = frame_bgr.shape[:2]
    cx_frame = w / 2.0
    half_w = w / 2.0
    out: list[TrackedPerson] = []

    boxes = getattr(track_result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return out

    xyxy = boxes.xyxy
    confs = boxes.conf
    clss = boxes.cls
    ids = getattr(boxes, "id", None)

    def _to_numpy_2d(t: object) -> np.ndarray:
        if hasattr(t, "detach"):
            t = t.detach()
        if hasattr(t, "cpu"):
            t = t.cpu()
        return np.asarray(t, dtype=np.float64)

    xyxy_np = _to_numpy_2d(xyxy)
    conf_np = np.asarray(confs).reshape(-1)
    cls_np = np.asarray(clss, dtype=np.int64).reshape(-1)
    id_np: np.ndarray | None = None if ids is None else _to_numpy_2d(ids).reshape(-1)

    n = int(min(xyxy_np.shape[0], len(boxes)))
    for i in range(n):
        cls_int = int(cls_np[i]) if i < cls_np.size else _COCO_PERSON_CLASS_ID + 1
        if cls_int != _COCO_PERSON_CLASS_ID:
            continue

        row = xyxy_np[i]
        x1f, y1f, x2f, y2f = float(row[0]), float(row[1]), float(row[2]), float(row[3])

        bw = max(1, int(round(x2f - x1f)))
        bh = max(1, int(round(y2f - y1f)))
        xi = int(round(x1f))
        yi = int(round(y1f))

        confidence = float(conf_np[i]) if i < conf_np.size else 0.0
        confidence = max(0.0, min(1.0, confidence))

        cx = xi + bw / 2.0
        norm = float((cx - cx_frame) / half_w) if half_w > 0 else 0.0
        norm = max(-1.0, min(1.0, norm))

        tid: int | None = None
        if id_np is not None and i < id_np.size:
            raw = float(id_np[i])
            if not math.isnan(raw):
                try:
                    tid = int(raw)
                except (TypeError, ValueError):
                    tid = None

        dist = distance.estimate(bh)
        out.append(
            TrackedPerson(
                track_id=tid,
                bbox=BoundingBox(x=xi, y=yi, width=bw, height=bh),
                confidence=confidence,
                horizontal_offset=norm,
                approximate_distance_m=dist,
                backend=backend_label,
            ),
        )
    return out


class UltralyticsPersonTracker:
    """YOLO ``track`` pipeline with configurable BoT-SORT / ByteTrack YAML."""

    def __init__(self, settings: Settings, *, tracker_yaml: str) -> None:
        self._settings = settings
        self._tracker_yaml = tracker_yaml
        self._distance = DistanceEstimator(settings)
        self._model: Any = None

        if os.environ.get("PYTEST_CURRENT_TEST"):
            _LOG.info(
                "Skipping YOLO model load during pytest (avoids weight downloads); "
                "tracker will return no detections.",
            )
            return

        try:
            from ultralytics import YOLO
        except ImportError as exc:
            _LOG.exception("Ultralytics is not installed")
            raise ImportError(
                "optional ultralytics package is missing; install vision-ultralytics extra",
            ) from exc

        try:
            self._model = YOLO(settings.yolo_model)
            _LOG.info(
                "Loaded YOLO model %s tracker=%s device=%s",
                settings.yolo_model,
                tracker_yaml,
                settings.yolo_device,
            )
        except Exception:
            _LOG.exception("Failed to load YOLO model %s", settings.yolo_model)
            raise

    def update(self, frame: NDArray[np.uint8]) -> list[TrackedPerson]:
        if self._model is None:
            return []

        try:
            results = self._model.track(
                source=frame,
                persist=self._settings.yolo_persist_tracks,
                tracker=self._tracker_yaml,
                conf=self._settings.yolo_confidence,
                iou=self._settings.yolo_iou,
                imgsz=self._settings.yolo_image_size,
                device=self._settings.yolo_device,
                verbose=self._settings.yolo_show_debug,
            )
        except Exception:
            _LOG.exception("YOLO track() failed")
            return []

        if not results:
            return []

        return tracked_people_from_track_result(
            frame_bgr=frame,
            track_result=results[0],
            backend_label=self._settings.vision_backend,
            distance=self._distance,
        )
