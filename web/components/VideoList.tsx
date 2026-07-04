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

  return (
    <div className="mt-6 grid gap-3">
      {videos.map((v) => (
        <div
          key={v._id}
          className="card flex items-center justify-between p-4 hover:border-brand"
        >
          <Link
            href={`/video/${v._id}`}
            className="flex min-w-0 flex-1 items-center justify-between gap-3"
          >
            <div className="min-w-0">
              <div className="truncate font-medium">{v.title}</div>
              <div className="mt-1 text-xs text-gray-400">
                {v.stage || "—"}
                {typeof v.progress === "number" && v.status === "processing"
                  ? ` · ${v.progress}%`
                  : ""}
              </div>
            </div>
            <StatusBadge status={v.status} />
          </Link>
          <button
            onClick={() => del(v._id)}
            className="ml-3 rounded-lg px-2 py-1 text-gray-500 transition hover:bg-red-500/10 hover:text-red-400"
            title="Delete video"
            aria-label="Delete video"
          >
            🗑
          </button>
        </div>
      ))}
    </div>
  );
}
