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
