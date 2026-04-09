import os
from pathlib import Path
from typing import Optional

from fastapi import Header, HTTPException, status

from backend.app.config import AUTH_TOKEN, VALID_USERNAME, DEFAULT_DB_PATH
from backend.app.storage import BoardStore


def get_db_path(explicit_path: Optional[Path] = None) -> Path:
    if explicit_path is not None:
        return explicit_path

    configured_path = os.getenv("PM_DB_PATH")
    if configured_path:
        return Path(configured_path)

    return DEFAULT_DB_PATH


def create_board_store(explicit_path: Optional[Path] = None) -> BoardStore:
    store = BoardStore(get_db_path(explicit_path))
    store.initialize()
    return store


def get_authenticated_username(authorization: Optional[str]) -> str:
    parts = (authorization or "").split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or parts[1] != AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    return VALID_USERNAME


def require_username(authorization: Optional[str] = Header(default=None)) -> str:
    return get_authenticated_username(authorization)
