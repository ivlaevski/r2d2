# Agent rules — Robot Follower PoC

Use this file as standing guidance when editing this repository.

## Product intent

- **Local-first** personal follower robot assistant PoC; **no required cloud** in v0.
- **Safety-critical** paths (emergency stop, motion gating) stay in local Python (`safety`, `behavior`, `motion`).
- Movement is **simulated** only; design motor I/O so a **real adapter** can replace `SimulatedMotorController` without rewriting planners.

## Architecture boundaries

- **`packages/contracts`**: Pydantic models only; no I/O, no OpenCV imports.
- **`packages/perception`**: Camera, detection, tracking, distance — no HTTP.
- **`packages/behavior`**: State machine and policies — pure logic + `Settings`.
- **`packages/motion`**: Planning and motor adapters — no FastAPI.
- **`packages/safety`**: Last-line motion filtering; must remain conservative.
- **`packages/infrastructure`**: Config, logging, wiring (`RobotApplication`), optional cloud **stubs** — not a dumping ground for business rules.
- **`apps/*`**: Thin entry points and HTTP routes; delegate to `RobotApplication` or small service functions.

## Coding standards

- Python **3.11+**, type hints on public APIs, short docstrings on public classes.
- Prefer **configuration** (`Settings` / `.env`) over magic numbers in logic.
- Keep route handlers **thin**; validate I/O with Pydantic; put decisions in packages.
- Avoid drive-by refactors unrelated to the task; keep diffs focused.
- Do not add Docker/Kubernetes unless explicitly requested.

## Running services

- For an integrated demo, run **`python -m apps.orchestrator_service.main --with-api`** so API and brain share one process.
- Separate processes do **not** share `RobotApplication` memory unless you add IPC.

## Tests

- Add or update **pytest** coverage when changing behavior, motion, safety, or distance logic.
- Keep tests deterministic (no real camera in unit tests).

## Windows notes

- OpenCV capture uses **DirectShow** (`CAP_DSHOW`) for laptop cameras.
- Prefer a project **venv** and `pip install -e ".[dev]"` from `robot-follower-poc/`.
- **`apps/dashboard`**: Node SPA; set `API_CORS_ORIGINS` so the browser can call the FastAPI dev server from `http://localhost:5173` (defaults are in `.env.example`).
