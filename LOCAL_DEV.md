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

| Cloud (prod) | Local (dev) |
|---|---|
| Cloudflare R2 | MinIO (`minio/minio`) |
| MongoDB Atlas | `mongo:7` |
| Upstash Redis (REST) | `redis:7` + `serverless-redis-http` shim |
| Render worker | the `worker` image, built locally |
| Vercel web | `npm run dev` on the host |

## One-time setup

1. **Add your Groq key.** Edit [worker/.env.worker.local](worker/.env.worker.local)
   and set `GROQ_API_KEY=` (from https://console.groq.com → API Keys). Optionally
   set `GEMINI_API_KEY=` (https://aistudio.google.com/app/apikey).
2. Make sure **Docker Desktop** is running.

## Start it

```powershell
# 1) backing services + worker (first run builds the worker image)
docker compose up -d --build

# 2) the web app (host)
cd web
npm install        # first time only
npm run dev        # http://localhost:3000
```

Open http://localhost:3000, sign in with any email, pick a style, upload a short
video, and watch the clips appear.

## Handy

```powershell
docker compose logs -f worker     # watch the pipeline run
docker compose ps                 # service status
docker compose restart worker     # after editing worker/.env.worker.local
docker compose down               # stop (keeps data)
docker compose down -v            # stop and wipe DB/storage
```
