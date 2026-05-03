import type { AudioCommandRow, ConversationStatus, RobotStatus, TranscriptItem } from "./types";

const STORAGE_KEY = "robot-follower.apiBase";

export function normalizeBase(url: string): string {
  return url.replace(/\/+$/, "");
}

export function loadSavedApiBase(fallback: string): string {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    if (v && v.trim()) return normalizeBase(v.trim());
  } catch {
    /* ignore */
  }
  return normalizeBase(fallback);
}

export function saveApiBase(url: string): void {
  try {
    localStorage.setItem(STORAGE_KEY, normalizeBase(url));
  } catch {
    /* ignore */
  }
}

export function defaultApiBase(): string {
  const env = import.meta.env.VITE_API_BASE;
  if (env && String(env).trim()) return normalizeBase(String(env).trim());
  return "http://127.0.0.1:8000";
}

async function readJson(res: Response): Promise<unknown> {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

export async function probeEndpoint(
  base: string,
  path: string,
  init?: RequestInit,
): Promise<{ ok: boolean; status: number; ms: number; body: unknown; error?: string }> {
  const url = `${normalizeBase(base)}${path.startsWith("/") ? path : `/${path}`}`;
  const t0 = performance.now();
  try {
    const res = await fetch(url, {
      ...init,
      headers: { Accept: "application/json", ...(init?.headers ?? {}) },
    });
    const ms = Math.round(performance.now() - t0);
    const body = await readJson(res);
    return { ok: res.ok, status: res.status, ms, body };
  } catch (e) {
    const ms = Math.round(performance.now() - t0);
    const msg = e instanceof Error ? e.message : String(e);
    return { ok: false, status: 0, ms, body: null, error: msg };
  }
}

export async function fetchAudioCommands(base: string): Promise<AudioCommandRow[]> {
  const url = `${normalizeBase(base)}/audio/commands`;
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  if (!res.ok) {
    throw new Error(`GET /audio/commands failed: HTTP ${res.status}`);
  }
  const body = (await readJson(res)) as { commands?: AudioCommandRow[] };
  return Array.isArray(body.commands) ? body.commands : [];
}

export async function fetchAudioStatus(base: string): Promise<ConversationStatus> {
  const url = `${normalizeBase(base)}/audio/status`;
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  if (!res.ok) {
    throw new Error(`GET /audio/status failed: HTTP ${res.status}`);
  }
  return (await readJson(res)) as ConversationStatus;
}

export async function fetchAudioTranscript(base: string, limit?: number): Promise<TranscriptItem[]> {
  const q = limit != null ? `?limit=${encodeURIComponent(String(limit))}` : "";
  const url = `${normalizeBase(base)}/audio/transcript${q}`;
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  if (!res.ok) {
    throw new Error(`GET /audio/transcript failed: HTTP ${res.status}`);
  }
  const body = (await readJson(res)) as { items?: TranscriptItem[] };
  return Array.isArray(body.items) ? body.items : [];
}

export async function postAudioConversationStart(base: string): Promise<ConversationStatus> {
  const url = `${normalizeBase(base)}/audio/conversation/start`;
  const res = await fetch(url, {
    method: "POST",
    headers: { Accept: "application/json" },
  });
  const body = await readJson(res);
  if (!res.ok) {
    const detail = typeof body === "object" && body !== null ? JSON.stringify(body) : String(body);
    throw new Error(`POST /audio/conversation/start failed: HTTP ${res.status}: ${detail}`);
  }
  return body as ConversationStatus;
}

export async function postAudioConversationStop(base: string): Promise<ConversationStatus> {
  const url = `${normalizeBase(base)}/audio/conversation/stop`;
  const res = await fetch(url, {
    method: "POST",
    headers: { Accept: "application/json" },
  });
  const body = await readJson(res);
  if (!res.ok) {
    const detail = typeof body === "object" && body !== null ? JSON.stringify(body) : String(body);
    throw new Error(`POST /audio/conversation/stop failed: HTTP ${res.status}: ${detail}`);
  }
  return body as ConversationStatus;
}

export async function postAudioTranscriptClear(base: string): Promise<void> {
  const url = `${normalizeBase(base)}/audio/transcript/clear`;
  const res = await fetch(url, {
    method: "POST",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    const body = await readJson(res);
    const detail = typeof body === "object" && body !== null ? JSON.stringify(body) : String(body);
    throw new Error(`POST /audio/transcript/clear failed: HTTP ${res.status}: ${detail}`);
  }
}

export async function postCommand(base: string, path: string, json?: unknown): Promise<RobotStatus> {
  const url = `${normalizeBase(base)}${path}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: json !== undefined ? JSON.stringify(json) : undefined,
  });
  const body = await readJson(res);
  if (!res.ok) {
    const detail =
      typeof body === "object" && body !== null && "detail" in body
        ? JSON.stringify((body as { detail: unknown }).detail)
        : JSON.stringify(body);
    throw new Error(`HTTP ${res.status}: ${detail}`);
  }
  return body as RobotStatus;
}
