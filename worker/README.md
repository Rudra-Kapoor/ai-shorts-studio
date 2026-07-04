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
