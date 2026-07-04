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

export interface Clip {
  _id: string;
  videoId: string;
  userId: string;
  index: number;
  title: string;
  startSec: number;
  endSec: number;
  durationSec: number;
  scores: ClipScores;
  reason: string;
  captionStyle?: string;
  aspectRatio?: string; // "9:16" | "1:1" | "16:9"
  editedKey?: string;
  editedUrl?: string; // presigned GET url, filled in at read time
  thumbnailKey?: string;
  thumbnailUrl?: string; // presigned GET url, filled in at read time
  srtKey?: string;
  srtUrl?: string; // presigned GET url for the .srt caption file
  trendMatch?: string[]; // Phase 3: matched trend titles
  caption?: string;
  hashtags?: string[];
  youtubeUrl?: string; // Phase 3: set after auto-post
  instagramUrl?: string;
  published?: boolean;
  status: "pending" | "rendering" | "done" | "failed";
  createdAt: string;
}

export interface Video {
  _id: string;
  userId: string;
  title: string;
  originalKey?: string; // set after upload, or after a link is fetched
  sourceUrl?: string; // YouTube/other link, when ingested from a URL
  originalUrl?: string; // presigned GET url, filled in at read time
  sizeBytes: number;
  durationSec?: number;
  status: VideoStatus;
  stage?: string; // human-readable current step
  progress?: number; // 0..100
  error?: string;
  transcript?: string;
  captionStyle?: string; // Phase 2: chosen at upload
  aspectRatio?: string; // "9:16" | "1:1" | "16:9", chosen at upload
  createdAt: string;
  updatedAt: string;
}

export interface VideoWithClips extends Video {
  clips: Clip[];
}

export interface Usage {
  used: number;
  limit: number;
  remaining: number;
}

export interface User {
  _id: string;
  email: string;
  name?: string;
  subscription: "free" | "pro";
  totalVideos?: number;
  createdAt: string;
}
