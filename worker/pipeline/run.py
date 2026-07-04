"""Job orchestrator — runs the full agent pipeline for one video.

  download → guard (audio?) → Transcription Agent (auto-chunk long)
  → Detection + Judge Agent → snap to word boundaries
  → per clip (fault-isolated): Vision + Face + Subtitle + Editing + Thumbnail
    + Trend + Caption agents
  → upload + write status

Design for "no issues":
  - every external call (Groq/Gemini) retries on rate limits (see ai.py)
  - one failing clip is isolated and skipped, not fatal to the whole video
  - reprocessing is idempotent (old clips cleared first)
  - graceful exits for no-audio / no-speech / no-strong-clips
"""
import os
import shutil
import subprocess
import tempfile
import traceback
import uuid
from datetime import datetime, timezone

from . import storage
from . import transcribe
from . import score
from . import subtitles
from . import edit
from . import caption
from . import thumbnail
from . import vision
from . import smartcrop
from . import trends
from . import fetch
import config


def _now():
    return datetime.now(timezone.utc).isoformat()


def _err_detail(e: Exception) -> str:
    """Surface ffmpeg/ffprobe stderr. We run subprocesses with capture_output,
    so a CalledProcessError's str() is just the exit code — the real reason
    (codec, missing stream, filter error) lives in stderr. Pull the tail of it
    so logs and the stored `error` field actually say what went wrong."""
    if isinstance(e, subprocess.CalledProcessError):
        err = e.stderr
        if isinstance(err, bytes):
            err = err.decode("utf-8", "ignore")
        if err:
            tail = " | ".join(err.strip().splitlines()[-3:])
            return f"{e} :: {tail}"
    return str(e)


def _clip_transcript(segments, start, end):
    parts = [s["text"] for s in segments if s["end"] > start and s["start"] < end]
    return " ".join(parts).strip()


def _blend_virality(base: int, visual) -> int:
    return base if visual is None else int(round(0.8 * base + 0.2 * visual))


def _process_clip(video_id, user_id, src, tr, c, i, style, tmp, dims, seeded_trends,
                  out_w, out_h, ratio) -> None:
    """Render + caption a single clip. Raises on hard failure; the caller
    isolates it so other clips still succeed."""
    clip_id = uuid.uuid4().hex
    ass_path = os.path.join(tmp, f"{clip_id}.ass")
    out_path = os.path.join(tmp, f"{clip_id}.mp4")

    # Sample frames once if any vision/face feature is on (reused below).
    frames = []
    if config.VISION_SCORING or config.FACE_CROP:
        frames = edit.extract_frames(src, c["start"], c["end"], 3, tmp, prefix=clip_id)

    visual = vision.score_visual(frames) if config.VISION_SCORING else None
    virality = _blend_virality(c["virality"], visual)
    crop_frac = smartcrop.face_center_frac(frames) if config.FACE_CROP else None

    subtitles.build_ass(tr["words"], c["start"], c["end"], ass_path, style=style,
                        width=out_w, height=out_h)
    edit.render_clip(src, c["start"], c["end"], ass_path, out_path,
                     crop_frac=crop_frac, dims=dims, out_w=out_w, out_h=out_h)

    key = f"clips/{user_id}/{video_id}/{clip_id}.mp4"
    storage.upload_file(out_path, key, content_type="video/mp4")

    thumb_key = None
    if config.THUMBNAILS:
        try:
            thumb_path = os.path.join(tmp, f"{clip_id}.jpg")
            thumbnail.make_thumbnail(out_path, thumb_path, c["title"])
            thumb_key = f"thumbs/{user_id}/{video_id}/{clip_id}.jpg"
            storage.upload_file(thumb_path, thumb_key, content_type="image/jpeg")
        except Exception as e:  # noqa: BLE001 — thumbnail is non-essential
            print(f"[run] thumbnail failed: {e}")

    # SRT caption file — a creator-friendly export they can re-edit/upload.
    srt_key = None
    try:
        srt_path = os.path.join(tmp, f"{clip_id}.srt")
        subtitles.build_srt(tr["segments"], c["start"], c["end"], srt_path)
        srt_key = f"clips/{user_id}/{video_id}/{clip_id}.srt"
        storage.upload_file(srt_path, srt_key, content_type="text/plain; charset=utf-8")
    except Exception as e:  # noqa: BLE001 — non-essential
        print(f"[run] srt failed: {e}")
