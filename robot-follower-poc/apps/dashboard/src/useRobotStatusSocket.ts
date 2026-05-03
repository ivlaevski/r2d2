import { useEffect, useRef, useState } from "react";

import { normalizeBase } from "./api";
import type { RobotStatus } from "./types";

function parseRobotStatus(data: unknown): RobotStatus | null {
  if (!data || typeof data !== "object") return null;
  const o = data as Record<string, unknown>;
  if (typeof o.mode !== "string") return null;
  return data as RobotStatus;
}

export function dashboardWsUrl(httpBase: string): string {
  const base = normalizeBase(httpBase);
  const u = new URL(base);
  u.protocol = u.protocol === "https:" ? "wss:" : "ws:";
  u.pathname = "/ws/dashboard";
  u.hash = "";
  u.search = "";
  return u.toString();
}

/**
 * Streams ``GET /status``-equivalent JSON over ``/ws/dashboard`` (same host as API).
 */
export function useRobotStatusSocket(apiBase: string): {
  status: RobotStatus | null;
  connected: boolean;
  error: string | null;
} {
  const [status, setStatus] = useState<RobotStatus | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reconnectTimer = useRef<number>(0);

  useEffect(() => {
    let cancelled = false;
    let ws: WebSocket | null = null;

    const clearTimer = () => {
      if (reconnectTimer.current) {
        window.clearTimeout(reconnectTimer.current);
        reconnectTimer.current = 0;
      }
    };

    const connect = () => {
      if (cancelled) return;
      clearTimer();
      setError(null);
      const url = dashboardWsUrl(apiBase);
      try {
        ws = new WebSocket(url);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : String(e));
          reconnectTimer.current = window.setTimeout(connect, 2000);
        }
        return;
      }

      ws.onopen = () => {
        if (!cancelled) {
          setConnected(true);
          setError(null);
        }
      };

      ws.onclose = () => {
        if (!cancelled) setConnected(false);
        ws = null;
        if (!cancelled) {
          reconnectTimer.current = window.setTimeout(connect, 2000);
        }
      };

      ws.onerror = () => {
        if (!cancelled) setError("WebSocket error (check API is up and path /ws/dashboard)");
      };

      ws.onmessage = (ev) => {
        try {
          const j = JSON.parse(String(ev.data)) as unknown;
          const st = parseRobotStatus(j);
          if (st && !cancelled) setStatus(st);
        } catch {
          /* ignore malformed frames */
        }
      };
    };

    connect();

    return () => {
      cancelled = true;
      clearTimer();
      ws?.close();
    };
  }, [apiBase]);

  return { status, connected, error };
}

export function formatDurationHms(totalSeconds: number): string {
  if (!Number.isFinite(totalSeconds) || totalSeconds < 0) return "00:00:00";
  const s = Math.floor(totalSeconds);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  return [h, m, sec].map((n) => String(n).padStart(2, "0")).join(":");
}
