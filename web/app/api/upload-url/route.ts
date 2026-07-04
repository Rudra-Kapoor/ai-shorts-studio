import { NextRequest, NextResponse } from "next/server";
import { getUploadUrl } from "@/lib/r2";

export const runtime = "nodejs";

// POST { filename, contentType, userId }
// → { key, uploadUrl }
// The browser then PUTs the file bytes directly to R2 using uploadUrl.
export async function POST(req: NextRequest) {
  try {
    const { filename, contentType, userId } = await req.json();
    if (!filename || !contentType || !userId) {
      return NextResponse.json(
        { error: "filename, contentType and userId are required" },
        { status: 400 }
      );
    }
    const allowed = ["video/mp4", "video/quicktime", "video/x-matroska", "video/webm"];
    if (!allowed.includes(contentType)) {
      return NextResponse.json(
        { error: `Unsupported type ${contentType}. Use MP4, MOV, MKV or WEBM.` },
        { status: 400 }
      );
    }
