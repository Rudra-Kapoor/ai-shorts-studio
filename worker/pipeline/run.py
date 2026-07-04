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
