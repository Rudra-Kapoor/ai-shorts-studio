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


def _crop_filter(crop_frac, dims, W, H):
    """Build the crop filter. crop_frac in [0,1] re-centers horizontally around a
    point of interest (e.g. a face); None = centered crop. Uses pre-probed dims
    so we don't run another ffprobe per clip."""
    if crop_frac is None or not dims:
        return f"crop={W}:{H}"
    iw, ih = dims.get("width", 0), dims.get("height", 0)
    if not iw or not ih:
        return f"crop={W}:{H}"
    scaled_w = round(H * iw / ih) if (iw / ih) > (W / H) else W
    if scaled_w > W:
        x = int(min(max(crop_frac * scaled_w - W / 2, 0), scaled_w - W))
        return f"crop={W}:{H}:{x}:0"
    return f"crop={W}:{H}"


def render_clip(src_video: str, start: float, end: float, ass_path: str,
                out_path: str, crop_frac=None, dims=None,
                out_w: int = None, out_h: int = None) -> str:
    """Trim [start, end], scale + crop to out_w x out_h (9:16 by default), burn
    captions."""
    W = out_w or config.OUT_W
    H = out_h or config.OUT_H
    duration = max(0.5, end - start)
    work_dir = os.path.dirname(os.path.abspath(ass_path)) or "."
    ass_name = os.path.basename(ass_path)

    # Fast input-seek to ~SEEK_PAD before the start (skips decoding the rest of
    # the video), then an accurate output-seek for the remainder.
    fast = max(0.0, start - SEEK_PAD)
    rem = start - fast

    # setpts/asetpts force the post-seek streams to start at t=0 so the 0-based
    # ASS captions line up exactly with the audio, regardless of seek behavior.
    vf = (
        f"setpts=PTS-STARTPTS,"
        f"scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"{_crop_filter(crop_frac, dims, W, H)},"
        f"ass={ass_name}"
    )

    # Explicitly map the first video + first audio stream. Real-world sources
    # (esp. YouTube) can have multiple/odd streams, variable frame rate, edit
    # lists, or async audio — without explicit mapping + aresample the clip can
    # come out silent or out of sync. `0:a:0?` makes audio optional so a
    # silent source still renders instead of failing.
    has_audio = True if dims is None else bool(dims.get("has_audio", True))
