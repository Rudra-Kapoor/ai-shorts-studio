"use client";

import { useRef, useState } from "react";
import { Identity } from "@/lib/identity";

export default function UploadCard({
  me,
  onCreated,
}: {
  me: Identity;
  onCreated: () => void;
}) {
  const [mode, setMode] = useState<"file" | "url">("file");
  const [title, setTitle] = useState("");
  const [captionStyle, setCaptionStyle] = useState("hormozi");
  const [aspectRatio, setAspectRatio] = useState("9:16");
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState("");
  const [pct, setPct] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const STYLES: { id: string; label: string; hint: string }[] = [
    { id: "hormozi", label: "Hormozi", hint: "Bold white, UPPERCASE" },
    { id: "mrbeast", label: "MrBeast", hint: "Huge yellow pop" },
    { id: "clean", label: "Clean", hint: "Soft, sentence case" },
    { id: "minimal", label: "Minimal", hint: "Small & subtle" },
  ];
  const RATIOS: { id: string; label: string }[] = [
    { id: "9:16", label: "9:16 Shorts" },
    { id: "1:1", label: "1:1 Square" },
    { id: "16:9", label: "16:9 Wide" },
  ];
  const MAX_UPLOAD_MB = 500;

  // --- Upload a file: presign → PUT to storage → register ---
  async function start() {
    if (!file) return;
    if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
      setError(`File is too large (max ${MAX_UPLOAD_MB}MB). Use a shorter clip.`);
      return;
    }
    setBusy(true);
    setError(null);
    setPct(0);
    try {
      const r = await fetch("/api/upload-url", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          filename: file.name,
          contentType: file.type,
          userId: me.userId,
        }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.error || "could not get upload url");

      await new Promise<void>((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open("PUT", j.uploadUrl);
        xhr.setRequestHeader("Content-Type", file.type);
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) setPct(Math.round((e.loaded / e.total) * 100));
        };
        xhr.onload = () =>
          xhr.status >= 200 && xhr.status < 300
            ? resolve()
            : reject(new Error("upload failed: " + xhr.status));
        xhr.onerror = () => reject(new Error("network error during upload"));
        xhr.send(file);
      });

      const reg = await fetch("/api/videos", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          userId: me.userId,
          title: title || file.name,
          key: j.key,
          sizeBytes: file.size,
          captionStyle,
          aspectRatio,
        }),
      });
      const regJson = await reg.json();
      if (!reg.ok) throw new Error(regJson.error || "could not register video");

      setFile(null);
      setTitle("");
      setPct(0);
      if (inputRef.current) inputRef.current.value = "";
      onCreated();
    } catch (e: any) {
      setError(e.message || "something went wrong");
    } finally {
      setBusy(false);
    }
  }

  // --- Paste a link: the worker downloads it, then runs the same pipeline ---
  async function startUrl() {
    const link = url.trim();
    if (!link) return;
    if (!/^https?:\/\/\S+$/i.test(link)) {
      setError("Enter a valid video link (https://…)");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const reg = await fetch("/api/videos", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          userId: me.userId,
          title: title || undefined,
          sourceUrl: link,
          captionStyle,
          aspectRatio,
        }),
      });
      const regJson = await reg.json();
      if (!reg.ok) throw new Error(regJson.error || "could not start");
      setUrl("");
      setTitle("");
      onCreated();
    } catch (e: any) {
      setError(e.message || "something went wrong");
    } finally {
      setBusy(false);
    }
  }

  const canSubmit = mode === "file" ? !!file : url.trim().length > 0;

  return (
    <div className="card p-6">
      <h2 className="text-base font-semibold">Create Shorts</h2>
      <p className="mt-1 text-sm text-gray-400">
        Upload a video or paste a link — we transcribe it, find the viral
        moments, and cut captioned Shorts.
      </p>

      {/* Source toggle */}
      <div className="mt-4 grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={() => { setMode("file"); setError(null); }}
          className={`rounded-xl border p-2 text-center text-sm transition ${
            mode === "file" ? "border-brand bg-brand/10" : "border-edge hover:border-gray-500"
          }`}
        >
          Upload file
        </button>
        <button
          type="button"
          onClick={() => { setMode("url"); setError(null); }}
          className={`rounded-xl border p-2 text-center text-sm transition ${
            mode === "url" ? "border-brand bg-brand/10" : "border-edge hover:border-gray-500"
          }`}
        >
          YouTube link
        </button>
      </div>

      <div className="mt-4 grid gap-3">
        <input
          className="input"
          placeholder="Title (optional)"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />

        <div>
          <label className="mb-1 block text-xs text-gray-400">Caption style</label>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {STYLES.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => setCaptionStyle(s.id)}
                className={`rounded-xl border p-2 text-left transition ${
                  captionStyle === s.id
                    ? "border-brand bg-brand/10"
                    : "border-edge hover:border-gray-500"
                }`}
              >
                <div className="text-sm font-medium">{s.label}</div>
                <div className="text-[11px] text-gray-400">{s.hint}</div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="mb-1 block text-xs text-gray-400">Aspect ratio</label>
          <div className="grid grid-cols-3 gap-2">
            {RATIOS.map((rr) => (
              <button
                key={rr.id}
                type="button"
                onClick={() => setAspectRatio(rr.id)}
                className={`rounded-xl border p-2 text-center text-sm transition ${
                  aspectRatio === rr.id
                    ? "border-brand bg-brand/10"
                    : "border-edge hover:border-gray-500"
                }`}
              >
                {rr.label}
              </button>
            ))}
          </div>
        </div>

        {mode === "file" ? (
          <input
            ref={inputRef}
            className="input file:mr-3 file:rounded-md file:border-0 file:bg-brand file:px-3 file:py-1 file:text-white"
            type="file"
            accept="video/mp4,video/quicktime,video/x-matroska,video/webm"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        ) : (
          <div>
            <input
              className="input"
              type="url"
              inputMode="url"
              placeholder="https://www.youtube.com/watch?v=…"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
            <p className="mt-1 text-[11px] text-gray-500">
              Only use videos you own or have the rights to (your uploads,
              Creative-Commons / public-domain, or with permission).
            </p>
          </div>
        )}

        {busy && mode === "file" && (
          <div className="h-2 w-full overflow-hidden rounded-full bg-ink">
            <div
              className="h-full bg-brand transition-all"
              style={{ width: `${pct}%` }}
            />
          </div>
        )}
        {error && <p className="text-sm text-red-400">{error}</p>}

        <button
          className="btn-primary"
          disabled={!canSubmit || busy}
          onClick={mode === "file" ? start : startUrl}
        >
          {busy
            ? mode === "file"
              ? `Uploading ${pct}%…`
              : "Fetching & queuing…"
            : mode === "file"
            ? "Upload & generate Shorts"
            : "Generate Shorts from link"}
        </button>
      </div>
    </div>
  );
}
