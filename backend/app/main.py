from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

FRONTEND_DIST_DIR = Path(__file__).resolve().parents[2] / "frontend" / "out"
VALID_USERNAME = "user"
VALID_PASSWORD = "password"
AUTH_TOKEN = "pm-mvp-user-token"

PLACEHOLDER_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Project Management MVP</title>
    <style>
      :root {
        --accent-yellow: #ecad0a;
        --primary-blue: #209dd7;
        --secondary-purple: #753991;
        --navy-dark: #032147;
        --gray-text: #888888;
        --surface: #f7f8fb;
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        background:
          radial-gradient(circle at top left, rgba(32, 157, 215, 0.16), transparent 32%),
          radial-gradient(circle at bottom right, rgba(117, 57, 145, 0.14), transparent 36%),
          var(--surface);
        color: var(--navy-dark);
        font-family: "Segoe UI", sans-serif;
      }

      main {
        width: min(720px, calc(100vw - 32px));
        padding: 40px;
        border: 1px solid rgba(3, 33, 71, 0.08);
        border-radius: 28px;
        background: rgba(255, 255, 255, 0.92);
        box-shadow: 0 18px 40px rgba(3, 33, 71, 0.12);
      }

      p {
        line-height: 1.6;
      }

      .eyebrow {
        margin: 0;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.24em;
        text-transform: uppercase;
        color: var(--gray-text);
      }

      h1 {
        margin: 12px 0 16px;
        font-size: clamp(32px, 5vw, 48px);
      }

      .status {
        margin-top: 28px;
        padding: 16px 18px;
        border-left: 4px solid var(--accent-yellow);
        border-radius: 16px;
        background: rgba(32, 157, 215, 0.06);
      }

      code {
        font-family: "SFMono-Regular", "SFMono-Regular", Consolas, monospace;
      }
    </style>
  </head>
  <body>
    <main>
      <p class="eyebrow">FastAPI Scaffold</p>
      <h1>Project Management MVP</h1>
      <p>
        The backend container is running and serving placeholder HTML from
        <code>/</code>. The existing Next.js kanban frontend will replace this page
        in the next phase.
      </p>
      <div class="status">
        API status endpoint: <code>/api/health</code>
      </div>
    </main>
  </body>
</html>
"""


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str


def get_authenticated_username(authorization: Optional[str]) -> str:
    expected_value = f"Bearer {AUTH_TOKEN}"
    if authorization != expected_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    return VALID_USERNAME


def create_app(frontend_dist_dir: Optional[Path] = None) -> FastAPI:
    app = FastAPI(title="Project Management MVP")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:3000",
            "http://localhost:3000",
        ],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    frontend_dir = frontend_dist_dir or FRONTEND_DIST_DIR

    @app.get("/api/health")
    def read_health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/auth/login", response_model=LoginResponse)
    def login(payload: LoginRequest) -> LoginResponse:
        if (
            payload.username != VALID_USERNAME
            or payload.password != VALID_PASSWORD
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        return LoginResponse(token=AUTH_TOKEN, username=VALID_USERNAME)

    @app.get("/api/auth/me")
    def read_current_user(
        authorization: Optional[str] = Header(default=None),
    ) -> dict[str, str]:
        username = get_authenticated_username(authorization)
        return {"username": username}

    if frontend_dir.is_dir():
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    else:
        @app.get("/", response_class=HTMLResponse)
        def read_root() -> str:
            return PLACEHOLDER_HTML

    return app


app = create_app()
