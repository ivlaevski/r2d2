"""Distance estimator unit tests."""

from __future__ import annotations

from infrastructure.config import Settings
from perception.distance_estimator import DistanceEstimator


def test_inverse_height_relation() -> None:
    s = Settings(calibration_constant_m_px=1.65)
    est = DistanceEstimator(s)
    d = est.estimate(100)
    assert d is not None
    assert abs(d - 1.65 / 100.0) < 1e-9


def test_invalid_height_returns_none() -> None:
    est = DistanceEstimator(Settings())
    assert est.estimate(0) is None
    assert est.estimate(-5) is None
