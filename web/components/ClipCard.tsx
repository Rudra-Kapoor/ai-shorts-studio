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

  return (
    <div className="card overflow-hidden">
      <div
        className="w-full bg-black"
        style={{ aspectRatio: (clip.aspectRatio || "9:16").replace(":", " / ") }}
      >
        {clip.editedUrl ? (
          <video
            src={clip.editedUrl}
            poster={clip.thumbnailUrl}
            controls
            playsInline
            className="h-full w-full object-contain"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-gray-500">
            {clip.status === "failed" ? "render failed" : "rendering…"}
          </div>
        )}
      </div>

      <div className="space-y-3 p-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-medium leading-tight">{clip.title}</h3>
          <span className="badge bg-brand/20 text-brand">
            🔥 {clip.scores?.virality ?? 0}
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs text-gray-400">
          <span>
            {fmt(clip.startSec)} – {fmt(clip.endSec)} ·{" "}
            {Math.round(clip.durationSec)}s
          </span>
          {clip.captionStyle && (
            <span className="badge bg-edge text-gray-300">{clip.captionStyle}</span>
          )}
        </div>

        {clip.trendMatch && clip.trendMatch.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {clip.trendMatch.map((t) => (
              <span key={t} className="badge bg-brand2/15 text-brand2">
                📈 {t}
              </span>
            ))}
          </div>
        )}

        <div className="space-y-1.5">
          <Score label="Hook" value={clip.scores?.hook ?? 0} />
          <Score label="Emotion" value={clip.scores?.emotion ?? 0} />
          <Score label="Energy" value={clip.scores?.energy ?? 0} />
          {clip.scores?.visual ? (
            <Score label="Visual" value={clip.scores?.visual ?? 0} />
          ) : null}
        </div>

        {clip.reason && (
          <p className="text-xs italic text-gray-500">“{clip.reason}”</p>
        )}

        {clip.caption && (
          <div className="rounded-lg bg-ink p-3 text-sm">
            <p>{clip.caption}</p>
            {clip.hashtags && clip.hashtags.length > 0 && (
              <p className="mt-2 text-brand">
                {clip.hashtags.map((h) => `#${h.replace(/^#/, "")}`).join(" ")}
              </p>
            )}
          </div>
        )}

        <div className="flex flex-wrap gap-2">
          {clip.editedUrl && (
            <a className="btn-primary flex-1" href={clip.editedUrl} download>
              Download
            </a>
          )}
          {clip.srtUrl && (
            <a className="btn-ghost" href={clip.srtUrl} download title="Download captions (.srt)">
              .SRT
            </a>
          )}
          {clip.caption && (
            <button
              className="btn-ghost"
              onClick={() => {
                const tags = (clip.hashtags || [])
                  .map((h) => `#${h.replace(/^#/, "")}`)
                  .join(" ");
                const text = `${clip.caption ?? ""}\n\n${tags}`;
                navigator.clipboard.writeText(text);
                setCopied(true);
                setTimeout(() => setCopied(false), 1500);
              }}
            >
              {copied ? "Copied!" : "Copy caption"}
            </button>
          )}
        </div>
