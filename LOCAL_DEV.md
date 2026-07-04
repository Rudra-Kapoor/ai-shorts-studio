# Run AI Shorts Studio locally (all-in-one, no cloud accounts)

This runs the whole app on your machine using Docker for the backing services,
so the only thing you need from the internet is a **free Groq API key** (and
optionally a Gemini key for captions/hashtags).

```
Browser ─▶ Web (Next.js, host :3000)
                │  presigned URLs / API
                ▼
   MinIO :9000 (S3)   Mongo :27017   serverless-redis-http :8079 ─▶ Redis
                ▲                                    │
                └──────────── Worker :8000 ◀─────────┘  (FFmpeg pipeline, Docker)
```

The Docker stack replaces the cloud services 1:1:
