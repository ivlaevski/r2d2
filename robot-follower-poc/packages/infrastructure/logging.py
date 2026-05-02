"""Structured logging setup for services."""

from __future__ import annotations

import logging
import sys
from typing import Any


def configure_logging(level: str = "INFO", service_name: str = "robot") -> None:
    """Configure root logger once per process (idempotent enough for PoC)."""

    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level.upper())
        return

    logging.basicConfig(
        level=level.upper(),
        format=f"%(asctime)s [%(levelname)s] {service_name} %(name)s: %(message)s",
        stream=sys.stdout,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger."""

    return logging.getLogger(name)


class JsonLogFormatter(logging.Formatter):
    """Optional JSON lines formatter for future log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        import json

        return json.dumps(payload, default=str)
