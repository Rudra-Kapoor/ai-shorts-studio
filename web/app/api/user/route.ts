import { NextRequest, NextResponse } from "next/server";
import { getDb, Collections } from "@/lib/mongo";
import { getUsage } from "@/lib/usage";

export const runtime = "nodejs";

// GET /api/user?userId=...  → { user, usage }
export async function GET(req: NextRequest) {
  const userId = req.nextUrl.searchParams.get("userId");
  if (!userId) {
    return NextResponse.json({ error: "userId is required" }, { status: 400 });
  }
  const db = await getDb();
  const user = await db.collection(Collections.users).findOne({ _id: userId as any });
  const usage = await getUsage(db, userId);
  return NextResponse.json({ user, usage });
}
