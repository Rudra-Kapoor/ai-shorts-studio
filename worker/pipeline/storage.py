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
