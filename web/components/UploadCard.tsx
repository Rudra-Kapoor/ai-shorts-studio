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
