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

    const ALLOWED_STYLES = ["hormozi", "mrbeast", "minimal", "clean"];
    const ALLOWED_RATIOS = ["9:16", "1:1", "16:9"];
    const now = new Date().toISOString();
    const video = {
      _id: randomUUID(),
      userId,
      title: title || (sourceUrl ? "YouTube video" : "Untitled video"),
      // An uploaded file already has its R2 key; a link is fetched by the worker,
      // which fills in originalKey after download.
      ...(key ? { originalKey: key } : {}),
      ...(sourceUrl ? { sourceUrl } : {}),
      sizeBytes: sizeBytes || 0,
      captionStyle: ALLOWED_STYLES.includes(captionStyle) ? captionStyle : "hormozi",
      aspectRatio: ALLOWED_RATIOS.includes(aspectRatio) ? aspectRatio : "9:16",
      status: "queued" as const,
      stage: sourceUrl ? "Queued — will fetch from link" : "Queued — waiting for a worker",
      progress: 0,
      createdAt: now,
      updatedAt: now,
    };

    const db = await getDb();

    // Enforce the per-user daily quota before doing any work.
    const allowed = await consumeUsage(db, userId);
    if (!allowed) {
      return NextResponse.json(
        { error: `Daily limit reached (${MAX_VIDEOS_PER_DAY} videos/day). Try again tomorrow.` },
        { status: 429 }
      );
    }

    // The quota slot is already consumed; if registering or queuing the job
    // fails, hand the slot back so a transient error doesn't burn the user's day.
    try {
      await db.collection(Collections.videos).insertOne(video as any);
      // Enqueue + nudge the (possibly sleeping) worker awake.
      await enqueueJob({ videoId: video._id, userId });
      await wakeWorker();
    } catch (workErr) {
      await releaseUsage(db, userId).catch(() => {});
      throw workErr;
    }
