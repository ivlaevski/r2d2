# Ultralytics YOLO + BoT-SORT / ByteTrack (optional)

This integration provides `UltralyticsPersonTracker`, a `PersonTracker` implementation backed by the **ultralytics** Python package using `YOLO.track(..., persist=True)` with **BoT-SORT** or **ByteTrack** YAML configs.

## License

The **robot-follower-poc** core is MIT-licensed. The **ultralytics** package and the default **Ultralytics YOLO** pretrained weights are licensed under **AGPL-3.0** unless you obtain a separate license from Ultralytics.

Using this integration in **commercial**, **proprietary**, **client-facing**, or **network-accessible** deployments may impose AGPL obligations or require an **Ultralytics Enterprise** license. **Get legal review** before shipping.

## Install

From the repository root:

```bash
pip install -e ".[dev,vision-ultralytics]"
```

## Configure

See the root `.env.example` for `VISION_BACKEND`, `YOLO_MODEL`, `YOLO_TRACKER`, and related variables.

## Implementation notes

- Only **COCO class 0 (person)** boxes are turned into `TrackedPerson` results.
- Distance uses the core `DistanceEstimator` from bounding-box height.
- Model loading and inference errors are logged on the `integrations.ultralytics_yolo_botsort` logger.
- Unit tests in this repository avoid constructing a live `YOLO` model (no weight downloads in CI).
