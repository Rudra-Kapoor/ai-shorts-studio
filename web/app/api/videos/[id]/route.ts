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
