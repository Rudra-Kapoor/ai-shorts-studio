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

// POST /api/user { userId, email, name? }  → upsert on sign-in
export async function POST(req: NextRequest) {
  try {
    const { userId, email, name } = await req.json();
    if (!userId) {
      return NextResponse.json({ error: "userId is required" }, { status: 400 });
    }
    const db = await getDb();
    await db.collection(Collections.users).updateOne(
      { _id: userId as any },
      {
        $set: { email: email || userId, ...(name ? { name } : {}), updatedAt: new Date().toISOString() },
        $setOnInsert: { subscription: "free", createdAt: new Date().toISOString() },
      },
      { upsert: true }
    );
    const usage = await getUsage(db, userId);
    return NextResponse.json({ ok: true, usage });
  } catch (err: any) {
    return NextResponse.json({ error: err.message || "failed" }, { status: 500 });
  }
}
