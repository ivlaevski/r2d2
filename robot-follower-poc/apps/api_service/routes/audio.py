"""Audio ingress metadata (listening heartbeat, command catalog)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from audio.command_catalog import AUDIO_COMMANDS

router = APIRouter(prefix="/audio", tags=["audio"])


class ListeningBody(BaseModel):
    """Posted by ``audio_service`` while the console / future mic pipeline is active."""

    listening: bool


@router.get("/commands")
def list_audio_commands() -> dict[str, object]:
    """Supported phrases for local console / future ASR (single source of truth)."""

    return {"commands": AUDIO_COMMANDS}


@router.post("/listening")
def report_listening(request: Request, body: ListeningBody) -> dict[str, object]:
    """Update microphone / ingress listening state (requires periodic heartbeat while true)."""

    robot = request.app.state.robot
    robot.set_microphone_listening(body.listening)
    return robot.get_status().model_dump(mode="json")
