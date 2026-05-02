"""Health and status routes."""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(tags=["status"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/status")
def status(request: Request) -> dict[str, object]:
    robot = request.app.state.robot
    return robot.get_status().model_dump(mode="json")
