"""Thumbnail generation (Phase 2). Grabs a strong frame from the rendered clip
(captions already burned in) and optionally stamps the title across the top.
Best-effort: if the text overlay fails for any reason, falls back to a clean
frame grab so a clip never fails just because of its thumbnail."""
import os
import re
import subprocess

import config


def _sanitize(text: str) -> str:
    # drawtext is picky about special chars (and we wrap the text in single
    # quotes), so strip anything risky — including apostrophes and colons.
    text = re.sub(r"[^A-Za-z0-9 !?.-]", "", text or "").strip()
    return text[:38].upper()


def make_thumbnail(clip_video: str, out_path: str, title: str = "", at: float = 1.0) -> str:
    title_txt = _sanitize(title)

    # Attempt 1: frame + title bar via drawtext.
    if title_txt and os.path.exists(config.FONT_FILE):
        draw = (
            f"drawbox=x=0:y=ih*0.06:w=iw:h=140:color=black@0.45:t=fill,"
            f"drawtext=fontfile='{config.FONT_FILE}':text='{title_txt}':"
            f"fontcolor=white:fontsize=58:x=(w-text_w)/2:y=ih*0.06+40"
        )
        vf = f"scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,{draw}"
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-ss", f"{at:.2f}", "-i", clip_video,
                 "-frames:v", "1", "-q:v", "3", "-vf", vf, out_path],
                check=True, capture_output=True,
            )
            return out_path
        except subprocess.CalledProcessError:
            pass  # fall through to plain grab

    # Attempt 2: plain frame grab.
    subprocess.run(
        ["ffmpeg", "-y", "-ss", f"{at:.2f}", "-i", clip_video, "-frames:v", "1",
         "-q:v", "3",
         "-vf", "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280",
         out_path],
        check=True, capture_output=True,
    )
    return out_path
