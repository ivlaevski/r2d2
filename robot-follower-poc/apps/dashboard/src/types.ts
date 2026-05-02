/** Mirrors ``RobotStatus`` from the FastAPI ``GET /status`` payload. */

export interface TargetObservation {
  target_detected: boolean;
  bbox_x: number;
  bbox_y: number;
  bbox_width: number;
  bbox_height: number;
  confidence: number;
  horizontal_offset: number;
  approximate_distance_m: number | null;
}

export interface RobotStatus {
  mode: string;
  last_high_level_command: string | null;
  desired_distance_m: number;
  target: TargetObservation | null;
  last_motion_command: string;
  emergency_latched: boolean;
  target_lost_seconds: number;
  frame_timestamp_s: number;
  /** Present on API ≥ PoC with audio ingress fields. */
  microphone_listening?: boolean;
  command_receipt_echo?: string | null;
  command_receipt_at_s?: number;
}

export interface AudioCommandRow {
  phrase: string;
  description: string;
}

export interface HealthPayload {
  status?: string;
}

export interface ProbeResult {
  ok: boolean;
  statusCode: number;
  latencyMs: number;
  checkedAt: string;
  error?: string;
  payload?: unknown;
}
