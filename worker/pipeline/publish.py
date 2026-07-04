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

    base = f"https://graph.facebook.com/v20.0/{config.IG_USER_ID}"
    # 1) create a REELS container pointing at the public video URL
    create = requests.post(
        f"{base}/media",
        data={"media_type": "REELS", "video_url": video_url,
              "caption": caption[:2200], "access_token": config.IG_ACCESS_TOKEN},
        timeout=60,
    )
    if not create.ok:
        return {"ok": False, "error": f"IG container failed: {create.text[:200]}"}
    container_id = create.json().get("id")

    # 2) wait for the container to finish processing
    for _ in range(20):
        st = requests.get(
            f"https://graph.facebook.com/v20.0/{container_id}",
            params={"fields": "status_code", "access_token": config.IG_ACCESS_TOKEN},
            timeout=30,
        ).json()
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") == "ERROR":
            return {"ok": False, "error": "IG processing error"}
        time.sleep(5)

    # 3) publish
    pub = requests.post(
        f"{base}/media_publish",
        data={"creation_id": container_id, "access_token": config.IG_ACCESS_TOKEN},
        timeout=60,
    )
    if not pub.ok:
        return {"ok": False, "error": f"IG publish failed: {pub.text[:200]}"}
    media_id = pub.json().get("id")
    return {"ok": True, "platform": "instagram", "id": media_id,
            "url": f"https://www.instagram.com/reel/{media_id}"}


# --------------------------- orchestration --------------------------
def publish_clip(clip_id: str, platform: str) -> dict:
    clip = storage.get_clip(clip_id)
    if not clip or not clip.get("editedKey"):
        return {"ok": False, "error": "clip not found or not rendered"}

    title = clip.get("title", "Short")
    caption = clip.get("caption") or title
    tags = clip.get("hashtags", [])
    description = (caption + "\n\n" + " ".join(f"#{t}" for t in tags)).strip()

    if platform == "youtube":
        tmp = tempfile.mkdtemp(prefix="pub_")
        try:
            local = os.path.join(tmp, "clip.mp4")
            storage.download_file(clip["editedKey"], local)
            res = publish_youtube(local, title, description, tags)
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)
    elif platform == "instagram":
        # IG pulls the video from a public URL — hand it a presigned R2 link.
        url = storage.presigned_get(clip["editedKey"], expires=3600)
        res = publish_instagram(url, description)
    else:
        return {"ok": False, "error": f"unknown platform '{platform}'"}

    if res.get("ok"):
        field = "youtubeUrl" if platform == "youtube" else "instagramUrl"
        storage.update_clip(clip_id, {field: res["url"], "published": True})
    return res
