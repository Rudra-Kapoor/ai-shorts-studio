"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { VideoWithClips } from "@/lib/types";
import StatusBadge from "@/components/StatusBadge";
import ClipCard from "@/components/ClipCard";

export default function VideoPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [data, setData] = useState<VideoWithClips | null>(null);
  const [notFound, setNotFound] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  function stopPolling() {
    if (timer.current) {
      clearInterval(timer.current);
      timer.current = null;
    }
  }
  function startPolling() {
    stopPolling();
    timer.current = setInterval(load, 3000);
  }

  async function load() {
    const r = await fetch(`/api/videos/${id}`);
    if (r.status === 404) {
      setNotFound(true);
      stopPolling();
      return;
    }
    const j = await r.json();
    setData(j.video);
    // Stop polling once there's nothing left to update.
    if (j.video?.status === "done" || j.video?.status === "failed") stopPolling();
  }
