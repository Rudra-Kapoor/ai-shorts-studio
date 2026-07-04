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
