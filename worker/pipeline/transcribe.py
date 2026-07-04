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
