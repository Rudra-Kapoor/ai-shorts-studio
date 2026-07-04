"""Transcription Agent — Groq Whisper (free, fast). Returns word-level
timestamps for karaoke captions without running Whisper locally.

Robustness:
  - retries on transient errors / rate limits (re-opening the file each try)
  - long videos are auto-split into chunks and stitched back onto the timeline
  - if Whisper returns no word-level timestamps, we synthesize them from the
    segment timings so captions are never blank
"""
import glob
import os
import subprocess
import time

import requests

import config


def extract_audio(video_path: str, out_path: str) -> str:
    """Pull a small mono 16kHz mp3 out of the video for transcription."""
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path,
         "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k", out_path],
        check=True, capture_output=True,
    )
    return out_path


def _transcribe_file(audio_path: str, max_attempts: int = 4) -> dict:
    """One Whisper call with retry. File is re-opened each attempt (multipart
    bodies can't be safely replayed)."""
    last_exc = None
    for attempt in range(max_attempts):
        try:
            with open(audio_path, "rb") as f:
                files = {"file": (os.path.basename(audio_path), f, "audio/mpeg")}
                data = [
                    ("model", config.GROQ_WHISPER_MODEL),
                    ("response_format", "verbose_json"),
                    ("timestamp_granularities[]", "word"),
                    ("timestamp_granularities[]", "segment"),
                ]
                r = requests.post(
                    f"{config.GROQ_BASE}/audio/transcriptions",
                    headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
                    files=files, data=data, timeout=300,
                )
            if r.status_code in (429, 500, 502, 503, 504) and attempt < max_attempts - 1:
                ra = r.headers.get("Retry-After")
                time.sleep(min(float(ra), 30) if ra else min(2 ** attempt, 20))
                continue
            r.raise_for_status()
            j = r.json()
            break
        except requests.RequestException as e:
            last_exc = e
            if attempt < max_attempts - 1:
                time.sleep(min(2 ** attempt, 20))
                continue
            raise
    else:
        if last_exc:
            raise last_exc
        raise RuntimeError("transcription failed")
