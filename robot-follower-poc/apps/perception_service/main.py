"""Run camera capture and person detection (logging / diagnostics)."""

from __future__ import annotations

import time

from dotenv import load_dotenv

from infrastructure.config import Settings
from infrastructure.logging import configure_logging, get_logger
from perception.camera import CameraCapture
from perception.person_detector import HOGPersonDetector
from perception.pipeline import PerceptionPipeline

_LOG = get_logger(__name__)


def main() -> None:
    load_dotenv()
    settings = Settings()
    configure_logging(settings.log_level, service_name="perception")
    detector = HOGPersonDetector(settings)
    pipeline = PerceptionPipeline(settings, detector)
    with CameraCapture(settings) as cam:
        t0 = time.monotonic()
        n = 0
        while True:
            frame = cam.read_frame()
            if frame is None:
                _LOG.warning("Frame grab failed; exiting.")
                break
            result = pipeline.process_frame(frame)
            n += 1
            if n % 30 == 0:
                fps = n / max(1e-6, (time.monotonic() - t0))
                tgt = result.primary_target
                _LOG.info(
                    "fps=%.1f detected=%s conf=%.2f offset=%.2f dist=%s",
                    fps,
                    tgt.target_detected,
                    tgt.confidence,
                    tgt.horizontal_offset,
                    tgt.approximate_distance_m,
                )


if __name__ == "__main__":
    main()
