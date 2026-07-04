import { NextRequest, NextResponse } from "next/server";
import { randomUUID } from "crypto";
import { getDb, Collections } from "@/lib/mongo";
import { enqueueJob, wakeWorker } from "@/lib/redis";
import { consumeUsage, releaseUsage, MAX_VIDEOS_PER_DAY } from "@/lib/usage";

export const runtime = "nodejs";

// GET /api/videos?userId=...  → list a user's videos (newest first)
export async function GET(req: NextRequest) {
  const userId = req.nextUrl.searchParams.get("userId");
  if (!userId) {
    return NextResponse.json({ error: "userId is required" }, { status: 400 });
  }
  const db = await getDb();
  const videos = await db
    .collection(Collections.videos)
    .find({ userId })
    .sort({ createdAt: -1 })
    .limit(100)
    .toArray();
  return NextResponse.json({ videos });
}

// POST /api/videos { userId, title, key, sizeBytes }
// Registers an uploaded video, enqueues the processing job, and wakes the worker.
export async function POST(req: NextRequest) {
  try {
    const { userId, title, key, sourceUrl, sizeBytes, captionStyle, aspectRatio } = await req.json();
    if (!userId || (!key && !sourceUrl)) {
      return NextResponse.json(
        { error: "userId and either an uploaded file key or a video link are required" },
        { status: 400 }
      );
    }
    if (sourceUrl && !/^https?:\/\/\S+$/i.test(sourceUrl)) {
      return NextResponse.json(
        { error: "sourceUrl must be a valid http(s) link" },
        { status: 400 }
      );
    }
