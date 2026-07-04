"""Viral-moment detection + Judge Agent.

For a transcript that fits one prompt we make a SINGLE batched Groq call (the
free-tier-friendly design). For long videos we WINDOW the transcript and score
each window, then judge globally — so clips are chosen from across the whole
video instead of only the slice that happened to fit in one prompt. This is the
main fix for "random / no-context" clips on longer videos.

The 'judge' work is the local _select pass: clamp times, enforce length, drop
weak and overlapping picks, and spread them out. Clips are then snapped to real
SENTENCE boundaries (snap_to_sentences) so each one starts and ends on a
complete thought instead of a mid-sentence cut.
"""
import json
import re

import config
from . import ai

SYSTEM = """You are an expert short-form video editor (TikTok / Reels / YouTube Shorts).
You read a timestamped transcript and pick the moments that work best as
STANDALONE clips.

A great clip:
- is SELF-CONTAINED: it makes complete sense on its own, without the rest of the video;
- STARTS at the beginning of the sentence that sets up the moment (never mid-thought);
- has a strong HOOK in the first seconds (a bold claim, question, surprise, or stakes);
- builds to a clear PAYOFF or punchline and ENDS on a complete sentence;
- carries one coherent idea, story, tip, or emotional beat.

Avoid filler, throat-clearing, intros/outros, ad reads, and spans that only make
sense with surrounding context. Return STRICT JSON only."""

CHAR_BUDGET = 14000   # ~ how much transcript fits comfortably in one prompt
MAX_WINDOWS = 8       # cap LLM calls on very long videos


def _seg_line(s) -> str:
    return f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}"


def _prompt(seg_lines, duration, min_s, max_s, n) -> str:
    transcript = "\n".join(seg_lines)
    return f"""Video duration: {duration:.0f}s.

From the transcript below, select the best standalone clips — aim for {n}, but
skip filler (intros, sign-offs, "where was I", ad reads). Don't stop at one clip
if several strong, separate moments exist. ALWAYS return at least one clip — the
single best moment — even if the video is fairly ordinary; never return an empty list.

Each clip must:
- be between {min_s} and {max_s} seconds long. COMBINE several CONSECUTIVE
  sentences so the clip reaches at least {min_s} seconds — never return a single
  short sentence,
- start and end on REAL sentence timestamps from the transcript (use the
  [start-end] numbers shown: start at a sentence's start, end at a later
  sentence's end),
- contain the COMPLETE moment — the setup AND its payoff / resolution / punchline.
  Do NOT end before the conclusion (e.g. don't stop on the cliffhanger and cut
  the result),
- be self-contained and not overlap another pick.

Return STRICT JSON of this exact shape:
{{
  "clips": [
    {{
      "start": <seconds, number — a sentence start from the transcript>,
      "end": <seconds, number — a sentence end from the transcript>,
      "title": "<punchy 3-6 word title>",
      "hook": <0-100>,
      "emotion": <0-100>,
      "energy": <0-100>,
      "virality": <0-100 overall>,
      "reason": "<one sentence: why this stands alone and pops>"
    }}
  ]
}}

Transcript (timestamps in seconds):
{transcript}
"""


def _parse_json(content: str) -> dict:
    """Be forgiving — strip code fences / extract the JSON object if needed."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", content, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return {"clips": []}


def _call_llm(seg_lines, duration, n) -> list:
    body = {
        "model": config.GROQ_LLM_MODEL,
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": _prompt(
                seg_lines, duration, config.MIN_CLIP_SEC, config.MAX_CLIP_SEC, n)},
        ],
    }
    r = ai.post_with_retry(
        f"{config.GROQ_BASE}/chat/completions",
        headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
        json=body, timeout=120,
    )
    content = r.json()["choices"][0]["message"]["content"]
    return _parse_json(content).get("clips", [])
