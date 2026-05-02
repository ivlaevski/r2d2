"""Person detection abstraction with OpenCV HOG implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import cv2
import numpy as np
from numpy.typing import NDArray

from infrastructure.config import Settings


def _hog_weight_to_score(wt: object) -> float:
    """Normalize HOG ``weights`` entries (scalar or 1-D) to a float score."""

    arr = np.asarray(wt, dtype=np.float64).ravel()
    if arr.size == 0:
        return 0.0
    return float(arr.flat[0])


@dataclass(frozen=True)
class Detection:
    """Raw detector output in pixel coordinates."""

    x: int
    y: int
    width: int
    height: int
    confidence: float


@runtime_checkable
class PersonDetector(Protocol):
    """Pluggable person detector (HOG, MediaPipe, YOLO, etc.)."""

    def detect(self, frame_bgr: NDArray[np.uint8]) -> list[Detection]:
        """Return zero or more person detections."""


class HOGPersonDetector:
    """OpenCV HOGDescriptor default people detector."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._hog = cv2.HOGDescriptor()
        self._hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def detect(self, frame_bgr: NDArray[np.uint8]) -> list[Detection]:
        """Run multiscale HOG detection."""

        win_stride = (self._settings.hog_win_stride, self._settings.hog_win_stride)
        padding = (self._settings.hog_padding, self._settings.hog_padding)
        scale = self._settings.hog_scale
        rects, weights = self._hog.detectMultiScale(
            frame_bgr,
            winStride=win_stride,
            padding=padding,
            scale=scale,
            hitThreshold=self._settings.hog_hit_threshold,
        )
        out: list[Detection] = []
        for (x, y, w, h), wt in zip(rects, weights, strict=True):
            raw = _hog_weight_to_score(wt)
            conf = float(min(1.0, max(0.0, raw)))
            out.append(Detection(int(x), int(y), int(w), int(h), conf))
        return out


class PlaceholderPersonDetector:
    """No-op detector for headless CI or missing camera."""

    def detect(self, frame_bgr: NDArray[np.uint8]) -> list[Detection]:
        return []
