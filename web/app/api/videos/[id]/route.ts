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
