"""Resilient HTTP for the AI agents.

Free-tier APIs (Groq, Gemini) regularly return 429 (rate limit) or transient
5xx. Without retries a single blip fails the whole job. This wraps requests
with exponential backoff that honors the `Retry-After` header on 429s.

Used by: transcribe, score, caption, vision, trends.
"""
import time

import requests

import config

RETRYABLE = {429, 500, 502, 503, 504}
