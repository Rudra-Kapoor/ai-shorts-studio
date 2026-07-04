"""FastAPI worker.

The web app pushes jobs onto the Upstash queue and pings POST /wake. This
service may be scaled-to-zero (free tier), so /wake exists purely to wake the
instance and kick off a background drain loop that processes every queued job
until the queue is empty, then lets the instance idle back to sleep.
"""
import threading

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

import config
from pipeline import storage, run, publish, trends

app = FastAPI(title="AI Shorts Studio — Worker")


def _check_secret(secret: str):
    if config.WORKER_SECRET and secret != config.WORKER_SECRET:
        raise HTTPException(status_code=401, detail="bad secret")

# Ensure only one drain loop runs at a time on this instance.
_lock = threading.Lock()
_draining = False


def _drain():
    global _draining
    with _lock:
        if _draining:
            return
        _draining = True
    try:
        processed = 0
        while True:
            job = storage.pop_job()
            if not job:
                break
            video_id = job.get("videoId")
            user_id = job.get("userId")
            if not video_id or not user_id:
                print(f"[worker] skipping malformed job: {job}")
                continue
            print(f"[worker] processing {video_id}")
            run.process_job(video_id, user_id)
            processed += 1
        print(f"[worker] drain complete — {processed} job(s)")
    finally:
        with _lock:
            _draining = False


@app.get("/")
def root():
    return {"service": "ai-shorts-worker", "status": "awake", "draining": _draining}


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/wake", status_code=202)
def wake(x_worker_secret: str = Header(default="")):
    _check_secret(x_worker_secret)
    # Kick off draining in the background and return immediately so the
    # web app's fire-and-forget ping doesn't block.
    threading.Thread(target=_drain, daemon=True).start()
    return {"accepted": True, "draining": True}
