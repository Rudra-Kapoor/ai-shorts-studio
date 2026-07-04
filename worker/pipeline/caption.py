"""Caption + hashtag generation via Gemini Flash (free). One call per clip;
returns a scroll-stopping caption and a set of relevant hashtags."""
import json

import config
from . import ai

PROMPT = """You write viral social captions for short videos.
Given the clip transcript below, return STRICT JSON:
{{"caption": "<1-2 line scroll-stopping caption with 1 emoji>",
  "hashtags": ["<8-12 relevant hashtags, no # symbol>"]}}
{hint}
Transcript:
{transcript}
"""
