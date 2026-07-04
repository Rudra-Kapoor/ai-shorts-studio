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
