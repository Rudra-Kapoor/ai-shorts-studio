"""Thumbnail generation (Phase 2). Grabs a strong frame from the rendered clip
(captions already burned in) and optionally stamps the title across the top.
Best-effort: if the text overlay fails for any reason, falls back to a clean
frame grab so a clip never fails just because of its thumbnail."""
import os
import re
import subprocess

import config


def _sanitize(text: str) -> str:
    # drawtext is picky about special chars (and we wrap the text in single
    # quotes), so strip anything risky — including apostrophes and colons.
    text = re.sub(r"[^A-Za-z0-9 !?.-]", "", text or "").strip()
    return text[:38].upper()
