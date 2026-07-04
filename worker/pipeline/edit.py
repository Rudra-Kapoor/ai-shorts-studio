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
