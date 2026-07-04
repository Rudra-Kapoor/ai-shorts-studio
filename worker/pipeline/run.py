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
