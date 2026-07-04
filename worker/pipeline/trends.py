"""Trend intelligence (Phase 3) — RAG-lite, no heavy vector DB.

We embed each clip's transcript with Gemini embeddings and compare (cosine)
against a small set of seeded "trends" stored in MongoDB. The closest trends'
hooks/hashtags are fed into caption generation and shown on the clip.

This deliberately avoids ChromaDB/Qdrant: for a hand-seeded trend set, an
in-memory cosine over a Mongo collection is plenty and uses no extra memory —
important on a 512MB free worker. There is no free, legal live-trend API, so
trends are seeded manually (see seed_trends + POST /seed-trends)."""
import math

import config
from . import ai
from . import storage

# Starter trend set — edit/extend freely, then re-seed.
DEFAULT_TRENDS = [
    {"_id": "t_question_hook",
     "title": "Bold question hook",
     "text": "Open with a provocative question that challenges a common belief and promises a surprising answer.",
     "hooks": ["What nobody tells you about", "Why you're wrong about", "The truth about"],
     "style": "hormozi",
     "hashtags": ["fyp", "mindset", "motivation"]},
    {"_id": "t_number_list",
     "title": "Numbered secrets",
     "text": "List a specific number of secrets, mistakes, or tips, counting them down fast.",
     "hooks": ["3 things I wish I knew", "5 mistakes that cost me", "Top 3 reasons"],
     "style": "mrbeast",
     "hashtags": ["tips", "learnontiktok", "viral"]},
    {"_id": "t_story_transformation",
     "title": "Transformation story",
     "text": "A short before/after personal story of struggle leading to a payoff or lesson.",
     "hooks": ["I went from", "6 months ago I", "This changed everything"],
     "style": "clean",
     "hashtags": ["story", "growth", "inspiration"]},
    {"_id": "t_contrarian",
     "title": "Contrarian take",
     "text": "State a strong contrarian opinion against mainstream advice and defend it.",
     "hooks": ["Unpopular opinion", "Stop doing this", "Everyone is lying about"],
     "style": "hormozi",
     "hashtags": ["opinion", "debate", "fyp"]},
    {"_id": "t_how_to",
     "title": "Fast how-to",
     "text": "A crisp step-by-step on achieving a concrete result quickly.",
     "hooks": ["How to", "The fastest way to", "Do this to"],
     "style": "minimal",
     "hashtags": ["howto", "tutorial", "tips"]},
]


def embed(text: str):
    """Gemini embedding for a piece of text. Returns a vector or None."""
    if not config.GEMINI_API_KEY or not text.strip():
        return None
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.GEMINI_EMBED_MODEL}:embedContent?key={config.GEMINI_API_KEY}"
    )
    body = {
        "model": f"models/{config.GEMINI_EMBED_MODEL}",
        "content": {"parts": [{"text": text[:8000]}]},
    }
    try:
        r = ai.post_with_retry(url, json=body, timeout=30)
        return r.json()["embedding"]["values"]
    except Exception as e:  # noqa: BLE001
        print(f"[trends] embed failed: {e}")
        return None


def _cosine(a, b) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def seed_default_trends() -> int:
    """Embed + upsert the default trend set. Idempotent. Returns count seeded."""
    n = 0
    for t in DEFAULT_TRENDS:
        vec = embed(t["text"])
        doc = dict(t)
        if vec:
            doc["embedding"] = vec
        storage.upsert_trend(doc)
        n += 1
    return n
