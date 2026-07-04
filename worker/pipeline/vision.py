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
