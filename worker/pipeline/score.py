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


def _windows(segments, budget):
    """Group consecutive segments into prompt-sized windows (by char count) so the
    whole video gets scored, not just the part that fits in one prompt."""
    windows, cur, cur_len = [], [], 0
    for s in segments:
        ln = len(s.get("text", "")) + 18
        if cur and cur_len + ln > budget:
            windows.append(cur)
            cur, cur_len = [], 0
        cur.append(s)
        cur_len += ln
    if cur:
        windows.append(cur)
    return windows


def find_clips(segments, duration: float) -> list:
    if not config.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set")
    if not segments:
        return []

    windows = _windows(segments, CHAR_BUDGET)
    # On very long videos, merge windows so we make at most MAX_WINDOWS calls.
    if len(windows) > MAX_WINDOWS:
        group = len(windows) // MAX_WINDOWS + 1
        windows = [
            [s for w in windows[i:i + group] for s in w]
            for i in range(0, len(windows), group)
        ]

    raw = []
    for win in windows:
        try:
            raw.extend(_call_llm([_seg_line(s) for s in win], duration, config.MAX_CLIPS))
        except Exception as e:  # noqa: BLE001 — one window failing shouldn't kill the rest
            print(f"[score] window scoring failed: {e}")

    # Normalize → snap/extend to full sentence spans → judge/dedup. Snapping
    # BEFORE selection means the model can point at a short sentence and we grow
    # it into a proper 15-60s clip, instead of the short pick being discarded.
    cands = snap_to_sentences(_normalize(raw, duration), segments)
    picked = _select(cands)
    if not picked:
        # The model returned nothing usable — guarantee clips anyway from the
        # densest speech spans, so the user never gets "no clips".
        print("[score] no usable LLM picks — using speech-density fallback")
        picked = snap_to_sentences(_fallback_clips(segments, duration), segments)
    return picked


def _fallback_clips(segments, duration):
    """Deterministic backup: walk the transcript and form non-overlapping spans
    (up to MAX_CLIP_SEC) on sentence boundaries, preferring the ones with the
    most speech. Guarantees output for any video that has speech."""
    if not segments:
        return []
    spans, i, n = [], 0, len(segments)
    while i < n:
        st = segments[i]["start"]
        en, words, j = st, 0, i
        while j < n and segments[j]["end"] - st <= config.MAX_CLIP_SEC:
            en = segments[j]["end"]
            words += len(segments[j].get("text", "").split())
            j += 1
        if en - st >= min(config.MIN_CLIP_SEC, duration):
            spans.append({"start": st, "end": min(en, duration), "words": words})
        i = max(j, i + 1)
    if not spans:  # very short video → just use the whole thing
        spans = [{"start": 0.0, "end": min(duration, config.MAX_CLIP_SEC), "words": 1}]
    spans.sort(key=lambda s: s["words"], reverse=True)
    picked = []
    for s in spans:
        no_overlap = all(s["end"] <= p["start"] or s["start"] >= p["end"] for p in picked)
        if no_overlap:
            picked.append({
                "start": s["start"], "end": s["end"], "title": "Highlight",
                "hook": 50, "emotion": 50, "energy": 50, "virality": 50,
                "reason": "Selected as one of the most speech-dense moments.",
            })
        if len(picked) >= config.MAX_CLIPS:
            break
    picked.sort(key=lambda x: x["start"])
    return picked


def _normalize(raw, duration):
    """Parse raw LLM clips: clamp to the video, cap at MAX, keep scores. Short
    clips are kept (not dropped) — snap_to_sentences grows them to a valid span."""
    out = []
    for c in raw:
        try:
            start = max(0.0, float(c["start"]))
            end = min(duration, float(c["end"]))
        except (KeyError, TypeError, ValueError):
            continue
        if end <= start:
            continue
        if end - start > config.MAX_CLIP_SEC:
            end = start + config.MAX_CLIP_SEC
        out.append({
            "start": start, "end": end,
            "title": str(c.get("title", "Untitled clip"))[:80],
            "hook": _score(c.get("hook")),
            "emotion": _score(c.get("emotion")),
            "energy": _score(c.get("energy")),
            "virality": _score(c.get("virality")),
            "reason": str(c.get("reason", ""))[:200],
        })
    return out


def _select(cands):
    """Judge pass over already-snapped candidates: keep valid-length clips, drop
    weak/overlapping, keep the best and spread them out."""
    valid = [c for c in cands
             if config.MIN_CLIP_SEC <= (c["end"] - c["start"]) <= config.MAX_CLIP_SEC]
    pool0 = valid or cands  # very short videos may not reach MIN — keep them anyway
    pool0.sort(key=lambda x: x["virality"], reverse=True)
    # Prefer clips actually worth clipping; if none clear the bar, keep the best one.
    strong = [c for c in pool0 if c["virality"] >= config.MIN_VIRALITY]
    pool = strong or pool0[:1]

    picked = []
    for c in pool:
        if all(c["end"] <= p["start"] or c["start"] >= p["end"] for p in picked):
            picked.append(c)
        if len(picked) >= config.MAX_CLIPS:
            break
    picked.sort(key=lambda x: x["start"])  # chronological for display
    return picked


def snap_to_sentences(clips, segments):
    """Align each clip's start/end to real sentence boundaries so every clip
    begins and ends on a complete thought (no mid-sentence, context-free cuts).
    Keeps the result within [MIN, MAX]; falls back to the original times if it
    can't form a valid window."""
    if not clips or not segments:
        return clips
    seg_starts = sorted(s["start"] for s in segments)
    seg_ends = sorted(s["end"] for s in segments)
    out = []
    for c in clips:
        ns = min(seg_starts, key=lambda x: abs(x - c["start"]))
        ne = min(seg_ends, key=lambda x: abs(x - c["end"]))
        # too short → extend to the next sentence end that still fits
        if ne - ns < config.MIN_CLIP_SEC:
            for e in seg_ends:
                if e > ne and (e - ns) <= config.MAX_CLIP_SEC:
                    ne = e
                    if ne - ns >= config.MIN_CLIP_SEC:
                        break
        # too long → pull end back to the last sentence end within MAX
        if ne - ns > config.MAX_CLIP_SEC:
            fits = [e for e in seg_ends if ns < e <= ns + config.MAX_CLIP_SEC]
            if fits:
                ne = max(fits)
        cc = dict(c)
        if ne > ns:  # apply the snapped/extended boundaries (best effort)
            cc["start"], cc["end"] = ns, ne
        out.append(cc)
    return out


def _score(v):
    try:
        return max(0, min(100, int(round(float(v)))))
    except (TypeError, ValueError):
        return 50
