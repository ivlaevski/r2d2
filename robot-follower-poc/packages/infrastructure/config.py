"""Application configuration via environment and .env files."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration; avoids magic numbers in business logic."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Camera
    camera_index: int = Field(default=0, ge=0)
    camera_width: int = Field(default=640, ge=160)
    camera_height: int = Field(default=480, ge=120)

    # Perception / HOG
    hog_win_stride: int = Field(default=4, ge=1)
    hog_padding: int = Field(default=8, ge=0)
    hog_scale: float = Field(default=1.05, gt=1.0)
    hog_hit_threshold: float = Field(default=0.0, ge=0.0)

    # Distance: distance_m = calibration_constant_m_px / bbox_height_pixels
    calibration_constant_m_px: float = Field(default=1.65, gt=0.0)

    # Behavior
    target_lost_timeout_s: float = Field(default=2.0, gt=0.0)

    # Motion planner
    desired_distance_m: float = Field(default=2.0, ge=0.1, le=50.0)
    distance_too_far_m: float = Field(default=2.5, ge=0.1)
    distance_too_close_m: float = Field(default=1.2, ge=0.1)
    horizontal_offset_threshold: float = Field(default=0.15, ge=0.0, le=1.0)

    # Simulated motor
    motor_max_speed: float = Field(default=1.0, gt=0.0)
    motor_command_timeout_s: float = Field(default=0.5, gt=0.0)
    motor_log_interval_s: float = Field(default=0.25, ge=0.0)

    # API
    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8000, ge=1, le=65535)
    robot_api_base: str = "http://127.0.0.1:8000"
    # Comma-separated browser origins allowed to call the API (dashboard dev server, etc.).
    api_cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:4173,http://127.0.0.1:4173"
    )

    # Logging
    log_level: str = "INFO"

    # Orchestrator loop
    orchestrator_period_s: float = Field(default=0.05, gt=0.0)
    status_log_interval_s: float = Field(default=1.0, ge=0.1)

    # Audio ingress (console / future ASR) — TTL without heartbeat clears “listening”
    audio_listening_ttl_s: float = Field(default=15.0, gt=0.0)
