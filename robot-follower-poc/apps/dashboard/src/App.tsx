import { useCallback, useEffect, useMemo, useState } from "react";

import {
  defaultApiBase,
  fetchAudioTranscript,
  loadSavedApiBase,
  normalizeBase,
  postCommand,
  probeEndpoint,
  saveApiBase,
} from "./api";
import type { DashboardTargetSnapshot, ProbeResult, TranscriptItem } from "./types";
import { dashboardWsUrl, formatDurationHms, useRobotStatusSocket } from "./useRobotStatusSocket";

const HEALTH_POLL_MS = 8000;
const TRANSCRIPT_POLL_MS = 4000;
const SHOW_TRANSCRIPT_KEY = "robot-follower.showTranscript";

const SERVICES: { id: string; name: string; path: string; note: string }[] = [
  { id: "health", name: "Control API", path: "/health", note: "FastAPI / Uvicorn" },
];

function formatJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function loadShowTranscript(): boolean {
  try {
    return localStorage.getItem(SHOW_TRANSCRIPT_KEY) === "1";
  } catch {
    return false;
  }
}

function saveShowTranscript(on: boolean): void {
  try {
    localStorage.setItem(SHOW_TRANSCRIPT_KEY, on ? "1" : "0");
  } catch {
    /* ignore */
  }
}

function FaceThumb({ target, index }: { target: DashboardTargetSnapshot; index: number }) {
  const [broken, setBroken] = useState(false);
  const src =
    target.face_thumbnail_jpeg_b64 && !broken
      ? `data:image/jpeg;base64,${target.face_thumbnail_jpeg_b64}`
      : null;
  const key = target.track_id ?? `i-${index}`;
  return (
    <div className="face-thumb-wrap" aria-hidden={true}>
      {src ? (
        <img
          key={key}
          className="face-thumb"
          src={src}
          alt=""
          width={64}
          height={64}
          onError={() => setBroken(true)}
        />
      ) : (
        <div className="face-thumb face-thumb-placeholder" title="No crop (disabled or empty frame)">
          <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor" aria-hidden>
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
          </svg>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [apiBase, setApiBase] = useState(() => loadSavedApiBase(defaultApiBase()));
  const [draftBase, setDraftBase] = useState(apiBase);
  const [probes, setProbes] = useState<Record<string, ProbeResult>>({});
  const [lastPollAt, setLastPollAt] = useState<string>("—");
  const [commandError, setCommandError] = useState<string | null>(null);
  const [commandOk, setCommandOk] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showTranscriptSection, setShowTranscriptSection] = useState(() => loadShowTranscript());
  const [transcriptItems, setTranscriptItems] = useState<TranscriptItem[]>([]);
  const [transcriptError, setTranscriptError] = useState<string | null>(null);

  const { status: robotStatus, connected: wsConnected, error: wsError } = useRobotStatusSocket(apiBase);

  const runHealthPoll = useCallback(async () => {
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
  }, [apiBase]);

  useEffect(() => {
    void runHealthPoll();
    const id = window.setInterval(() => void runHealthPoll(), HEALTH_POLL_MS);
    return () => window.clearInterval(id);
  }, [runHealthPoll]);

  useEffect(() => {
    if (!showTranscriptSection) {
      setTranscriptItems([]);
      setTranscriptError(null);
      return;
    }
    let cancelled = false;
    const tick = async () => {
      try {
        const items = await fetchAudioTranscript(apiBase, 40);
        if (!cancelled) {
          setTranscriptItems(items);
          setTranscriptError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setTranscriptItems([]);
          setTranscriptError(e instanceof Error ? e.message : String(e));
        }
      }
    };
    void tick();
    const id = window.setInterval(() => void tick(), TRANSCRIPT_POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [apiBase, showTranscriptSection]);

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
      const echo = st.command_receipt_echo ?? `mode ${st.mode}`;
      setCommandOk(`${echo} · motion ${st.last_motion_command}`);
      void runHealthPoll();
    } catch (e) {
      setCommandError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const toggleTranscript = (on: boolean) => {
    setShowTranscriptSection(on);
    saveShowTranscript(on);
  };

  const statusPretty = useMemo(() => formatJson(robotStatus), [robotStatus]);
  const targets = robotStatus?.targets ?? [];
  const targetsCount = robotStatus?.targets_count ?? targets.length;
  const motorHistory = robotStatus?.motor_command_history ?? [];
  const runningClock = formatDurationHms(robotStatus?.frame_timestamp_s ?? 0);

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Robot follower — dashboard</h1>
          <p className="sub">
            Live robot state over WebSocket <code>{dashboardWsUrl(apiBase)}</code> · HTTP health every{" "}
            {HEALTH_POLL_MS / 1000}s · CORS <code>API_CORS_ORIGINS</code>
          </p>
        </div>
        <span className={`pill ${wsConnected ? "" : "pill-warn"}`}>
          WS: {wsConnected ? "connected" : "disconnected"}
        </span>
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
          Last health poll: <span>{lastPollAt}</span>
        </div>
      </section>

      <section className="section section-live" aria-label="Live robot overview">
        <h2>Live overview</h2>
        <div className={`live-overview ${wsConnected ? "" : "live-overview-stale"}`}>
          <div className="live-metric">
            <span className="live-label">Mode</span>
            <span className="live-value">{robotStatus?.mode ?? "—"}</span>
          </div>
          <div className="live-metric">
            <span className="live-label">Desired distance (m)</span>
            <span className="live-value">
              {robotStatus != null ? robotStatus.desired_distance_m.toFixed(2) : "—"}
            </span>
          </div>
          <div className="live-metric">
            <span className="live-label">Targets</span>
            <span className="live-value">{robotStatus != null ? targetsCount : "—"}</span>
          </div>
          <div className="live-metric">
            <span className="live-label">Frame time (hh:mm:ss)</span>
            <span className="live-value mono">{robotStatus != null ? runningClock : "—"}</span>
          </div>
        </div>
        {wsError ? <div className="banner" style={{ marginTop: 10 }}>{wsError}</div> : null}
        {!wsConnected && !wsError ? (
          <div className="meta" style={{ marginTop: 8 }}>
            Connecting to WebSocket… If this persists, ensure the API exposes <code>/ws/dashboard</code>.
          </div>
        ) : null}
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
          <div className="card">
            <div className="card-title">
              <span>Live state (WebSocket)</span>
              <span className={`dot ${wsConnected ? "ok" : "fail"}`} title={wsConnected ? "streaming" : "down"} />
            </div>
            <div className="meta">
              <div>
                <code>/ws/dashboard</code>
              </div>
              <div>JSON snapshots ~5 Hz (same payload as GET /status)</div>
              <div style={{ marginTop: 6 }}>{wsConnected ? "Receiving frames" : "Not connected"}</div>
            </div>
          </div>
        </div>
      </section>

      <section className="section" aria-label="Targets">
        <h2>Targets</h2>
        <div className="targets-box" role="list">
          {targets.length === 0 ? (
            <div className="meta targets-empty">No tracked people in the latest frame.</div>
          ) : (
            targets.map((t, i) => (
              <div key={t.track_id ?? `idx-${i}`} className="target-chip" role="listitem">
                <FaceThumb target={t} index={i} />
                <div className="target-meta">
                  <span className="target-dist">
                    {t.approximate_distance_m != null ? `${t.approximate_distance_m.toFixed(2)} m` : "— m"}
                  </span>
                  <span className={`target-flag ${t.is_followed ? "followed" : ""}`}>
                    {t.is_followed ? "Followed" : "—"}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </section>

      <section className="section" aria-label="Motor command history">
        <h2>Motor commands (recent)</h2>
        <p className="meta section-lead">Last distinct low-level commands applied to the simulated motor (newest first).</p>
        {motorHistory.length === 0 ? (
          <div className="meta">No history yet (orchestrator not ticking / no motion).</div>
        ) : (
          <ol className="motor-list">
            {motorHistory.map((m, i) => (
              <li key={`${m.command}-${m.applied_at_s}-${i}`}>
                <span className="mono motor-cmd">{m.command}</span>
                <span className="motor-int">intensity {m.intensity.toFixed(2)}</span>
                <span className="motor-time">
                  {m.applied_at_s > 0 ? new Date(m.applied_at_s * 1000).toLocaleString() : "—"}
                </span>
              </li>
            ))}
          </ol>
        )}
      </section>

      <section className="section" aria-label="Transcript (optional)">
        <h2>Transcript (audio service)</h2>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={showTranscriptSection}
            onChange={(e) => toggleTranscript(e.target.checked)}
          />
          <span>Show transcript when the audio stack is running (polls GET /audio/transcript).</span>
        </label>
        {showTranscriptSection ? (
          <>
            {transcriptError ? (
              <div className="banner" style={{ marginTop: 10 }}>
                {transcriptError}
              </div>
            ) : null}
            <div className="transcript-panel" style={{ marginTop: 12 }}>
              <div className="transcript-title">Latest lines (up to 40)</div>
              <div className="transcript-scroll">
                {transcriptItems.length === 0 ? (
                  <div className="meta">No transcript lines yet.</div>
                ) : (
                  transcriptItems.map((line) => (
                    <div
                      key={line.id}
                      className={`transcript-line role-${line.role === "user" ? "user" : line.role === "agent" ? "agent" : "system"}`}
                    >
                      <span className="transcript-role">{line.role}</span>
                      <span>{line.text}</span>
                      <span className="transcript-time">{line.timestamp_utc}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </>
        ) : null}
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
        {robotStatus?.command_receipt_echo ? (
          <div className="echo-banner" role="status" style={{ marginTop: 12 }}>
            <div className="echo-label">Last command receipt</div>
            <div className="echo-text">{robotStatus.command_receipt_echo}</div>
            {(robotStatus.command_receipt_at_s ?? 0) > 0 ? (
              <div className="meta">
                at {new Date((robotStatus.command_receipt_at_s ?? 0) * 1000).toLocaleString()}
              </div>
            ) : null}
          </div>
        ) : (
          <div className="meta echo-muted" style={{ marginTop: 10 }}>
            No commands applied yet (or receipt cleared on restart).
          </div>
        )}
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
