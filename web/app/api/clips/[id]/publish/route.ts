import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

// POST /api/clips/:id/publish { platform: "youtube" | "instagram" }
// Forwards to the worker, which holds the OAuth credentials and does the upload.
export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { platform } = await req.json();
    if (!["youtube", "instagram"].includes(platform)) {
      return NextResponse.json({ error: "invalid platform" }, { status: 400 });
    }
