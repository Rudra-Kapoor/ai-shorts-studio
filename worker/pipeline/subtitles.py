"""Build an ASS subtitle file for a clip, in one of several viral styles.

Styles (Phase 2):
  - hormozi : big bold WHITE, thick black outline, UPPERCASE, 1-3 words
  - mrbeast : huge bold YELLOW, extra-thick outline, UPPERCASE, 1-2 words
  - minimal : smaller clean white, thin outline, normal case, fuller lines
  - clean   : medium white, soft outline, sentence-case, 3-4 words

Times are made relative to the clip start so they line up with the trimmed
video. Uses the Liberation font installed in the Docker image so libass can
actually render the text.
"""
import config

# Per-style configuration. Colours are ASS &HAABBGGRR.
STYLES = {
    "hormozi": dict(size=120, primary="&H00FFFFFF", outline_col="&H00101010",
                    bold=-1, outline=7, shadow=3, marginv=360,
                    uppercase=True, max_words=3, max_chars=16, fade=(60, 0)),
    "mrbeast": dict(size=132, primary="&H0000FFFF", outline_col="&H00000000",
                    bold=-1, outline=8, shadow=4, marginv=380,
                    uppercase=True, max_words=2, max_chars=12, fade=(40, 0)),
    "minimal": dict(size=66, primary="&H00FFFFFF", outline_col="&H00000000",
                    bold=0, outline=2, shadow=0, marginv=240,
                    uppercase=False, max_words=6, max_chars=30, fade=(80, 0)),
    "clean":   dict(size=84, primary="&H00FFFFFF", outline_col="&H00141414",
                    bold=-1, outline=4, shadow=2, marginv=300,
                    uppercase=False, max_words=4, max_chars=20, fade=(60, 0)),
}


def _header(s, w: int, h: int) -> str:
    # Scale type/outline/position to the output height so captions look right at
    # any aspect ratio (9:16 → factor 1.0, the tuned baseline).
    factor = h / 1920.0
    size = max(int(s["size"] * factor), 28)
    outline = max(round(s["outline"] * factor, 1), 2)
    shadow = round(s["shadow"] * factor, 1)
    marginv = int(h * 0.18)
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{config.FONT_NAME},{size},{s['primary']},&H000000FF,{s['outline_col']},&H64000000,{s['bold']},0,0,0,100,100,0,0,1,{outline},{shadow},2,90,90,{marginv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _ass_time(t: float) -> str:
    if t < 0:
        t = 0.0
    cs = int(round(t * 100))
    h = cs // 360000
    m = (cs % 360000) // 6000
    s = (cs % 6000) // 100
    c = cs % 100
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"


def _clean(text: str, uppercase: bool) -> str:
    text = text.replace("{", "").replace("}", "").replace("\n", " ").strip()
    return text.upper() if uppercase else text


def _group(words, max_words, max_chars):
    cards, cur, cur_chars = [], [], 0
    for w in words:
        token = w["word"].strip()
        if not token:
            continue
        if cur and (len(cur) >= max_words or cur_chars + len(token) > max_chars):
            cards.append(cur)
            cur, cur_chars = [], 0
        cur.append(w)
        cur_chars += len(token) + 1
    if cur:
        cards.append(cur)
    return cards


def build_ass(words, clip_start: float, clip_end: float, out_path: str,
              style: str = "hormozi", width: int = None, height: int = None) -> str:
    s = STYLES.get((style or "").lower(), STYLES["hormozi"])
    w = width or config.OUT_W
    h = height or config.OUT_H
    in_clip = [w2 for w2 in words if w2["end"] > clip_start and w2["start"] < clip_end]
    events = []

    for card in _group(in_clip, s["max_words"], s["max_chars"]):
        start = max(0.0, card[0]["start"] - clip_start)
        end = max(start + 0.2, card[-1]["end"] - clip_start)
        text = _clean(" ".join(wd["word"].strip() for wd in card), s["uppercase"])
        if not text:
            continue
        fin, fout = s["fade"]
        body = f"{{\\fad({fin},{fout})\\q2}}{text}"
        events.append(
            f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Cap,,0,0,0,,{body}"
        )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(_header(s, w, h))
        f.write("\n".join(events))
        f.write("\n")
    return out_path


def _srt_time(t: float) -> str:
    if t < 0:
        t = 0.0
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(segments, clip_start: float, clip_end: float, out_path: str) -> str:
    """Standard .srt caption file for the clip (for re-editing / accessibility /
    uploading alongside the video). Built from sentence-level segments."""
    blocks, idx = [], 1
    for seg in segments:
        if seg["end"] <= clip_start or seg["start"] >= clip_end:
            continue
        st = max(0.0, seg["start"] - clip_start)
        en = max(st + 0.3, min(seg["end"], clip_end) - clip_start)
        text = seg["text"].strip()
        if not text:
            continue
        blocks.append(f"{idx}\n{_srt_time(st)} --> {_srt_time(en)}\n{text}\n")
        idx += 1
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(blocks))
    return out_path
