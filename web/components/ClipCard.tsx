"use client";

import { useState } from "react";
import { Clip } from "@/lib/types";

function fmt(s: number) {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, "0")}`;
}

function Score({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-16 text-xs text-gray-400">{label}</span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-ink">
        <div className="h-full bg-brand" style={{ width: `${value}%` }} />
      </div>
      <span className="w-8 text-right text-xs tabular-nums text-gray-300">
        {value}
      </span>
    </div>
  );
}

export default function ClipCard({ clip }: { clip: Clip }) {
  const [copied, setCopied] = useState(false);
  const [posting, setPosting] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  async function publish(platform: "youtube" | "instagram") {
    setPosting(platform);
    setMsg(null);
    try {
      const r = await fetch(`/api/clips/${clip._id}/publish`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ platform }),
      });
      const data = await r.json();
      if (data.ok && data.url) setMsg(`Posted → ${data.url}`);
      else setMsg(data.error || "Could not post (check setup).");
    } catch (e: any) {
      setMsg(e.message || "post failed");
    } finally {
      setPosting(null);
    }
  }
