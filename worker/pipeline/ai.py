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


def _backoff(attempt: int, retry_after) -> None:
    if retry_after:
        try:
            time.sleep(min(float(retry_after), 30))
            return
        except (TypeError, ValueError):
            pass
    # 1s, 2s, 4s, 8s … capped at 20s
    time.sleep(min(2 ** attempt, 20))


def post_with_retry(url, *, headers=None, json=None, data=None,
                    timeout=120, max_attempts=4) -> requests.Response:
    """POST with retry on 429/5xx. Raises on non-retryable errors or after the
    final attempt. For multipart file uploads (which can't be safely replayed)
    callers should retry around their own file handle instead."""
    last_exc = None
    for attempt in range(max_attempts):
        try:
            r = requests.post(url, headers=headers, json=json, data=data, timeout=timeout)
        except requests.RequestException as e:
            last_exc = e
            if attempt < max_attempts - 1:
                _backoff(attempt, None)
                continue
            raise
        if r.status_code in RETRYABLE and attempt < max_attempts - 1:
            print(f"[ai] {r.status_code} from {url.split('?')[0]} — retry {attempt + 1}")
            _backoff(attempt, r.headers.get("Retry-After"))
            continue
        r.raise_for_status()
        return r
    if last_exc:
        raise last_exc
    raise RuntimeError("post_with_retry: exhausted attempts")


def gemini_generate(parts, temperature: float = 0.7, timeout: int = 60) -> str:
    """Call Gemini generateContent (JSON mode) with retry and return the raw
    text of the first candidate. Shared by the caption + vision agents so the
    URL/body/parse boilerplate lives in one place."""
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.GEMINI_MODEL}:generateContent?key={config.GEMINI_API_KEY}"
    )
    body = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": temperature,
            "response_mime_type": "application/json",
        },
    }
    r = post_with_retry(url, json=body, timeout=timeout)
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]
