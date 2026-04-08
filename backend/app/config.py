import os
from functools import lru_cache
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "out"
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "pm.sqlite3"
ROOT_ENV_PATH = PROJECT_ROOT / ".env"

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-oss-120b"
OPENROUTER_CONNECTIVITY_PROMPT = "What is 2+2? Reply with digits only."
OPENROUTER_HTTP_REFERER = "http://127.0.0.1:8000"
OPENROUTER_APP_TITLE = "Project Management MVP"
OPENROUTER_TIMEOUT_SECONDS = 30
OPENROUTER_MAX_RETRIES = 2

VALID_USERNAME = "user"
VALID_PASSWORD = "password"
AUTH_TOKEN = "pm-mvp-user-token"


def get_openrouter_api_key() -> Optional[str]:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        return api_key

    return _read_root_env_file().get("OPENROUTER_API_KEY")


@lru_cache(maxsize=1)
def _read_root_env_file() -> dict[str, str]:
    values: dict[str, str] = {}

    if not ROOT_ENV_PATH.is_file():
        return values

    for raw_line in ROOT_ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        cleaned_key = key.strip()
        cleaned_value = value.strip().strip("'\"")

        if cleaned_key:
            values[cleaned_key] = cleaned_value

    return values
