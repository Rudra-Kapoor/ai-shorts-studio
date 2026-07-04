# 🚀 Quick Start — Run AI Shorts Studio on Your Computer

The easiest way to run this app on your own machine. **No paid services, no cloud
accounts** — just Docker, Node.js, and one free API key. Takes ~10 minutes.

**What it does:** you give it a video (a file **or** a YouTube link) and it makes
short, captioned, vertical clips ready for Shorts / Reels / TikTok.

---

## 1) Install two free tools (one time)

1. **Docker Desktop** — https://www.docker.com/products/docker-desktop/
   Install it, then **open it** and wait until it says *"Docker Desktop is running."*
2. **Node.js (LTS)** — https://nodejs.org/  → click the big **LTS** button and install.

Check they work — open a terminal (**PowerShell** on Windows) and run:

```bash
docker --version
node --version
```

Both should print a version number. If so, you're good.

## 2) Get one free API key (2 minutes)

The app needs a **Groq** key (it transcribes the video and finds the viral moments):

1. Go to **https://console.groq.com** and sign in.
2. Open **API Keys → Create API Key**.
3. Copy the key — it starts with `gsk_...`. Keep it handy.

> Optional: a **Gemini** key from https://aistudio.google.com/app/apikey adds
> auto-written captions & hashtags. You can skip this and add it later.

## 3) Download the code

```bash
git clone https://github.com/Rudra-Kapoor/ai-shorts-studio.git
cd ai-shorts-studio
```

## 4) Add your key

Copy the two template files, then paste your Groq key into one of them.

**Windows (PowerShell):**
```powershell
Copy-Item worker\.env.worker.local.example worker\.env.worker.local
Copy-Item web\.env.local.example web\.env.local
```

**Mac / Linux:**
```bash
cp worker/.env.worker.local.example worker/.env.worker.local
cp web/.env.local.example web/.env.local
```

Now open **`worker/.env.worker.local`** in any text editor and put your key on the
`GROQ_API_KEY=` line:

```
GROQ_API_KEY=gsk_your_key_here
```

Save it. That's the only thing you have to fill in.

## 5) Start the backend (Docker)

Make sure Docker Desktop is running, then from the project folder:

```bash
docker compose up -d --build
```

The **first** run takes a few minutes (it downloads + builds everything). After
that it's quick. This starts the database, storage, job queue, and the video
worker — all on your machine.

## 6) Start the web app

```bash
cd web
npm install
npm run dev
```

When it prints **Ready**, open **http://localhost:3000** in your browser.

> If port 3000 is already used, run `npm run dev -- -p 3200` and open
> **http://localhost:3200** instead.

## 7) Use it 🎉

1. Sign in with **any email** (it's a simple demo login).
2. Choose **Upload file** or **YouTube link**, pick a caption style + size, and
   click **Generate**.
3. Watch the progress. Finished clips appear with a thumbnail, burned-in
   captions, scores, and a **Download** button.

> Tip: start with a **short** video. Making clips uses your computer's CPU, so
> long videos are slow.

---

## Start / stop later

```bash
docker compose down       # stop the backend (your data is kept)
docker compose up -d      # start it again anytime
```

For the web app, just run `npm run dev` again inside the `web` folder.

## If something doesn't work

| Problem | Fix |
|---|---|
| `docker: command not found` or connection errors | Make sure **Docker Desktop is open and running**, then retry. |
| Clips fail; worker log says `GROQ_API_KEY is not set` | You didn't paste the key. Edit `worker/.env.worker.local`, then run `docker compose up -d --force-recreate worker`. |
| **"No strong clips found"** | The video had little/no clear speech. Use a talking video (podcast, interview, talk). |
| Port 3000 already in use | `npm run dev -- -p 3200`, then open http://localhost:3200. |
| Want to watch what's happening | `docker compose logs -f worker` |
| No sound in a clip | Re-generate it — new clips use browser-friendly audio; download and play in VLC to double-check. |

---

Want to put it **online for free** (so anyone can use it, not just your computer)?
See **[DEPLOY.md](DEPLOY.md)**. For more local details, see **[LOCAL_DEV.md](LOCAL_DEV.md)**.
