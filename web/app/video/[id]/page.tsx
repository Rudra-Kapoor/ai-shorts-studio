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

  useEffect(() => {
    load();
    startPolling();
    return () => stopPolling();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function retry() {
    await fetch(`/api/videos/${id}`, { method: "POST" });
    startPolling(); // resume live updates after re-queueing
    load();
  }

  async function del() {
    if (!confirm("Delete this video and all its clips? This cannot be undone.")) return;
    stopPolling();
    await fetch(`/api/videos/${id}`, { method: "DELETE" }).catch(() => {});
    router.push("/");
  }

  if (notFound) {
    return (
      <div className="card p-10 text-center text-gray-400">
        Video not found.{" "}
        <Link href="/" className="text-brand">
          Back to studio
        </Link>
      </div>
    );
  }
  if (!data) return <div className="text-gray-400">Loading…</div>;

  const working = data.status === "queued" || data.status === "processing";

  return (
    <div>
      <Link href="/" className="text-sm text-gray-400 hover:text-gray-200">
        ← Back
      </Link>

      <div className="mt-3 flex items-start justify-between gap-4">
        <h1 className="text-2xl font-semibold">{data.title}</h1>
        <div className="flex items-center gap-3">
          <StatusBadge status={data.status} />
          <button
            onClick={del}
            className="rounded-lg px-2 py-1 text-sm text-gray-500 transition hover:bg-red-500/10 hover:text-red-400"
            title="Delete video"
          >
            🗑
          </button>
        </div>
      </div>

      {/* Progress / status panel */}
      {working && (
        <div className="card mt-4 p-5">
          <div className="flex items-center gap-3">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-edge border-t-brand" />
            <div className="flex-1">
              <div className="text-sm">{data.stage || "Working…"}</div>
              <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-ink">
                <div
                  className="h-full bg-brand transition-all"
                  style={{ width: `${data.progress ?? 5}%` }}
                />
              </div>
            </div>
          </div>
          <p className="mt-3 text-xs text-gray-500">
            The worker may take ~30–60s to wake up on the first job (free tier
            cold start). This page updates automatically.
          </p>
        </div>
      )}

      {data.status === "failed" && (
        <div className="card mt-4 border-red-500/40 p-5">
          <p className="text-sm text-red-300">
            Processing failed: {data.error || "unknown error"}
          </p>
          <button className="btn-ghost mt-3" onClick={retry}>
            Retry
          </button>
        </div>
      )}

      {/* Original preview */}
      {data.originalUrl && (
        <details className="card mt-4 p-4">
          <summary className="cursor-pointer text-sm text-gray-300">
            Original video
          </summary>
          <video
            src={data.originalUrl}
            controls
            className="mt-3 max-h-80 w-full rounded-lg bg-black"
          />
        </details>
      )}
