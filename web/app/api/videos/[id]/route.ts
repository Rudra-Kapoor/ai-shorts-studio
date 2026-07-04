import { NextRequest, NextResponse } from "next/server";
import { getDb, Collections } from "@/lib/mongo";
import { getDownloadUrl, deleteObjects } from "@/lib/r2";
import { enqueueJob, wakeWorker } from "@/lib/redis";

export const runtime = "nodejs";

// GET /api/videos/:id  → the video plus its clips, with fresh presigned URLs.
export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  const db = await getDb();
  const video = await db
    .collection(Collections.videos)
    .findOne({ _id: params.id as any });
  if (!video) {
    return NextResponse.json({ error: "not found" }, { status: 404 });
  }

  const clips = await db
    .collection(Collections.clips)
    .find({ videoId: params.id })
    .sort({ index: 1 })
    .toArray();

  // Mint short-lived download URLs so the browser can play private R2 objects.
  if (video.originalKey) {
    (video as any).originalUrl = await getDownloadUrl(video.originalKey);
  }
  for (const c of clips) {
    if (c.editedKey) (c as any).editedUrl = await getDownloadUrl(c.editedKey);
    if (c.thumbnailKey)
      (c as any).thumbnailUrl = await getDownloadUrl(c.thumbnailKey);
    if (c.srtKey) (c as any).srtUrl = await getDownloadUrl(c.srtKey);
  }

  return NextResponse.json({ video: { ...video, clips } });
}

// POST /api/videos/:id  → retry a failed/stuck video.
export async function POST(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  const db = await getDb();
  const video = await db
    .collection(Collections.videos)
    .findOne({ _id: params.id as any });
  if (!video) {
    return NextResponse.json({ error: "not found" }, { status: 404 });
  }

  await db.collection(Collections.videos).updateOne(
    { _id: params.id as any },
    {
      $set: {
        status: "queued",
        stage: "Re-queued",
        progress: 0,
        error: null,
        updatedAt: new Date().toISOString(),
      },
    }
  );
  await enqueueJob({ videoId: params.id, userId: video.userId });
  await wakeWorker();

  return NextResponse.json({ ok: true });
}

// DELETE /api/videos/:id  → remove the video, its clips, and all R2 objects.
export async function DELETE(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  const db = await getDb();
  const video = await db
    .collection(Collections.videos)
    .findOne({ _id: params.id as any });
  if (!video) {
    return NextResponse.json({ error: "not found" }, { status: 404 });
  }

  const clips = await db
    .collection(Collections.clips)
    .find({ videoId: params.id })
    .toArray();
