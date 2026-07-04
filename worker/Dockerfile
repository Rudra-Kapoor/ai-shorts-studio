# Worker image — deploy to Render (free web service), Hugging Face Spaces,
# Google Cloud Run, or Fly.io. ffmpeg is the only system dependency; all AI
# (Whisper, Llama, Gemini) is called over HTTP so the image stays small and
# fits in 512MB RAM free tiers.

FROM python:3.11-slim

# ffmpeg + ffprobe for all video/audio work, plus fonts so libass can
# actually render burned-in captions (the slim image ships with none) and
# fontconfig so it can find them.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ffmpeg fonts-liberation fontconfig \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
