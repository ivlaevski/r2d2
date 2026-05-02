"""Perception pipeline result contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TargetObservation(BaseModel):
    """Single tracked person hypothesis in image space."""

    target_detected: bool = False
    bbox_x: int = 0
    bbox_y: int = 0
    bbox_width: int = 0
    bbox_height: int = 0
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    horizontal_offset: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Normalized offset: negative=left, positive=right.",
    )
    approximate_distance_m: float | None = Field(default=None, ge=0.0)


class PerceptionFrameResult(BaseModel):
    """One frame of perception output."""

    frame_id: int = 0
    timestamp_s: float = 0.0
    frame_width: int = 0
    frame_height: int = 0
    primary_target: TargetObservation = Field(default_factory=TargetObservation)
