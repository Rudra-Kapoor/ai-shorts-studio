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


def generate_caption(transcript: str, trend_hint: str = "") -> dict:
    if not config.GEMINI_API_KEY:
        # Captions are a nice-to-have; don't fail the whole clip without a key.
        return {"caption": "", "hashtags": []}

    hint = f"\nLean into these trending angles if they fit: {trend_hint}\n" if trend_hint else ""
    try:
        text = ai.gemini_generate(
            [{"text": PROMPT.format(transcript=transcript[:6000], hint=hint)}],
            temperature=0.9,
        )
        data = json.loads(text)
        caption = str(data.get("caption", "")).strip()
        tags = data.get("hashtags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split() if t.strip()]
        tags = [str(t).lstrip("#").strip() for t in tags][:12]
        return {"caption": caption, "hashtags": tags}
    except Exception as e:  # noqa: BLE001 — never let captioning kill a clip
        print(f"[caption] gemini failed: {e}")
        return {"caption": "", "hashtags": []}
