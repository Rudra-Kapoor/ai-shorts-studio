import { VideoStatus } from "@/lib/types";

const MAP: Record<VideoStatus, { label: string; cls: string }> = {
  uploading: { label: "Uploading", cls: "bg-gray-700 text-gray-200" },
  queued: { label: "Queued", cls: "bg-amber-500/20 text-amber-300" },
  processing: { label: "Processing", cls: "bg-brand/20 text-brand" },
  done: { label: "Ready", cls: "bg-emerald-500/20 text-emerald-300" },
  failed: { label: "Failed", cls: "bg-red-500/20 text-red-300" },
};

export default function StatusBadge({ status }: { status: VideoStatus }) {
  const s = MAP[status] || MAP.queued;
  return <span className={`badge ${s.cls}`}>{s.label}</span>;
}
