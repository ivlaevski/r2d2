import { useCallback, useEffect, useMemo, useState } from "react";

import {
  defaultApiBase,
  fetchAudioCommands,
  loadSavedApiBase,
  normalizeBase,
  postCommand,
  probeEndpoint,
  saveApiBase,
} from "./api";
import type { AudioCommandRow, ProbeResult, RobotStatus } from "./types";

const POLL_MS = 5000;

const SERVICES: { id: string; name: string; path: string; note: string }[] = [
  { id: "health", name: "Control API", path: "/health", note: "FastAPI / Uvicorn" },
  { id: "status", name: "Robot status", path: "/status", note: "Orchestrator brain when co-hosted" },
];

function formatJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

export default function App() {
  const [apiBase, setApiBase] = useState(() => loadSavedApiBase(defaultApiBase()));
  const [draftBase, setDraftBase] = useState(apiBase);
  const [probes, setProbes] = useState<Record<string, ProbeResult>>({});
  const [robotStatus, setRobotStatus] = useState<RobotStatus | null>(null);
  const [lastPollAt, setLastPollAt] = useState<string>("—");
  const [commandError, setCommandError] = useState<string | null>(null);
  const [commandOk, setCommandOk] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [audioCommands, setAudioCommands] = useState<AudioCommandRow[]>([]);
  const [audioCatalogError, setAudioCatalogError] = useState<string | null>(null);

  const runPoll = useCallback(async () => {
    const base = apiBase;
    const checkedAt = new Date().toISOString();
    const next: Record<string, ProbeResult> = {};

    for (const s of SERVICES) {
      const r = await probeEndpoint(base, s.path);
      next[s.id] = {
        ok: r.ok,
        statusCode: r.status,
        latencyMs: r.ms,
        checkedAt,
        error: r.error,
        payload: r.body,
      };
    }

    setProbes(next);
    setLastPollAt(checkedAt);

    if (next.status?.ok) {
      const st = next.status.payload;
      if (st && typeof st === "object" && st !== null && "mode" in st) {
        setRobotStatus(st as RobotStatus);
      }
    }
  }, [apiBase]);

  useEffect(() => {
    setAudioCatalogError(null);
    void fetchAudioCommands(apiBase)
      .then(setAudioCommands)
      .catch((e: unknown) => setAudioCatalogError(e instanceof Error ? e.message : String(e)));
  }, [apiBase]);

  useEffect(() => {
    void runPoll();
    const id = window.setInterval(() => void runPoll(), POLL_MS);
    return () => window.clearInterval(id);
  }, [runPoll]);

  const applyBase = () => {
    const n = normalizeBase(draftBase.trim() || defaultApiBase());
    setDraftBase(n);
    setApiBase(n);
    saveApiBase(n);
  };

  const runCommand = async (path: string, body?: unknown) => {
    setCommandError(null);
    setCommandOk(null);
    setBusy(true);
    try {
      const st = await postCommand(apiBase, path, body);
      setRobotStatus(st);
      const echo = st.command_receipt_echo ?? `mode ${st.mode}`;
      setCommandOk(`${echo} · motion ${st.last_motion_command}`);
      void runPoll();
    } catch (e) {
      setCommandError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const statusPretty = useMemo(() => formatJson(robotStatus ?? probes.status?.payload ?? null), [robotStatus, probes]);

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Robot follower — dashboard</h1>
          <p className="sub">
            Service probes every {POLL_MS / 1000}s · same origin CORS required (see API{" "}
            <code>API_CORS_ORIGINS</code>)
          </p>
        </div>
        <span className="pill">poll: {POLL_MS / 1000}s</span>
      </header>

      <section className="section" aria-label="API configuration">
        <h2>API base</h2>
        <div className="config-row">
          <label htmlFor="api-base">URL</label>
          <input
            id="api-base"
            type="url"
            value={draftBase}
            onChange={(e) => setDraftBase(e.target.value)}
            placeholder="http://127.0.0.1:8000"
          />
          <button type="button" className="btn btn-primary" onClick={applyBase}>
            Apply
          </button>
        </div>
        <div className="links">
          OpenAPI docs:{" "}
          <a href={`${normalizeBase(apiBase)}/docs`} target="_blank" rel="noreferrer">
            {normalizeBase(apiBase)}/docs
          </a>
          {" · "}
          Last poll: <span>{lastPollAt}</span>
        </div>
      </section>

      <section className="section" aria-label="Service health">
        <h2>Services</h2>
        <div className="grid">
          {SERVICES.map((s) => {
            const p = probes[s.id];
            return (
              <div key={s.id} className="card">
                <div className="card-title">
                  <span>{s.name}</span>
                  <span className={`dot ${p?.ok ? "ok" : p ? "fail" : ""}`} title={p?.ok ? "up" : "unknown/down"} />
                </div>
                <div className="meta">
                  <div>
                    <code>{s.path}</code>
                  </div>
                  <div>{s.note}</div>
                  {p ? (
                    <>
                      <div>
                        HTTP {p.statusCode} · {p.latencyMs} ms
                      </div>
                      {p.error ? <div>error: {p.error}</div> : null}
                      <div style={{ marginTop: 6 }}>checked {p.checkedAt}</div>
                    </>
                  ) : (
                    <div>waiting…</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section className="section" aria-label="Audio ingress">
        <h2>Microphone / audio ingress</h2>
        <div className={`mic-banner ${robotStatus?.microphone_listening === true ? "live" : ""}`}>
          <span className={`mic-dot ${robotStatus?.microphone_listening === true ? "live" : ""}`} />
          <div>
            <strong>{robotStatus?.microphone_listening === true ? "Listening" : "Idle"}</strong>
            <div className="meta">
              Run <code>python -m apps.audio_service.main</code> while the API is up. Heartbeats every 8s; idle if no
              heartbeat for longer than <code>AUDIO_LISTENING_TTL_S</code> (API <code>.env</code>).
            </div>
          </div>
        </div>
        {robotStatus?.command_receipt_echo ? (
          <div className="echo-banner" role="status">
            <div className="echo-label">Last command receipt (repeated)</div>
            <div className="echo-text">{robotStatus.command_receipt_echo}</div>
            {(robotStatus.command_receipt_at_s ?? 0) > 0 ? (
              <div className="meta">
                at {new Date((robotStatus.command_receipt_at_s ?? 0) * 1000).toLocaleString()}
              </div>
            ) : null}
          </div>
        ) : (
          <div className="meta echo-muted">No commands applied yet (or receipt cleared on restart).</div>
        )}
      </section>

      <section className="section" aria-label="Audio command list">
        <h2>Audio / console commands</h2>
        {audioCatalogError ? <div className="banner">{audioCatalogError}</div> : null}
        <ul className="audio-commands">
          {audioCommands.map((c) => (
            <li key={c.phrase}>
              <code>{c.phrase}</code>
              <span className="audio-desc">{c.description}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="section" aria-label="Robot status JSON">
        <h2>Robot status (latest)</h2>
        <pre className="pre">{statusPretty}</pre>
      </section>

      <section className="section" aria-label="Commands">
        <h2>Commands</h2>
        <div className="commands">
          <button type="button" className="btn btn-primary" disabled={busy} onClick={() => void runCommand("/commands/follow")}>
            Follow
          </button>
          <button type="button" className="btn btn-primary" disabled={busy} onClick={() => void runCommand("/commands/stay")}>
            Stay
          </button>
          <button type="button" className="btn btn-primary" disabled={busy} onClick={() => void runCommand("/commands/stop")}>
            Stop
          </button>
          <button type="button" className="btn btn-primary" disabled={busy} onClick={() => void runCommand("/commands/reset")}>
            Reset
          </button>
        </div>
        <DistanceCommand busy={busy} onRun={(m) => void runCommand("/commands/distance", { distance_m: m })} />
        {commandError ? <div className="banner">{commandError}</div> : null}
        {commandOk ? <div className="banner ok">{commandOk}</div> : null}
      </section>
    </div>
  );
}

function DistanceCommand({ busy, onRun }: { busy: boolean; onRun: (m: number) => void }) {
  const [m, setM] = useState(2.0);
  return (
    <div className="distance-row">
      <label htmlFor="dist">Distance (m)</label>
      <input
        id="dist"
        type="number"
        min={0.1}
        max={50}
        step={0.1}
        value={m}
        onChange={(e) => setM(Number(e.target.value))}
      />
      <button type="button" className="btn btn-primary" disabled={busy} onClick={() => onRun(m)}>
        Set distance
      </button>
    </div>
  );
}
