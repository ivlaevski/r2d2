/** Mirrors ``RobotStatus`` from the FastAPI ``GET /status`` payload. */

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface TargetObservation {
  target_detected: boolean;
  bbox: BoundingBox;
  confidence: number;
  horizontal_offset: number;
  approximate_distance_m: number | null;
  track_id?: number | null;
  backend?: string;
}

export interface TargetLock {
  locked_track_id: number | null;
  lost_frames: number;
  locked: boolean;
}

export interface PerceptionFrameResult {
  frame_id: number;
  timestamp_s: number;
  frame_width: number;
  frame_height: number;
  primary_target: TargetObservation;
  target_lock?: TargetLock;
}

export interface DashboardTargetSnapshot {
  track_id: number | null;
  approximate_distance_m: number | null;
  confidence: number;
  is_followed: boolean;
  face_thumbnail_jpeg_b64: string | null;
}

export interface MotorCommandHistoryItem {
  command: string;
  intensity: number;
  applied_at_s: number;
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
  targets_count?: number;
  targets?: DashboardTargetSnapshot[];
  motor_command_history?: MotorCommandHistoryItem[];
}

export interface AudioCommandRow {
  phrase: string;
  description: string;
}

export type TranscriptRole = "user" | "agent" | "system";

export interface TranscriptItem {
  id: string;
  timestamp_utc: string;
  role: TranscriptRole;
  text: string;
  is_final?: boolean;
  source?: string;
  metadata?: Record<string, unknown>;
}

export interface ConversationStatus {
  enabled: boolean;
  active: boolean;
  agent_id: string | null;
  last_error: string | null;
  transcript_count: number;
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
