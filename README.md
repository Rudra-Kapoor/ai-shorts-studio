# 🎬 AI Shorts Studio

Turn long videos into viral Shorts/Reels — **automatically and 100% on free
cloud tiers**. Upload a video, and an AI pipeline transcribes it, finds the most
viral moments, crops them to 9:16, burns on word-by-word captions, and writes a
caption + hashtags for each clip.

> **Nothing runs on your computer.** Your PC only holds the code and pushes to
> GitHub. Every running piece lives in a free cloud service that sleeps when
> idle. The heavy video worker *wakes on a job, processes, then sleeps* — so
> there's no machine you need to keep on, and no bill.

---

## What it does (the pipeline)

```
Upload ──► [Web · Vercel] ──► queue (Upstash) ──► wake ──► [Worker · Render]
                 │                                              │
              MongoDB                                           ├─ Whisper (Groq)      → transcript + word timings
                 ▲                                              ├─ Llama (Groq)        → score & pick viral clips
                 │                                              ├─ FFmpeg              → 9:16 crop + burn captions
                 └───────────── status / clips ────────────────┤─ Gemini Flash        → caption + hashtags
                                                                └─ R2                  → store finished Shorts
```

The single most important design choice: **one batched LLM call scores the whole
transcript** and returns the best clips. That's what keeps everything inside free
rate limits.

---

## The free stack (every piece has a free tier)

| Layer | Service | What to create | Free? |
|---|---|---|---|
| Web UI + API | **Vercel** | import the `web/` folder | ✅ always-on |
| Database | **MongoDB Atlas** | free M0 cluster + DB user | ✅ 512MB |
| Object storage | **Cloudflare R2** | a bucket + S3 API token | ✅ 10GB |
| Job queue | **Upstash Redis** | a database (REST) | ✅ serverless |
| Worker | **Render** | Docker web service (`render.yaml`) | ✅ wakes-on-request |
| Transcription + LLM | **Groq** | API key | ✅ free |
| Captions/vision | **Google Gemini** | API key (AI Studio) | ✅ free |

Repo layout:

```
ai-shorts-studio/
├── web/        Next.js app  → deploy to Vercel
├── worker/     FastAPI + FFmpeg pipeline → deploy to Render (Docker)
├── render.yaml Render blueprint for the worker
└── .env.example  every secret, annotated
```

---

## Setup — step by step

You'll create 6 free accounts and paste keys into 2 places (Vercel + Render).
Take it slow; it's all copy-paste.

### 1. Cloudflare R2 (storage)
1. Cloudflare dashboard → **R2** → *Create bucket* named `ai-shorts`.
2. R2 → *Manage API Tokens* → create a token with **Object Read & Write**.
3. Note: **Account ID**, **Access Key ID**, **Secret Access Key**.
4. **CORS** (so the browser can upload): R2 bucket → Settings → CORS, add:
   ```json
   [{ "AllowedOrigins": ["*"], "AllowedMethods": ["PUT","GET"],
      "AllowedHeaders": ["*"] }]
   ```
   (Tighten `AllowedOrigins` to your Vercel URL once deployed.)

### 2. MongoDB Atlas (database)
1. Create a free **M0** cluster.
2. *Database Access* → add a user/password.
3. *Network Access* → allow `0.0.0.0/0` (any IP — needed for serverless).
4. *Connect → Drivers* → copy the `mongodb+srv://…` URI.

### 3. Upstash Redis (queue)
1. Create a Redis database.
2. Copy the **REST URL** and **REST TOKEN** (not the TCP one).

### 4. Groq (Whisper + Llama)
1. https://console.groq.com → **API Keys** → create one (`gsk_…`).

### 5. Google Gemini (captions)
1. https://aistudio.google.com/app/apikey → create a key (`AIza…`).

### 6. Pick a WORKER_SECRET
Any long random string. The web app sends it to the worker so only you can
trigger jobs. Use the same value in both Vercel and Render.

---

## Deploy

### Worker → Render
1. Push this repo to GitHub.
2. Render → **New → Blueprint** → select the repo (it reads `render.yaml`).
3. Fill in the secret env vars (everything marked `sync:false`).
4. Deploy. Copy the service URL, e.g. `https://ai-shorts-worker.onrender.com`.

### Web → Vercel
1. Vercel → **Add New → Project** → import the repo.
2. **Set Root Directory to `web`.**
3. Add the env vars from `web/.env.example`, including:
   - `WORKER_URL` = your Render URL
   - `WORKER_SECRET` = the same secret you gave Render
4. Deploy.
