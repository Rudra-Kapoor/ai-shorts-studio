"""Fetch a source video from a URL (e.g. YouTube) with yt-dlp.

Used for the "paste a link" flow. Only intended for videos you own or are
otherwise authorized to use (your uploads, Creative-Commons / public-domain, or
a clear fair-use basis). Downloads at up to 1080p and produces an mp4 with
audio so the rest of the pipeline is unchanged.
"""
import glob
import os


def download_youtube(url: str, out_path: str) -> dict:
    """Download `url` to `out_path` (an .mp4). Returns {title, duration}.

    Raises on failure (no formats, private/blocked video, network error); the
    caller marks the job failed and surfaces the message."""
    import yt_dlp  # imported lazily so the worker boots even if it's absent

    work_base = os.path.splitext(out_path)[0]
    opts = {
        # Prefer <=1080p video + audio; fall back to best available with sound.
        "format": "bv*[height<=?1080]+ba/b[height<=?1080]/bv*+ba/b",
        "outtmpl": work_base + ".%(ext)s",
        "merge_output_format": "mp4",
        # Remux whatever we get into mp4 (lossless) so ffmpeg/libx264 is happy.
        "postprocessors": [{"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}],
        "noplaylist": True,      # a watch URL with &list=... → just the video
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "restrictfilenames": True,
        "socket_timeout": 30,
        "retries": 3,
    }
