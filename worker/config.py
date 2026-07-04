"""Central config — every tunable read from the environment."""
import os


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


# --- AI providers (free tiers) ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

GROQ_BASE = "https://api.groq.com/openai/v1"
GROQ_WHISPER_MODEL = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo")
GROQ_LLM_MODEL = os.getenv("GROQ_LLM_MODEL", "llama-3.3-70b-versatile")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# --- Storage (Cloudflare R2) ---
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET = os.getenv("R2_BUCKET", "ai-shorts")
# Optional explicit endpoint for local dev (MinIO) or any S3-compatible store.
# Unset → derive the R2 endpoint from the account id, exactly as before.
_R2_ENDPOINT_OVERRIDE = os.getenv("R2_ENDPOINT", "")
R2_ENDPOINT = _R2_ENDPOINT_OVERRIDE or f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
# MinIO/localhost need path-style addressing; R2 works with the default.
S3_PATH_STYLE = bool(_R2_ENDPOINT_OVERRIDE)

# --- Database (MongoDB Atlas) ---
MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_DB = os.getenv("MONGODB_DB", "ai_shorts")

# --- Queue (Upstash Redis REST) ---
UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
QUEUE_KEY = "ass:jobs"

# --- Security ---
WORKER_SECRET = os.getenv("WORKER_SECRET", "")

# --- Pipeline tuning ---
MAX_CLIPS = _int("MAX_CLIPS", 3)
MIN_CLIP_SEC = _int("MIN_CLIP_SEC", 15)
MAX_CLIP_SEC = _int("MAX_CLIP_SEC", 60)
# Minimum overall virality (0-100) for a clip to be kept when there are MORE
# candidates than MAX_CLIPS — it just trims the weakest extras. We always return
# at least one clip (and fall back to speech-density selection if the model
# declines), so this never causes "no clips". Lower/raise to taste.
MIN_VIRALITY = _int("MIN_VIRALITY", 35)

# Output dimensions per aspect ratio. 9:16 is the tuned default; 1:1 and 16:9
# let the same pipeline target square feed posts and landscape.
RATIOS = {
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
    "16:9": (1920, 1080),
}
DEFAULT_RATIO = os.getenv("ASPECT_RATIO", "9:16")
OUT_W, OUT_H = RATIOS.get(DEFAULT_RATIO, RATIOS["9:16"])


def dims_for(ratio):
    """(width, height) for a ratio key; falls back to 9:16."""
    return RATIOS.get(ratio, RATIOS["9:16"])

# --- Phase 2 ---
# Default caption style: hormozi | mrbeast | minimal | clean (per-video override
# comes from the upload form).
CAPTION_STYLE = os.getenv("CAPTION_STYLE", "hormozi")
# Generate a thumbnail per clip.
THUMBNAILS = os.getenv("THUMBNAILS", "1") == "1"
# Gemini-vision keyframe scoring (off by default — costs extra API calls).
VISION_SCORING = os.getenv("VISION_SCORING", "0") == "1"

# Fonts baked into the Docker image (used by ASS captions + thumbnail text).
FONT_NAME = os.getenv("FONT_NAME", "Liberation Sans")
FONT_FILE = os.getenv(
    "FONT_FILE", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
)

# --- Phase 3 ---
# Face-aware smart crop (needs opencv-python-headless installed; off by default
# so the lean free-tier image still works — falls back to center crop).
FACE_CROP = os.getenv("FACE_CROP", "0") == "1"
# Long-video transcription: chunk the audio when it exceeds the Whisper limit.
WHISPER_MAX_MB = _int("WHISPER_MAX_MB", 24)
CHUNK_SEC = _int("CHUNK_SEC", 600)
# Trend RAG (Gemini embeddings + Mongo). Disabled automatically if no key/seed.
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "text-embedding-004")

# Auto-post — YouTube (OAuth refresh-token flow). All optional.
YT_CLIENT_ID = os.getenv("YT_CLIENT_ID", "")
YT_CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET", "")
YT_REFRESH_TOKEN = os.getenv("YT_REFRESH_TOKEN", "")
# Auto-post — Instagram (Graph API, business/creator account). All optional.
IG_USER_ID = os.getenv("IG_USER_ID", "")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")
