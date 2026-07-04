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
