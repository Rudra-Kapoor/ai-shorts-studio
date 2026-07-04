"""Gemini-vision keyframe scoring (Phase 2, optional). Sends a couple of small
keyframes to Gemini Flash and asks for a 0-100 'visual engagement' score
(motion, faces, expressive visuals). Blended into the virality score.

Returns None on any failure or when disabled, so the caller just skips it."""
import base64
import json

import config
from . import ai

PROMPT = (
    "These are frames from a short vertical video clip. Rate its VISUAL "
    "engagement for social media from 0-100 (faces, motion, expression, color, "
    "visual interest). Return STRICT JSON: {\"visual\": <0-100>}."
)


def score_visual(frame_paths) -> "int | None":
    if not config.GEMINI_API_KEY or not frame_paths:
        return None

    parts = [{"text": PROMPT}]
    for p in frame_paths[:3]:
        try:
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            parts.append({"inline_data": {"mime_type": "image/jpeg", "data": b64}})
        except OSError:
            continue
    if len(parts) == 1:
        return None

    try:
        text = ai.gemini_generate(parts, temperature=0.2)
        val = int(round(float(json.loads(text).get("visual", 50))))
        return max(0, min(100, val))
    except Exception as e:  # noqa: BLE001
        print(f"[vision] scoring failed: {e}")
        return None
