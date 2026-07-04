"""FFmpeg editing: probe media, extract frames, and render a 9:16 clip with
burned-in captions. Optional face-aware horizontal crop (crop_frac); falls back
to a centered crop when not provided.

Performance: rendering uses a fast input-seek (skips decoding everything before
the clip) plus an accurate output-seek for the remainder. The output-seek resets
timestamps to 0 so the 0-based ASS captions stay perfectly in sync."""
import json
import os
import subprocess

import config

# Seconds of input we keep before the clip start for the fast/accurate seek.
SEEK_PAD = 10.0


def probe_media(video_path: str) -> dict:
    """ONE ffprobe call → duration, video dimensions, and whether audio exists.
    Replaces the old separate duration/dims/has-audio probes."""
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", video_path],
        check=True, capture_output=True, text=True,
    )
    data = json.loads(out.stdout)
    duration = float(data.get("format", {}).get("duration", 0.0) or 0.0)
    width = height = 0
    has_audio = False
    for s in data.get("streams", []):
        kind = s.get("codec_type")
        if kind == "video" and not width:
            width = int(s.get("width", 0) or 0)
            height = int(s.get("height", 0) or 0)
        elif kind == "audio":
            has_audio = True
    return {"duration": duration, "width": width, "height": height, "has_audio": has_audio}


def extract_frames(src_video: str, start: float, end: float, n: int, out_dir: str,
                   prefix: str = "f") -> list:
    """Grab n evenly-spaced small JPEG frames from [start, end] (for vision
    scoring and face detection). Fast input-seek; downscaled to keep them tiny."""
    dur = max(0.2, end - start)
    paths = []
    for i in range(n):
        t = start + dur * ((i + 0.5) / n)
        p = os.path.join(out_dir, f"{prefix}_{i}.jpg")
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-ss", f"{t:.3f}", "-i", src_video,
                 "-frames:v", "1", "-q:v", "3", "-vf", "scale=640:-1", p],
                check=True, capture_output=True,
            )
            paths.append(p)
        except subprocess.CalledProcessError:
            continue
    return paths
