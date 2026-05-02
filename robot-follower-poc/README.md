# Robot Follower PoC

Local-first proof-of-concept for a **personal follower robot assistant** running on a Windows 11 laptop. It uses the built-in **camera** and **microphone** hooks, simulates **motor commands**, and keeps **safety-critical logic** on-device. There is **no cloud dependency** in this version; remote AI is represented only by a small **stub interface** under `packages/infrastructure/cloud_command_provider.py`.

## Purpose

- Capture video and estimate **horizontal offset** and **approximate distance** from a person bounding box.
- Run a **behavior state machine** (idle, follow, stay, target lost, emergency stop).
- Plan **simulated motion** (forward / back / turn / stop) with configurable thresholds.
- Expose a **FastAPI** surface for commands and status (`curl`-friendly).
- Structure code as **separate services** (entry points under `apps/`) sharing **typed contracts** (`packages/contracts/`) so a future physical robot can swap in a real motor adapter.

See also **`AGENTS.md`** for repository conventions for future work.

## Architecture (high level)

| Area | Role |
|------|------|
| `packages/contracts` | Pydantic models shared across services |
| `packages/perception` | OpenCV camera, HOG person detector, distance estimate, tracker |
| `packages/behavior` | State machine for modes and commands |
| `packages/motion` | Motion planner + **simulated** motor controller (logging, timeouts) |
| `packages/safety` | Supervisor and watchdog helpers |
| `packages/audio` | Command recognizer abstraction + console stub |
| `packages/infrastructure` | Settings, logging, event bus, `RobotApplication` wiring |
| `apps/api_service` | FastAPI HTTP API |
| `apps/orchestrator_service` | Main control loop (camera + tick + optional API thread) |
| `apps/perception_service` | Standalone camera/detector diagnostics |
| `apps/audio_service` | Console commands forwarded to the API via HTTP |
| `apps/dashboard` | React + Vite SPA: service probes + command buttons |

**Integrated run:** start the orchestrator with `--with-api` so the API and control loop share one `RobotApplication` in a single process (recommended for local demos).

**Split run:** start `api_service` and `orchestrator` separately only if you add IPC later; out of the box, separate processes do **not** share in-memory robot state.

## Requirements

- Python **3.11+** (tested layout for 3.11 on Windows 11)
- **Node.js 20+** (for `apps/dashboard` only)
- Webcam and (optionally) speakers; microphone capture is stubbed for later ASR.

## Install

From the repository root `robot-follower-poc/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"
```

Copy environment defaults:

```powershell
copy .env.example .env
```

Tune `CAMERA_INDEX`, `CALIBRATION_CONSTANT_M_PX`, and distance thresholds for your room and camera.

## Distance calibration (perception)

Distance is a **rough monocular estimate** from bounding-box height only:

\[
\text{distance\_m} = \frac{\texttt{CALIBRATION\_CONSTANT\_M\_PX}}{\texttt{bbox\_height\_pixels}}
\]

Set **`CALIBRATION_CONSTANT_M_PX`** in your repo root **`.env`** (see `.env.example`). Pydantic maps it to `calibration_constant_m_px` in `packages/infrastructure/config.py`. Restart the orchestrator / API after changes.

**One-point scale (quick fix):** stand at a known distance (e.g. 2.0 m), read `approximate_distance_m` from `GET /status` or the dashboard JSON. Then:

\[
\text{new constant} = \text{old constant} \times \frac{\text{true distance}}{\text{reported distance}}
\]

Example: constant `1.65`, true 2.0 m, reported 2.5 m → new constant ≈ `1.65 × (2.0 / 2.5) = 1.32`.

Because D = k/h, if h is fixed wrong scale is linear in k: D_true/D_reported = k_new/k_old → k_new = k_old * (D_true/D_reported). Yes.

**From measured height:** if at 2.0 m the person’s bbox height is `h` pixels, set `CALIBRATION_CONSTANT_M_PX = 2.0 * h`.

**Why it still drifts:** HOG person height in pixels changes with **pose**, **cropping**, **partial body**, and **not true pinhole geometry**—so treat distance as a **tunable control signal**, not a tape measure. For steadier range, plan a detector with more stable scale (e.g. depth camera, stereo, or learned model).

**Follow distance for motion:** `DESIRED_DISTANCE_M`, `DISTANCE_TOO_FAR_M`, and `DISTANCE_TOO_CLOSE_M` in `.env` set when the planner commands forward/back; tune these together with calibration.

## Run the API service

```powershell
python -m apps.api_service.main
```

- Defaults: `http://127.0.0.1:8000`
- OpenAPI: `http://127.0.0.1:8000/docs`

## Run the orchestrator (control loop)

With **camera** and **in-process API** (best local demo):

```powershell
python -m apps.orchestrator_service.main --with-api
```

Headless / no camera (planner + state machine only, no detections):

```powershell
python -m apps.orchestrator_service.main --with-api --no-camera
```

## Run other entry points

```powershell
python -m apps.perception_service.main
python -m apps.audio_service.main
```

`audio_service` posts parsed console commands to `ROBOT_API_BASE` (see `.env.example`). Start the API first (standalone or via orchestrator `--with-api`).

## Web dashboard (SPA)

React + Vite UI under `apps/dashboard`: polls **`/health`** and **`/status`** every **5 seconds**, and sends **Follow / Stay / Stop / Reset / Set distance** to the API.

1. Ensure the API is up (e.g. `python -m apps.orchestrator_service.main --with-api`).
2. Root `.env` should allow the Vite dev origin (default `API_CORS_ORIGINS` in `.env.example` already includes `http://localhost:5173`).
3. In another terminal:

```powershell
cd apps\dashboard
npm install
npm run dev
```

Open `http://localhost:5173`. Details: `apps/dashboard/README.md`.

## Test with curl

```powershell
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/status
curl -s -X POST http://127.0.0.1:8000/commands/follow
curl -s -X POST http://127.0.0.1:8000/commands/stay
curl -s -X POST http://127.0.0.1:8000/commands/stop
curl -s -X POST http://127.0.0.1:8000/commands/reset
curl -s -X POST http://127.0.0.1:8000/commands/distance -H "Content-Type: application/json" -d "{\"distance_m\": 2.0}"
curl -s -X POST http://127.0.0.1:8000/commands -H "Content-Type: application/json" -d "{\"command\": \"FOLLOW\"}"
```

## Linting and tests

```powershell
ruff check packages apps tests
pytest -q
mypy packages
```

## Future extensions

- **Real motor controller** over serial / USB / CAN behind `packages/motion` (replace `SimulatedMotorController`).
- **Face recognition** or re-identification for tighter following.
- **MediaPipe / YOLO** behind `PersonDetector`.
- **Cloud AI** command interpretation; keep `SafetySupervisor` and emergency paths **local-only**.
- **Whisper / Vosk / Windows SR** behind `CommandRecognizerProtocol`.
- **TTS** via `TextToSpeechProtocol`.
- **Dashboard**: live camera preview, richer telemetry, per-service HTTP health when you add more endpoints.

## License

MIT (placeholder — adjust to your org’s policy).
