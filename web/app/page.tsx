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
