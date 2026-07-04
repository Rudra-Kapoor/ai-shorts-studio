# AI Shorts Studio — Worker

The Python service that does all the heavy lifting: transcription, viral-moment
detection, video editing (FFmpeg), and caption generation. It's a small FastAPI
app — all AI runs over HTTP (Groq + Gemini), so the image stays tiny and fits
free 512MB tiers.

## Flow

```
POST /wake  →  drain queue (Upstash)  →  for each job:
   download (R2) → audio → Whisper (Groq) → score clips (Llama/Groq)
   → per clip: ASS captions → FFmpeg 9:16 render → upload (R2) → Gemini caption
   → write status/clips (MongoDB)
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | liveness + whether it's currently draining |
| GET | `/health` | health check (used by Render) |
| POST | `/wake` | wakes the instance and drains the job queue (needs `x-worker-secret`) |

## Run locally with Docker (optional)

> You don't need to — the cloud build does this for you. But if you want to test:

```bash
docker build -t ass-worker ./worker
docker run --rm -p 8000:8000 --env-file .env ass-worker
# then: curl -X POST localhost:8000/wake -H "x-worker-secret: <yours>"
```

## Deploy (Render, free)

Use the repo-root `render.yaml` blueprint, or manually:
1. New → Web Service → this repo
2. Root directory: `worker`, Runtime: Docker
3. Add the env vars from `../.env.example` (WORKER block)
4. Health check path: `/health`

Alternatives that also work unchanged: Hugging Face Spaces (Docker), Google
Cloud Run, Fly.io.

## Tuning

`MAX_CLIPS`, `MIN_CLIP_SEC`, `MAX_CLIP_SEC`, and the model names are all env vars
(see `config.py`).
