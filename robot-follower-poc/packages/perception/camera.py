"""OpenCV camera capture wrapper."""

from __future__ import annotations

from collections.abc import Iterator

import cv2
import numpy as np
from numpy.typing import NDArray

from infrastructure.config import Settings


class CameraCapture:
    """Context-managed USB / built-in camera using OpenCV."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> None:
        """Open the camera device."""

        self._cap = cv2.VideoCapture(self._settings.camera_index, cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            raise RuntimeError(
                f"Cannot open camera index {self._settings.camera_index}. "
                "Check device permissions and index in .env.",
            )
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(self._settings.camera_width))
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(self._settings.camera_height))

    def close(self) -> None:
        """Release the camera."""

        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def read_frame(self) -> NDArray[np.uint8] | None:
        """Return BGR frame or None on failure."""

        if self._cap is None:
            return None
        ok, frame = self._cap.read()
        if not ok or frame is None:
            return None
        return frame

    def frames(self) -> Iterator[NDArray[np.uint8]]:
        """Infinite iterator of frames (caller controls break)."""

        while True:
            f = self.read_frame()
            if f is None:
                break
            yield f

    def __enter__(self) -> CameraCapture:
        self.open()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()
