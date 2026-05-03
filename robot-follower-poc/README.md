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
| `packages/perception` | OpenCV camera, pluggable `PersonTracker`, distance estimate, target lock |
| `integrations/ultralytics_yolo_botsort` | **Optional** YOLO + BoT-SORT / ByteTrack (AGPL — see below) |
| `packages/behavior` | State machine for modes and commands |
| `packages/motion` | Motion planner + **simulated** motor controller (logging, timeouts) |
| `packages/safety` | Supervisor and watchdog helpers |
| `packages/audio` | Command recognizer abstraction + console stub |
| `packages/infrastructure` | Settings, logging, event bus, `RobotApplication` wiring |
| `apps/api_service` | FastAPI HTTP API |
| `apps/orchestrator_service` | Main control loop (camera + tick + optional API thread) |
| `apps/perception_service` | Standalone camera/detector diagnostics |
| `apps/audio_service` | Console commands forwarded to the API via HTTP |
| `apps/dashboard` | React + Vite SPA: WebSocket live state, targets strip, motor history, HTTP probes |

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

The default stack uses **OpenCV HOG** only and stays aligned with the repo’s **MIT** intent. An **optional** Ultralytics backend is isolated under `integrations/ultralytics_yolo_botsort/` and is **not** installed by default.

### Computer vision backends

| `VISION_BACKEND` | Notes |
|------------------|--------|
| `hog` | **Default.** Simple CPU HOG people detector in core `packages/perception`; MIT-friendly. |
| `ultralytics_yolo_botsort` | **Optional.** YOLO + BoT-SORT / similar tracker YAML; stronger multi-person tracking. Depends on **ultralytics** + default weights (**AGPL-3.0**). |
| `ultralytics_yolo_bytetrack` | **Optional.** Same integration with **ByteTrack** (`bytetrack.yaml`) as the default tracker unless you override `YOLO_TRACKER`. |

### Optional Ultralytics install

```powershell
pip install -e ".[dev,vision-ultralytics]"
```

Example `.env` (after installing the extra):

```env
VISION_BACKEND=ultralytics_yolo_botsort
YOLO_MODEL=yolo11n.pt
YOLO_TRACKER=botsort.yaml
```

If you select an Ultralytics backend without the extra, the app exits with:

`Ultralytics backend requested but optional dependency is not installed. Run: pip install -e .[vision-ultralytics]`

(On PowerShell, quote the argument: `pip install -e ".[vision-ultralytics]"`.)

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

## ElevenLabs Agent audio backend (optional)

**Purpose**

- **Conversational voice UX** via the official ElevenLabs Conversational AI SDK (`DefaultAudioInterface`: microphone in, laptop speakers out).
- **Full transcript** (user, agent, system) exposed only through the **local FastAPI** API for the dashboard — **`ELEVENLABS_API_KEY` never goes to the browser**.
- **Local command extraction** from user transcripts (same safety model as console: **STOP** and other intents are parsed in Python and sent to the local robot API).

**Install**

```powershell
pip install -e ".[dev,audio-elevenlabs]"
```

On Windows, **PyAudio** can be finicky; if `pip install` fails, use a [prebuilt PyAudio wheel](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) for your Python version, or install PortAudio and build from source. The SDK expects PyAudio for `DefaultAudioInterface`.

**Environment** (root `.env`)

```env
ELEVENLABS_AUDIO_ENABLED=true
ELEVENLABS_AGENT_ID=agent_5301kqpx6qheej0a0qvmhkqm0236
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_REQUIRES_AUTH=true
ELEVENLABS_USE_SIGNED_URL=true
ELEVENLABS_AUTO_START=false
```

**Run** (recommended integrated demo):

```powershell
python -m apps.orchestrator_service.main --with-api
```

**Start conversation** (API or curl; the bundled dashboard does not show voice controls while audio is disabled by default):

```powershell
curl -s -X POST http://127.0.0.1:8000/audio/conversation/start
```

**View transcript**:

```powershell
curl -s "http://127.0.0.1:8000/audio/transcript?limit=50"
```

**Safety**

**STOP**, **STAY**, **FOLLOW**, **CHANGE_DISTANCE**, and related phrases are **parsed locally** from the user transcript and dispatched to the **local** `RobotApplication` / HTTP API. The ElevenLabs agent does **not** directly control motors; it provides conversation and audio playback only.

## Web dashboard (SPA)

React + Vite UI under `apps/dashboard`: opens a **WebSocket** to **`/ws/dashboard`** for the same JSON as **`GET /status`** (~5 Hz): live **mode**, **desired distance**, **target count**, **frame time** (duration from `frame_timestamp_s` as `hh:mm:ss`), a horizontal **targets** strip (upper-body **JPEG thumbnails** when the orchestrator runs the perception pipeline), and **motor command** history. It still polls **`/health`** on a slower interval. Commands use **HTTP POST** as before. Optional **transcript** lines appear only when you tick **Show transcript** in the UI (then it polls **`/audio/transcript`** while the audio service is up).

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
ruff check packages apps tests integrations
pytest -q
mypy packages integrations
```

## Future extensions

- **Real motor controller** over serial / USB / CAN behind `packages/motion` (replace `SimulatedMotorController`).
- **Face recognition** or re-identification for tighter following.
- **Other detectors** behind `PersonTracker` (keep optional / alternate-license code under `integrations/`).
- **Cloud AI** command interpretation; keep `SafetySupervisor` and emergency paths **local-only**.
- **Whisper / Vosk / Windows SR** behind `CommandRecognizerProtocol`.
- **TTS** via `TextToSpeechProtocol`.
- **Dashboard**: live camera preview, richer telemetry, per-service HTTP health when you add more endpoints.

## License

The **core project** is intended to remain **MIT**-licensed unless files state otherwise.

The **optional Ultralytics** path depends on the **`ultralytics`** package and default **Ultralytics YOLO** model weights, which are **AGPL-3.0** unless you use weights and terms covered by another license. **Commercial**, **proprietary**, **client-facing**, or **network-accessible** deployments may require **legal review** and may need an **Ultralytics Enterprise** license or a different permissively licensed vision stack. See `integrations/ultralytics_yolo_botsort/README.md`.
