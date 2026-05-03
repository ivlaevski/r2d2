"""Small JPEG crops from detection boxes (dashboard / PoC)."""

from __future__ import annotations

import base64

import cv2
import numpy as np
from numpy.typing import NDArray

from contracts.perception import BoundingBox


def upper_body_thumbnail_jpeg_b64(
    frame_bgr: NDArray[np.uint8],
    bbox: BoundingBox,
    *,
    max_side_px: int = 64,
    jpeg_quality: int = 52,
    upper_fraction: float = 0.45,
) -> str | None:
    """Crop the top ``upper_fraction`` of the box, resize, return base64 JPEG or None."""

    if frame_bgr.size == 0:
        return None
    fh, fw = frame_bgr.shape[:2]
    x1 = max(0, int(bbox.x))
    y1 = max(0, int(bbox.y))
    bw = max(1, int(bbox.width))
    bh = max(1, int(bbox.height))
    y2 = min(fh, y1 + int(bh * upper_fraction))
    x2 = min(fw, x1 + bw)
    if y2 <= y1 + 4 or x2 <= x1 + 4:
        return None
    crop = frame_bgr[y1:y2, x1:x2]
    if crop.size == 0:
        return None
    h, w = crop.shape[:2]
    side = max(h, w)
    scale = min(float(max_side_px) / float(side), 1.0)
    if scale < 1.0:
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        crop = cv2.resize(crop, (new_w, new_h), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", crop, (int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)))
    if not ok or buf is None:
        return None
    return base64.b64encode(buf.tobytes()).decode("ascii")
