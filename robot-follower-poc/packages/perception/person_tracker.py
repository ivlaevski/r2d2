"""Abstract person tracker: maps a frame to zero or more tracked people."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray

from contracts.perception import TrackedPerson


@runtime_checkable
class PersonTracker(Protocol):
    """Vision-backend-agnostic multi-person tracking for one frame."""

    def update(self, frame: NDArray[np.uint8]) -> list[TrackedPerson]:
        """Run tracking / detection on ``frame`` (BGR, uint8) and return hypotheses."""
