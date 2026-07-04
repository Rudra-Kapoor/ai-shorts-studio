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
