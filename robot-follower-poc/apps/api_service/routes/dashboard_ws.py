"""WebSocket stream of ``RobotStatus`` for the dashboard (JSON per tick)."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["dashboard"])


@router.websocket("/ws/dashboard")
async def dashboard_robot_status(websocket: WebSocket) -> None:
    """Push ``GET /status``-equivalent JSON several times per second."""

    await websocket.accept()
    robot = websocket.app.state.robot
    try:
        while True:
            await websocket.send_json(robot.get_status().model_dump(mode="json"))
            await asyncio.sleep(0.2)
    except WebSocketDisconnect:
        return
