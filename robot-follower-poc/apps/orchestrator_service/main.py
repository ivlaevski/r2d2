"""Run the perception–behavior–motion control loop (optional API in-process)."""

from __future__ import annotations

import argparse
import threading
import time

import numpy as np
import uvicorn
from dotenv import load_dotenv

from apps.api_service.app import create_app
from contracts.perception import PerceptionFrameResult, TargetObservation
from infrastructure.config import Settings
from infrastructure.logging import configure_logging, get_logger
from infrastructure.robot_application import RobotApplication
from perception.camera import CameraCapture
from perception.person_detector import HOGPersonDetector, PlaceholderPersonDetector
from perception.pipeline import PerceptionPipeline

_LOG = get_logger(__name__)


def _empty_perception(settings: Settings) -> PerceptionFrameResult:
    return PerceptionFrameResult(
        frame_id=0,
        timestamp_s=time.monotonic(),
        frame_width=settings.camera_width,
        frame_height=settings.camera_height,
        primary_target=TargetObservation(target_detected=False),
    )


def _start_api_background(robot: RobotApplication, settings: Settings) -> None:
    app = create_app(robot)
    cfg = uvicorn.Config(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )
    server = uvicorn.Server(cfg)

    def _run() -> None:
        import asyncio

        asyncio.run(server.serve())

    threading.Thread(target=_run, name="uvicorn-api", daemon=True).start()
    time.sleep(0.4)
    _LOG.info("API listening on http://%s:%s", settings.api_host, settings.api_port)


def main(argv: list[str] | None = None) -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Robot follower orchestrator (PoC).")
    parser.add_argument(
        "--with-api",
        action="store_true",
        help="Host FastAPI in a background thread using the same RobotApplication instance.",
    )
    parser.add_argument(
        "--no-camera",
        action="store_true",
        help="Skip OpenCV capture; perception will report no target.",
    )
    args = parser.parse_args(argv)

    settings = Settings()
    configure_logging(settings.log_level, service_name="orchestrator")
    robot = RobotApplication(settings)

    if args.with_api:
        _start_api_background(robot, settings)

    if args.no_camera:
        pipeline: PerceptionPipeline | None = None
        camera: CameraCapture | None = None
    else:
        detector = HOGPersonDetector(settings)
        pipeline = PerceptionPipeline(settings, detector)
        camera = CameraCapture(settings)
        try:
            camera.open()
        except Exception as exc:  # noqa: BLE001 — PoC: degrade to placeholder
            _LOG.warning("Camera unavailable (%s); using placeholder perception.", exc)
            pipeline = PerceptionPipeline(settings, PlaceholderPersonDetector())
            if camera is not None:
                camera.close()
            camera = None

    _LOG.info("Orchestrator running. Ctrl+C to exit.")
    try:
        while True:
            if pipeline is not None and camera is not None:
                frame = camera.read_frame()
                if frame is None:
                    robot.ingest_perception(_empty_perception(settings))
                else:
                    robot.ingest_perception(pipeline.process_frame(frame))
            elif pipeline is not None:
                black = np.zeros(
                    (settings.camera_height, settings.camera_width, 3),
                    dtype=np.uint8,
                )
                robot.ingest_perception(pipeline.process_frame(black))
            else:
                robot.ingest_perception(_empty_perception(settings))

            status = robot.tick()
            _LOG.debug(
                "mode=%s motion=%s target=%s",
                status.mode.value,
                status.last_motion_command.value,
                status.target is not None,
            )
            time.sleep(settings.orchestrator_period_s)
    except KeyboardInterrupt:
        _LOG.info("Orchestrator stopped.")
    finally:
        if camera is not None:
            camera.close()


if __name__ == "__main__":
    main()
