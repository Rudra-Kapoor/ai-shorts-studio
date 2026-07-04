"""Storage + queue + DB access for the worker.

- R2 (S3-compatible) for video files via boto3
- MongoDB Atlas for document state via pymongo
- Upstash Redis (REST) for the job queue
"""
import json
from datetime import datetime, timezone

import boto3
import requests
from botocore.config import Config
from pymongo import MongoClient

import config

# --- R2 (boto3 S3 client) ---
_s3 = boto3.client(
    "s3",
    endpoint_url=config.R2_ENDPOINT,
    aws_access_key_id=config.R2_ACCESS_KEY_ID,
    aws_secret_access_key=config.R2_SECRET_ACCESS_KEY,
    region_name="auto",
    config=Config(
        signature_version="s3v4",
        s3={"addressing_style": "path" if config.S3_PATH_STYLE else "auto"},
    ),
)


def download_file(key: str, dest_path: str) -> None:
    _s3.download_file(config.R2_BUCKET, key, dest_path)


def upload_file(local_path: str, key: str, content_type: str = "video/mp4") -> str:
    _s3.upload_file(
        local_path,
        config.R2_BUCKET,
        key,
        ExtraArgs={"ContentType": content_type},
    )
    return key


def presigned_get(key: str, expires: int = 3600) -> str:
    """A short-lived public GET url (used so Instagram can pull a private clip)."""
    return _s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": config.R2_BUCKET, "Key": key},
        ExpiresIn=expires,
    )


# --- MongoDB ---
_mongo = MongoClient(config.MONGODB_URI)
_db = _mongo[config.MONGODB_DB]
videos = _db["videos"]
clips = _db["clips"]
trends = _db["trends"]


def get_video(video_id: str):
    return videos.find_one({"_id": video_id})


def update_video(video_id: str, **fields) -> None:
    fields["updatedAt"] = datetime.now(timezone.utc).isoformat()
    videos.update_one({"_id": video_id}, {"$set": fields})


def upsert_clip(clip: dict) -> None:
    clips.update_one({"_id": clip["_id"]}, {"$set": clip}, upsert=True)


def get_clip(clip_id: str):
    return clips.find_one({"_id": clip_id})


def update_clip(clip_id: str, fields: dict) -> None:
    clips.update_one({"_id": clip_id}, {"$set": fields})


def delete_clips(video_id: str) -> int:
    """Remove a video's existing clips — so reprocessing/retry doesn't pile up
    duplicates."""
    return clips.delete_many({"videoId": video_id}).deleted_count


# --- Trends (Phase 3) ---
def all_trends() -> list:
    return list(trends.find({}))


def upsert_trend(trend: dict) -> None:
    trends.update_one({"_id": trend["_id"]}, {"$set": trend}, upsert=True)


def ensure_indexes() -> None:
    """Idempotent — keeps list/lookup queries fast as data grows."""
    try:
        videos.create_index([("userId", 1), ("createdAt", -1)])
        clips.create_index("videoId")
    except Exception as e:  # noqa: BLE001
        print(f"[storage] index setup skipped: {e}")


ensure_indexes()


# --- Upstash Redis (REST) queue ---
def pop_job():
    """RPOP one job from the queue (FIFO with the web app's LPUSH). Returns
    a dict {videoId, userId} or None when the queue is empty.

    Uses the Upstash REST command form (POST ["RPOP", key]) rather than the
    path style — it's the canonical Upstash format and also works against a
    local serverless-redis-http shim for offline dev."""
    if not config.UPSTASH_URL:
        return None
    try:
        r = requests.post(
            config.UPSTASH_URL.rstrip("/"),
            headers={"Authorization": f"Bearer {config.UPSTASH_TOKEN}"},
            json=["RPOP", config.QUEUE_KEY],
            timeout=10,
        )
        r.raise_for_status()
        result = r.json().get("result")
    except requests.RequestException as e:
        print(f"[storage] pop_job failed: {e}")
        return None
    if not result:
        return None
    try:
        return json.loads(result)
    except (json.JSONDecodeError, TypeError):
        return None
