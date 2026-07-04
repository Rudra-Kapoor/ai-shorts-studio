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
