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
