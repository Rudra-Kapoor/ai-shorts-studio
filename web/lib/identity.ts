"use client";

// Lightweight demo identity. For v1 we store a userId in localStorage so the
// app works with zero auth setup. To go to production, swap this for Clerk or
// Supabase Auth (see README → "Adding real auth").

const KEY = "ass_user";

export interface Identity {
  userId: string;
  email: string;
}

export function getIdentity(): Identity | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Identity;
  } catch {
    return null;
  }
}
