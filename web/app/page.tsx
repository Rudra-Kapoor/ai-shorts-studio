"use client";

import { useEffect, useState } from "react";
import { getIdentity, signOut, Identity } from "@/lib/identity";
import { Usage } from "@/lib/types";
import SignIn from "@/components/SignIn";
import UploadCard from "@/components/UploadCard";
import VideoList from "@/components/VideoList";

export default function Home() {
  const [me, setMe] = useState<Identity | null>(null);
  const [ready, setReady] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [usage, setUsage] = useState<Usage | null>(null);

  async function loadUsage(id: Identity) {
    try {
      const r = await fetch(`/api/user?userId=${encodeURIComponent(id.userId)}`);
      const j = await r.json();
      setUsage(j.usage || null);
    } catch {
      /* non-critical */
    }
  }

  async function syncUser(id: Identity) {
    // Upsert the user record on sign-in, then load their quota.
    await fetch("/api/user", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ userId: id.userId, email: id.email }),
    }).catch(() => {});
    loadUsage(id);
  }

  useEffect(() => {
    const id = getIdentity();
    setMe(id);
    setReady(true);
    if (id) syncUser(id);
  }, []);

  // Refresh quota after each upload.
  useEffect(() => {
    if (me) loadUsage(me);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey]);

  if (!ready) return null;
  if (!me)
    return (
      <SignIn
        onSignIn={() => {
          const id = getIdentity();
          setMe(id);
          if (id) syncUser(id);
        }}
      />
    );

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Your Studio</h1>
          <p className="text-sm text-gray-400">Signed in as {me.email}</p>
        </div>
        <div className="flex items-center gap-3">
          {usage && (
            <span
              className={`badge ${
                usage.remaining > 0
                  ? "bg-emerald-500/15 text-emerald-300"
                  : "bg-red-500/15 text-red-300"
              }`}
              title="Videos you can process today"
            >
              {usage.remaining}/{usage.limit} left today
            </span>
          )}
          <button
            className="btn-ghost text-sm"
            onClick={() => {
              signOut();
              setMe(null);
              setUsage(null);
            }}
          >
            Sign out
          </button>
        </div>
      </div>

      <UploadCard me={me} onCreated={() => setRefreshKey((k) => k + 1)} />
      <VideoList me={me} refreshKey={refreshKey} />
    </div>
  );
}
