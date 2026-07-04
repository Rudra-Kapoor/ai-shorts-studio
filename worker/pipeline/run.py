"""Job orchestrator — runs the full agent pipeline for one video.

  download → guard (audio?) → Transcription Agent (auto-chunk long)
  → Detection + Judge Agent → snap to word boundaries
  → per clip (fault-isolated): Vision + Face + Subtitle + Editing + Thumbnail
    + Trend + Caption agents
  → upload + write status

Design for "no issues":
  - every external call (Groq/Gemini) retries on rate limits (see ai.py)
  - one failing clip is isolated and skipped, not fatal to the whole video
  - reprocessing is idempotent (old clips cleared first)
  - graceful exits for no-audio / no-speech / no-strong-clips
"""
import os
import shutil
import subprocess
import tempfile
import traceback
import uuid
from datetime import datetime, timezone

from . import storage
from . import transcribe
from . import score
from . import subtitles
from . import edit
from . import caption
from . import thumbnail
from . import vision
from . import smartcrop
from . import trends
from . import fetch
import config


def _now():
    return datetime.now(timezone.utc).isoformat()


def _err_detail(e: Exception) -> str:
    """Surface ffmpeg/ffprobe stderr. We run subprocesses with capture_output,
    so a CalledProcessError's str() is just the exit code — the real reason
    (codec, missing stream, filter error) lives in stderr. Pull the tail of it
    so logs and the stored `error` field actually say what went wrong."""
    if isinstance(e, subprocess.CalledProcessError):
        err = e.stderr
        if isinstance(err, bytes):
            err = err.decode("utf-8", "ignore")
        if err:
            tail = " | ".join(err.strip().splitlines()[-3:])
            return f"{e} :: {tail}"
    return str(e)


def _clip_transcript(segments, start, end):
    parts = [s["text"] for s in segments if s["end"] > start and s["start"] < end]
    return " ".join(parts).strip()


def _blend_virality(base: int, visual) -> int:
    return base if visual is None else int(round(0.8 * base + 0.2 * visual))


def _process_clip(video_id, user_id, src, tr, c, i, style, tmp, dims, seeded_trends,
                  out_w, out_h, ratio) -> None:
    """Render + caption a single clip. Raises on hard failure; the caller
    isolates it so other clips still succeed."""
    clip_id = uuid.uuid4().hex
    ass_path = os.path.join(tmp, f"{clip_id}.ass")
    out_path = os.path.join(tmp, f"{clip_id}.mp4")

    # Sample frames once if any vision/face feature is on (reused below).
    frames = []
    if config.VISION_SCORING or config.FACE_CROP:
        frames = edit.extract_frames(src, c["start"], c["end"], 3, tmp, prefix=clip_id)

    visual = vision.score_visual(frames) if config.VISION_SCORING else None
    virality = _blend_virality(c["virality"], visual)
    crop_frac = smartcrop.face_center_frac(frames) if config.FACE_CROP else None

    subtitles.build_ass(tr["words"], c["start"], c["end"], ass_path, style=style,
                        width=out_w, height=out_h)
    edit.render_clip(src, c["start"], c["end"], ass_path, out_path,
                     crop_frac=crop_frac, dims=dims, out_w=out_w, out_h=out_h)

    key = f"clips/{user_id}/{video_id}/{clip_id}.mp4"
    storage.upload_file(out_path, key, content_type="video/mp4")

    thumb_key = None
    if config.THUMBNAILS:
        try:
            thumb_path = os.path.join(tmp, f"{clip_id}.jpg")
            thumbnail.make_thumbnail(out_path, thumb_path, c["title"])
            thumb_key = f"thumbs/{user_id}/{video_id}/{clip_id}.jpg"
            storage.upload_file(thumb_path, thumb_key, content_type="image/jpeg")
        except Exception as e:  # noqa: BLE001 — thumbnail is non-essential
            print(f"[run] thumbnail failed: {e}")

    # SRT caption file — a creator-friendly export they can re-edit/upload.
    srt_key = None
    try:
        srt_path = os.path.join(tmp, f"{clip_id}.srt")
        subtitles.build_srt(tr["segments"], c["start"], c["end"], srt_path)
        srt_key = f"clips/{user_id}/{video_id}/{clip_id}.srt"
        storage.upload_file(srt_path, srt_key, content_type="text/plain; charset=utf-8")
    except Exception as e:  # noqa: BLE001 — non-essential
        print(f"[run] srt failed: {e}")

    clip_text = _clip_transcript(tr["segments"], c["start"], c["end"])
    matched = trends.match_trends(clip_text, seeded_trends) if config.GEMINI_API_KEY else []
    trend_titles = [m["title"] for m in matched]
    hint = "; ".join(f"{m['title']} (e.g. '{m['hooks'][0]}')" for m in matched if m.get("hooks"))
    extra_tags = []
    for m in matched:
        extra_tags.extend(m.get("hashtags", []))

    cap = caption.generate_caption(clip_text or c["title"], trend_hint=hint)
    hashtags = list(dict.fromkeys((cap["hashtags"] or []) + extra_tags))[:15]

    storage.upsert_clip({
        "_id": clip_id, "videoId": video_id, "userId": user_id, "index": i,
        "title": c["title"], "startSec": c["start"], "endSec": c["end"],
        "durationSec": c["end"] - c["start"],
        "scores": {
            "hook": c["hook"], "emotion": c["emotion"], "energy": c["energy"],
            "visual": visual if visual is not None else 0, "virality": virality,
        },
        "reason": c["reason"], "captionStyle": style, "aspectRatio": ratio,
        "editedKey": key, "thumbnailKey": thumb_key, "srtKey": srt_key,
        "trendMatch": trend_titles,
        "caption": cap["caption"], "hashtags": hashtags,
        "status": "done", "createdAt": _now(),
    })


def _obtain_source(video, video_id, user_id, src) -> None:
    """Put the source video at `src`. Either the already-uploaded original from
    R2, or — for the "paste a link" flow — fetch it from the URL and persist it
    to R2 so playback and retries work without re-downloading."""
    if video.get("originalKey"):
        storage.download_file(video["originalKey"], src)
        return
    url = video.get("sourceUrl")
    if not url:
        raise RuntimeError("No video source (no uploaded file and no link).")
    storage.update_video(video_id, stage="Fetching video from link", progress=8)
    info = fetch.download_youtube(url, src)
    key = f"originals/{user_id}/{video_id}/source.mp4"
    storage.upload_file(src, key, content_type="video/mp4")
    fields = {"originalKey": key}
    title = (info or {}).get("title")
    if title and video.get("title") in (None, "", "YouTube video", "Untitled video"):
        fields["title"] = title[:200]
    storage.update_video(video_id, **fields)


def process_job(video_id: str, user_id: str) -> None:
    video = storage.get_video(video_id)
    if not video:
        print(f"[run] video {video_id} not found, skipping")
        return

    style = video.get("captionStyle") or config.CAPTION_STYLE
    ratio = video.get("aspectRatio") or config.DEFAULT_RATIO
    out_w, out_h = config.dims_for(ratio)
    tmp = tempfile.mkdtemp(prefix="ass_")
    try:
        storage.update_video(video_id, status="processing", stage="Downloading video", progress=5)
        src = os.path.join(tmp, "source.mp4")
        _obtain_source(video, video_id, user_id, src)

        media = edit.probe_media(src)          # one ffprobe → duration + dims + audio
        duration = media["duration"]
        storage.update_video(video_id, durationSec=duration)
        if not media["has_audio"]:
            raise RuntimeError("This video has no audio track — can't transcribe it.")

        # Idempotent: clear any clips left over from a previous/failed attempt.
        storage.delete_clips(video_id)

        # Transcription Agent (auto-chunks long videos)
        storage.update_video(video_id, stage="Transcribing (Whisper)", progress=15)
        audio = transcribe.extract_audio(src, os.path.join(tmp, "audio.mp3"))
        tr = transcribe.transcribe(audio)
        if not tr["segments"]:
            storage.update_video(video_id, status="done", stage="No speech detected", progress=100)
            return

        storage.update_video(video_id, transcript=tr["text"][:20000],
                             stage="Finding viral moments", progress=35)

        # Detection + Judge Agent, then snap to whole sentences for context
        found = score.find_clips(tr["segments"], duration)
        found = score.snap_to_sentences(found, tr["segments"])
        if not found:
            storage.update_video(video_id, status="done", stage="No strong clips found", progress=100)
            return

        total = len(found)
        # Fetch trends once per job (not once per clip).
        seeded_trends = storage.all_trends() if config.GEMINI_API_KEY else []
        succeeded = 0
        for i, c in enumerate(found):
            storage.update_video(video_id, stage=f"Editing clip {i + 1} of {total}",
                                 progress=40 + int((i / total) * 55))
            try:
                _process_clip(video_id, user_id, src, tr, c, i, style, tmp, media,
                              seeded_trends, out_w, out_h, ratio)
                succeeded += 1
            except Exception as e:  # noqa: BLE001 — isolate per-clip failures
                traceback.print_exc()
                print(f"[run] clip {i} failed: {_err_detail(e)}")
