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
