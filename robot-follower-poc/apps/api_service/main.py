"""Run the HTTP API service (Uvicorn)."""

from __future__ import annotations

import uvicorn
from dotenv import load_dotenv

from apps.api_service.app import create_app
from infrastructure.config import Settings
from infrastructure.logging import configure_logging
from infrastructure.robot_application import RobotApplication


def main() -> None:
    load_dotenv()
    settings = Settings()
    configure_logging(settings.log_level, service_name="api")
    robot = RobotApplication(settings)
    app = create_app(robot)
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
        reload=False,
    )


if __name__ == "__main__":
    main()
