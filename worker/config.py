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
