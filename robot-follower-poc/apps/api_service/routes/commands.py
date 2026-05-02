"""Command routes — thin handlers delegating to ``RobotApplication``."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from contracts.commands import HighLevelCommand, HighLevelCommandType

router = APIRouter(prefix="/commands", tags=["commands"])


class CommandRequest(BaseModel):
    """Generic command body for ``POST /commands``."""

    command: HighLevelCommandType
    distance_m: float | None = Field(default=None, ge=0.1, le=50.0)


class DistanceBody(BaseModel):
    """Body for ``POST /commands/distance``."""

    distance_m: float = Field(ge=0.1, le=50.0)


def _apply(request: Request, cmd: HighLevelCommand) -> dict[str, object]:
    robot = request.app.state.robot
    robot.apply_high_level_command(cmd)
    return robot.get_status().model_dump(mode="json")


@router.post("")
def post_command(request: Request, body: CommandRequest) -> dict[str, object]:
    return _apply(
        request,
        HighLevelCommand(command=body.command, distance_m=body.distance_m),
    )


@router.post("/follow")
def follow(request: Request) -> dict[str, object]:
    return _apply(request, HighLevelCommand(command=HighLevelCommandType.FOLLOW))


@router.post("/stay")
def stay(request: Request) -> dict[str, object]:
    return _apply(request, HighLevelCommand(command=HighLevelCommandType.STAY))


@router.post("/stop")
def stop(request: Request) -> dict[str, object]:
    return _apply(request, HighLevelCommand(command=HighLevelCommandType.STOP))


@router.post("/reset")
def reset(request: Request) -> dict[str, object]:
    return _apply(request, HighLevelCommand(command=HighLevelCommandType.RESET))


@router.post("/distance")
def distance(request: Request, body: DistanceBody) -> dict[str, object]:
    return _apply(
        request,
        HighLevelCommand(
            command=HighLevelCommandType.CHANGE_DISTANCE,
            distance_m=body.distance_m,
        ),
    )
