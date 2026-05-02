"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api_service.routes import audio as audio_routes
from apps.api_service.routes import commands as commands_routes
from apps.api_service.routes import status as status_routes
from infrastructure.robot_application import RobotApplication


def create_app(robot: RobotApplication) -> FastAPI:
    """Build the API app with shared ``RobotApplication`` state."""

    app = FastAPI(title="Robot Follower PoC API", version="0.1.0")
    app.state.robot = robot

    origins = [o.strip() for o in robot.settings.api_cors_origins.split(",") if o.strip()]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(status_routes.router)
    app.include_router(commands_routes.router)
    app.include_router(audio_routes.router)
    return app
