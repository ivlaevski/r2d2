# Robot follower — dashboard (SPA)

React + Vite single-page UI that:

- Polls **`GET /health`** and **`GET /status`** every **5 seconds** (configurable constant in `src/App.tsx`).
- Loads **`GET /audio/commands`** when the API base changes (supported console / future ASR phrases).
- Shows **microphone / ingress listening** from **`GET /status`** (`microphone_listening`), driven by **`audio_service`** heartbeats to **`POST /audio/listening`**.
- Shows **command receipt echo** (`command_receipt_echo`, `command_receipt_at_s`) so each accepted command is repeated for confirmation.
- Provides buttons for **`/commands/follow`**, **`stay`**, **`stop`**, **`reset`**, and **`/commands/distance`** with a numeric field.

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

Open the printed URL (usually `http://localhost:5173`). You can override the API base in the UI; it is saved in `localStorage`.

## Production build

```powershell
npm run build
npm run preview
```

Serve `dist/` behind the same host as the API, or extend `API_CORS_ORIGINS` / reverse-proxy so the browser can reach the API without CORS errors.

## Notes

- In this PoC, only the **control API** exposes HTTP. Perception and audio are separate processes without a built-in health URL; the dashboard treats **`/status`** as the “robot runtime” probe when the API shares the orchestrator’s `RobotApplication`.
