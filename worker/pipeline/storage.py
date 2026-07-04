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
