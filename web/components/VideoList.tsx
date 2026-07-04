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
