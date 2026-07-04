"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Identity } from "@/lib/identity";
import { Video } from "@/lib/types";
import StatusBadge from "./StatusBadge";

export default function VideoList({
  me,
  refreshKey,
}: {
  me: Identity;
  refreshKey: number;
}) {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loaded, setLoaded] = useState(false);

  async function load() {
    const r = await fetch(`/api/videos?userId=${encodeURIComponent(me.userId)}`);
    const j = await r.json();
    setVideos(j.videos || []);
    setLoaded(true);
  }

  async function del(id: string) {
    if (!confirm("Delete this video and all its clips? This cannot be undone.")) return;
    setVideos((vs) => vs.filter((v) => v._id !== id)); // optimistic
    try {
      const r = await fetch(`/api/videos/${id}`, { method: "DELETE" });
      if (!r.ok) load(); // resync if the server rejected it
    } catch {
      load();
    }
  }

  useEffect(() => {
    load();
    // Poll so statuses (queued → processing → done) update live.
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey]);

  if (loaded && videos.length === 0) {
    return (
      <div className="card mt-6 p-10 text-center text-gray-400">
        No videos yet. Upload one above to generate your first Shorts. ✨
      </div>
    );
  }
