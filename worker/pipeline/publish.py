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
