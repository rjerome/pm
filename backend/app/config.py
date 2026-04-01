from pathlib import Path


FRONTEND_DIST_DIR = Path(__file__).resolve().parents[2] / "frontend" / "out"
DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "pm.sqlite3"

VALID_USERNAME = "user"
VALID_PASSWORD = "password"
AUTH_TOKEN = "pm-mvp-user-token"
