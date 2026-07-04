# 🚀 Deploy AI Shorts Studio — Free, Step by Step

Follow this top to bottom. ~20–30 minutes, **₹0**, nothing runs on your PC.
You'll create 7 free accounts, paste keys into **Render** (worker) and **Vercel**
(web), and you're live.

> Legend: 📋 = copy this value somewhere (a notepad). You'll paste them later.

---

## 0) Push the code to GitHub

The project folder already has a git repo. Create an **empty** GitHub repo, then:

```bash
cd C:\Users\crpla\Desktop\ai-shorts-studio
git add .
git commit -m "AI Shorts Studio"
git branch -M main
git remote add origin https://github.com/<you>/ai-shorts-studio.git
git push -u origin main
```

---

## 1) Cloudflare R2 — storage (free 10GB)

1. Cloudflare dashboard → **R2** → *Create bucket* → name it **`ai-shorts`**.
2. R2 → **Manage R2 API Tokens** → *Create API token* → permission **Object Read & Write** → Create.
3. 📋 Save: **Account ID**, **Access Key ID**, **Secret Access Key**.
4. R2 → your bucket → **Settings → CORS Policy** → add this (lets the browser upload):

```json
[
  {
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["PUT", "GET"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"]
  }
]
```
*(After Vercel is live, replace `"*"` with your Vercel URL to lock it down.)*

---

## 2) MongoDB Atlas — database (free 512MB)

1. Create a free **M0** cluster.
2. **Database Access** → add a user + password. 📋 Save them.
3. **Network Access** → *Add IP* → **`0.0.0.0/0`** (allow anywhere — needed for serverless).
4. **Connect → Drivers** → 📋 copy the `mongodb+srv://…` connection string
   (put your password into it where it says `<password>`).

---

## 3) Upstash Redis — job queue (free)

1. Create a **Redis** database (any region).
2. Scroll to **REST API** → 📋 copy **UPSTASH_REDIS_REST_URL** and **UPSTASH_REDIS_REST_TOKEN**
   (the REST ones — not the `redis://` one).

---

## 4) Groq — transcription + LLM (free)

1. https://console.groq.com → **API Keys** → Create. 📋 Save the `gsk_…` key.

## 5) Google Gemini — captions + trends (free)

1. https://aistudio.google.com/app/apikey → Create API key. 📋 Save the `AIza…` key.

## 6) Make a worker secret

📋 Invent a long random string, e.g. `s7f9-Kd2p-Wq8x-Zr4m-Lv6n`. You'll paste the
**same** value into Render *and* Vercel.

---

## 7) Deploy the WORKER → Render (free, Docker)

1. https://render.com → **New → Blueprint** → connect your GitHub repo.
   Render reads `render.yaml` automatically.
2. It will ask for the env vars below. Fill them with your 📋 values:

| Key | Value |
|---|---|
| `GROQ_API_KEY` | your `gsk_…` |
| `GEMINI_API_KEY` | your `AIza…` |
| `MONGODB_URI` | your `mongodb+srv://…` |
| `R2_ACCOUNT_ID` | from step 1 |
| `R2_ACCESS_KEY_ID` | from step 1 |
| `R2_SECRET_ACCESS_KEY` | from step 1 |
| `UPSTASH_REDIS_REST_URL` | from step 3 |
| `UPSTASH_REDIS_REST_TOKEN` | from step 3 |
| `WORKER_SECRET` | your secret from step 6 |

*(`MONGODB_DB`, `R2_BUCKET`, and the tuning vars already have defaults.)*

3. Click **Apply / Deploy**. Wait for the build (a few minutes).
4. 📋 Copy your worker URL, e.g. `https://ai-shorts-worker.onrender.com`.
5. Test it: open `<worker-url>/health` in your browser → should show `{"ok":true}`.

> Not using Render? The same Docker image runs on Hugging Face Spaces, Google
> Cloud Run, or Fly.io — just set the same env vars.

---

## 8) Deploy the WEB app → Vercel (free)

1. https://vercel.com → **Add New → Project** → import the same repo.
2. **IMPORTANT: set _Root Directory_ to `web`.**
3. Add these Environment Variables:

| Key | Value |
|---|---|
| `MONGODB_URI` | same as Render |
| `MONGODB_DB` | `ai_shorts` |
| `R2_ACCOUNT_ID` | from step 1 |
| `R2_ACCESS_KEY_ID` | from step 1 |
| `R2_SECRET_ACCESS_KEY` | from step 1 |
| `R2_BUCKET` | `ai-shorts` |
| `UPSTASH_REDIS_REST_URL` | from step 3 |
| `UPSTASH_REDIS_REST_TOKEN` | from step 3 |
| `WORKER_URL` | your Render URL from step 7 |
| `WORKER_SECRET` | the **same** secret from step 6 |

4. **Deploy.** Open your Vercel URL. 🎉

---

## 9) Seed trends (one time, optional but recommended)

Turns on the Phase-3 trend matching. Run this once (replace the URL + secret):

```bash
curl -X POST https://ai-shorts-worker.onrender.com/seed-trends ^
  -H "x-worker-secret: YOUR_WORKER_SECRET"
```
*(Windows CMD uses `^` for line breaks; PowerShell uses a backtick `` ` ``. Or just
put it all on one line.)* You should get `{"ok":true,"seeded":5}`.

---

## 10) Use it

1. Open the Vercel URL → sign in with any email.
2. Pick a **caption style**, choose a short video, **Upload & generate Shorts**.
3. First job: the worker cold-starts (~30–60s). The page shows live progress.
4. Finished Shorts appear with thumbnails, scores, captions, hashtags, Download.

---

## ✅ What's enabled by default
- Whisper transcription (auto-chunks long videos)
- Viral-moment detection + scoring
- 4 caption styles (Hormozi / MrBeast / Clean / Minimal)
- 9:16 render with burned-in captions
- Thumbnails
- Captions + hashtags
- Trend matching (after you seed in step 9)

## 🔧 Optional power-ups (flip on in Render env, then redeploy)
| Feature | How to enable |
|---|---|
| **Gemini-vision scoring** | set `VISION_SCORING=1` |
| **Face-aware smart crop** | add `opencv-python-headless==4.10.0.84` to `worker/requirements.txt`, set `FACE_CROP=1` |
| **Auto-post to YouTube** | set `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` (see below) |
| **Auto-post to Instagram** | set `IG_USER_ID`, `IG_ACCESS_TOKEN` (Business/Creator account) |

### YouTube auto-post setup (if you want it)
1. Google Cloud Console → enable **YouTube Data API v3**.
2. Create an **OAuth client (Desktop app)** → 📋 client id + secret.
3. Generate a **refresh token** once (OAuth Playground at
   `developers.google.com/oauthplayground`, scope
   `https://www.googleapis.com/auth/youtube.upload`, use your own client id/secret).
4. Put all three into Render env. Videos upload as **private** by default — flip to
   public in YouTube Studio when you're happy.

---

## 🆘 Troubleshooting first deploy

| Symptom | Fix |
|---|---|
| Upload fails instantly in the browser | R2 **CORS** not set (step 1.4). |
| Video stuck on "Queued" forever | `WORKER_URL`/`WORKER_SECRET` mismatch between Vercel & Render, or worker still cold — wait 60s. |
| Worker `/health` 404 or won't build | Check Render build logs; ensure Root/Docker came from `render.yaml`. |
| "GROQ_API_KEY is not set" in logs | Key missing/typo'd in Render env. |
| Captions look blank | Make sure you deployed the latest Dockerfile (it installs fonts). Redeploy. |
| Mongo connection error | `0.0.0.0/0` not added in Atlas Network Access (step 2.3). |
| `failed` status on a video | Open the video page → **Retry**. Check Render logs for the real error. |
