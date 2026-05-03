"""Audio ingress, ElevenLabs conversation status, and transcript APIs."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from audio.command_catalog import AUDIO_COMMANDS
from contracts.audio import TranscriptListResponse

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


@router.get("/status")
def audio_conversation_status(request: Request) -> dict[str, object]:
    """ElevenLabs / audio backend status (no secrets)."""

    robot = request.app.state.robot
    return robot.audio_backend.status().model_dump(mode="json")


@router.get("/transcript")
def audio_transcript(
    request: Request,
    limit: int | None = Query(default=None, ge=1, le=2000),
) -> dict[str, object]:
    """Recent transcript lines (newest last)."""

    robot = request.app.state.robot
    items = robot.transcript_store.list(limit=limit)
    return TranscriptListResponse(items=items).model_dump(mode="json")


@router.post("/transcript/clear")
def audio_transcript_clear(request: Request) -> dict[str, object]:
    robot = request.app.state.robot
    robot.transcript_store.clear()
    return {"cleared": True}


@router.post("/conversation/start")
def audio_conversation_start(request: Request) -> dict[str, object]:
    robot = request.app.state.robot
    if not robot.settings.elevenlabs_audio_enabled:
        raise HTTPException(status_code=400, detail="ElevenLabs audio is disabled in settings.")
    try:
        robot.audio_backend.start()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return robot.audio_backend.status().model_dump(mode="json")


@router.post("/conversation/stop")
def audio_conversation_stop(request: Request) -> dict[str, object]:
    robot = request.app.state.robot
    robot.audio_backend.stop()
    return robot.audio_backend.status().model_dump(mode="json")
