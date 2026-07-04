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

    const workerUrl = process.env.WORKER_URL;
    if (!workerUrl) {
      return NextResponse.json(
        { error: "WORKER_URL not configured" },
        { status: 500 }
      );
    }

    const r = await fetch(`${workerUrl.replace(/\/$/, "")}/publish`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-worker-secret": process.env.WORKER_SECRET || "",
      },
      body: JSON.stringify({ clipId: params.id, platform }),
    });
    const data = await r.json();
    return NextResponse.json(data, { status: r.ok ? 200 : 502 });
  } catch (err: any) {
    return NextResponse.json(
      { error: err.message || "publish failed" },
      { status: 500 }
    );
  }
}
