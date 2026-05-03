"""Perception pipeline result contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Axis-aligned box in pixel coordinates (top-left origin)."""

    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0


class TrackedPerson(BaseModel):
    """One person hypothesis from a vision backend (tracker output)."""

    track_id: int | None = None
    bbox: BoundingBox
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    horizontal_offset: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Normalized offset: negative=left, positive=right.",
    )
    approximate_distance_m: float | None = Field(default=None, ge=0.0)
    backend: str = Field(
        default="unknown",
        description="Logical backend id (e.g. hog, ultralytics_yolo_botsort).",
    )
    face_thumbnail_jpeg_b64: str | None = Field(
        default=None,
        description="Optional small JPEG (base64) of the upper-body crop for dashboards.",
    )


class TargetLock(BaseModel):
    """Target lock bookkeeping for perception (API / telemetry)."""

    locked_track_id: int | None = None
    lost_frames: int = Field(default=0, ge=0)
    locked: bool = False


class TargetObservation(BaseModel):
    """Primary follow target after selection / locking."""

    target_detected: bool = False
    bbox: BoundingBox = Field(default_factory=BoundingBox)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    horizontal_offset: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Normalized offset: negative=left, positive=right.",
    )
    approximate_distance_m: float | None = Field(default=None, ge=0.0)
    track_id: int | None = None
    backend: str = "hog"


class PerceptionFrameResult(BaseModel):
    """One frame of perception output."""

    frame_id: int = 0
    timestamp_s: float = 0.0
    frame_width: int = 0
    frame_height: int = 0
    primary_target: TargetObservation = Field(default_factory=TargetObservation)
    target_lock: TargetLock = Field(default_factory=TargetLock)
    tracked_people: list[TrackedPerson] = Field(
        default_factory=list,
        description="All tracker hypotheses this frame (sorted L→R for UI in pipeline).",
    )
