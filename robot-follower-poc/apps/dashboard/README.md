# Robot follower — dashboard (SPA)

React + Vite single-page UI that:

- Opens a **WebSocket** to **`/ws/dashboard`** for the same payload as **`GET /status`** (~5 Hz): **mode**, **desired distance**, **targets** (with optional **JPEG thumbnails**), **motor command history**, and **frame time** as `hh:mm:ss` from `frame_timestamp_s`.
- Polls **`GET /health`** on a slower interval for the control API card.
- Sends **Follow / Stay / Stop / Reset / Set distance** via **HTTP POST** as before.
- Optionally shows **transcript** lines when you enable **Show transcript** in the UI (polls **`/audio/transcript`** while the audio service is running).

## Prerequisites

- Node.js **20+** (or current LTS) and npm.
- FastAPI running with CORS allowing this dev origin (default in repo `.env.example`: `API_CORS_ORIGINS` includes `http://localhost:5173`).

## Setup

```powershell
cd apps\dashboard
npm install
copy .env.example .env.local
```

Edit `.env.local` if the API is not at `http://127.0.0.1:8000`.

## Development

```powershell
npm run dev
```

Open the printed URL (usually `http://localhost:5173`). You can override the API base in the UI; it is saved in `localStorage`. The WebSocket URL is derived from that base (`http` → `ws`, `https` → `wss`).

## Production build

```powershell
npm run build
npm run preview
```

Serve `dist/` behind the same host as the API, or extend `API_CORS_ORIGINS` / reverse-proxy so the browser can reach the API without CORS errors.

## Notes

- **`/ws/dashboard`** is served by the same FastAPI app as **`/status`**; it does not replace HTTP commands.
- Thumbnails and multi-target rows appear when the **orchestrator** runs the **perception pipeline** and ingests frames into the shared `RobotApplication`. API-only runs still stream status, but targets may be empty until perception is active.
