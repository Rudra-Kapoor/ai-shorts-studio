import { Db } from "mongodb";
import { Collections } from "./mongo";

// Simple per-user daily quota. Protects the free AI tiers from a single user
// burning the whole quota, and gives the app real "account" structure.
export const MAX_VIDEOS_PER_DAY = parseInt(
  process.env.MAX_VIDEOS_PER_DAY || "10",
  10
);

function today(): string {
  return new Date().toISOString().slice(0, 10); // YYYY-MM-DD (UTC)
}

export async function getUsage(db: Db, userId: string) {
  const u = await db.collection(Collections.users).findOne({ _id: userId as any });
  const used = u && u.dayKey === today() ? u.videosToday || 0 : 0;
  return {
    used,
    limit: MAX_VIDEOS_PER_DAY,
    remaining: Math.max(0, MAX_VIDEOS_PER_DAY - used),
  };
}
