"""Auto-post to YouTube Shorts and Instagram Reels (Phase 3, optional).

Both are opt-in and need YOUR OAuth setup (env vars). They use plain HTTP so
there's no heavy SDK. If the relevant env vars are missing, the publisher
returns a clear, actionable error instead of failing the app.

YouTube  : OAuth refresh-token flow (YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN)
Instagram: Graph API for a Business/Creator account (IG_USER_ID / IG_ACCESS_TOKEN)
"""
import os
import tempfile
import time

import requests

import config
from . import storage


# ----------------------------- YouTube -----------------------------
def _yt_access_token() -> str:
    r = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": config.YT_CLIENT_ID,
            "client_secret": config.YT_CLIENT_SECRET,
            "refresh_token": config.YT_REFRESH_TOKEN,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def publish_youtube(file_path: str, title: str, description: str, tags: list) -> dict:
    if not (config.YT_CLIENT_ID and config.YT_CLIENT_SECRET and config.YT_REFRESH_TOKEN):
        return {"ok": False, "error": "YouTube not configured (set YT_CLIENT_ID/SECRET/REFRESH_TOKEN)"}

    token = _yt_access_token()
    metadata = {
        "snippet": {"title": title[:95] or "Short", "description": description[:4900],
                    "tags": tags[:15], "categoryId": "22"},
        "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False},
    }
    size = os.path.getsize(file_path)

    # 1) start a resumable session
    start = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos"
        "?uploadType=resumable&part=snippet,status",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(size),
        },
        json=metadata, timeout=30,
    )
    start.raise_for_status()
    upload_url = start.headers["Location"]

    # 2) upload the bytes
    with open(file_path, "rb") as f:
        up = requests.put(
            upload_url,
            headers={"Content-Type": "video/mp4", "Content-Length": str(size)},
            data=f, timeout=600,
        )
    up.raise_for_status()
    vid = up.json()["id"]
    return {"ok": True, "platform": "youtube", "url": f"https://youtu.be/{vid}", "id": vid}


# ----------------------------- Instagram ----------------------------
def publish_instagram(video_url: str, caption: str) -> dict:
    if not (config.IG_USER_ID and config.IG_ACCESS_TOKEN):
        return {"ok": False, "error": "Instagram not configured (set IG_USER_ID/IG_ACCESS_TOKEN)"}
