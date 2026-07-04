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
