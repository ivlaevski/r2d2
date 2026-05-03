"""Ensure default perception stack does not require optional vision backends."""

from __future__ import annotations


def test_import_perception_package() -> None:
    import perception

    assert perception.PerceptionPipeline is not None
    assert perception.HOGPersonTracker is not None


def test_import_infrastructure_perception_factory() -> None:
    from infrastructure import perception_factory

    assert perception_factory.create_person_tracker is not None


def test_orchestrator_main_importable_without_ultralytics() -> None:
    import apps.orchestrator_service.main as orch_main

    assert callable(orch_main.main)
