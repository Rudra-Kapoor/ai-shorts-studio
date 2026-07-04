// Shared domain types. These mirror the MongoDB document shapes and the
// JSON the worker writes back, so the UI and API stay in sync.

export type VideoStatus =
  | "uploading"
  | "queued"
  | "processing"
  | "done"
  | "failed";

export type CaptionStyle = "hormozi" | "mrbeast" | "minimal" | "clean";

export interface ClipScores {
  hook: number;
  emotion: number;
  energy: number;
  visual?: number; // Phase 2: Gemini-vision score (0 when disabled)
  virality: number;
}
