from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.app.ai import (
    MissingOpenRouterApiKeyError,
    OpenRouterClient,
    OpenRouterRequestError,
)
from backend.app.config import AUTH_TOKEN, FRONTEND_DIST_DIR, VALID_PASSWORD, VALID_USERNAME
from backend.app.dependencies import create_board_store, require_username
from backend.app.models import (
    AIConnectivityCheckResponse,
    AIChatRequest,
    AIChatResponse,
    BoardResponse,
    CardCreateRequest,
    CardResponse,
    CardMoveRequest,
    CardUpdateRequest,
    ColumnRenameRequest,
    LoginRequest,
    LoginResponse,
)

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

def create_app(
    frontend_dist_dir: Optional[Path] = None,
    db_path: Optional[Path] = None,
    ai_client: Optional[OpenRouterClient] = None,
) -> FastAPI:
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
    board_store = create_board_store(db_path)
    configured_ai_client = ai_client or OpenRouterClient()

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
    def read_current_user(username: str = Depends(require_username)) -> dict[str, str]:
        return {"username": username}

    @app.post("/api/ai/connectivity-check", response_model=AIConnectivityCheckResponse)
    def run_ai_connectivity_check(
        username: str = Depends(require_username),
    ) -> AIConnectivityCheckResponse:
        del username

        try:
            result = configured_ai_client.run_connectivity_check()
        except MissingOpenRouterApiKeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        except OpenRouterRequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

        return AIConnectivityCheckResponse(
            model=result.model,
            reply=result.reply,
        )

    @app.post("/api/ai/chat", response_model=AIChatResponse)
    def run_ai_chat(
        payload: AIChatRequest,
        username: str = Depends(require_username),
    ) -> AIChatResponse:
        try:
            board_snapshot = board_store.get_board_snapshot(username)
            result = configured_ai_client.run_board_assistant(
                board_snapshot=board_snapshot,
                message=payload.message,
                history=payload.history,
            )
        except MissingOpenRouterApiKeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        except OpenRouterRequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

        updated_board = board_snapshot
        board_updated = False
        if result.operations:
            try:
                updated_board = board_store.apply_ai_operations(
                    username=username,
                    operations=result.operations,
                    create_id=_create_id,
                )
                board_updated = True
            except HTTPException as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"AI returned invalid board operations: {exc.detail}",
                ) from exc

        return AIChatResponse(
            model=result.model,
            reply=result.reply,
            operations=result.operations,
            boardUpdated=board_updated,
            board=updated_board,
        )

    @app.get("/api/board", response_model=BoardResponse)
    def read_board(username: str = Depends(require_username)) -> BoardResponse:
        return BoardResponse(board=board_store.get_board_snapshot(username))

    @app.get("/api/cards/{card_id}", response_model=CardResponse)
    def read_card(card_id: str, username: str = Depends(require_username)) -> CardResponse:
        return CardResponse(card=board_store.get_card(username, card_id))

    @app.patch("/api/columns/{column_id}", response_model=BoardResponse)
    def rename_column(
        column_id: str,
        payload: ColumnRenameRequest,
        username: str = Depends(require_username),
    ) -> BoardResponse:
        return BoardResponse(
            board=board_store.rename_column(
                username=username,
                column_id=column_id,
                title=payload.title,
                expected_version=payload.version,
            )
        )

    @app.post("/api/cards", response_model=BoardResponse, status_code=status.HTTP_201_CREATED)
    def create_card(
        payload: CardCreateRequest,
        username: str = Depends(require_username),
    ) -> BoardResponse:
        return BoardResponse(
            board=board_store.create_card(
                username=username,
                card_id=_create_id("card"),
                column_id=payload.columnId,
                title=payload.title,
                details=payload.details,
                before_card_id=payload.beforeCardId,
                after_card_id=payload.afterCardId,
            )
        )

    @app.patch("/api/cards/{card_id}", response_model=BoardResponse)
    def update_card(
        card_id: str,
        payload: CardUpdateRequest,
        username: str = Depends(require_username),
    ) -> BoardResponse:
        return BoardResponse(
            board=board_store.update_card(
                username=username,
                card_id=card_id,
                title=payload.title,
                details=payload.details,
                expected_version=payload.version,
            )
        )

    @app.post("/api/cards/{card_id}/move", response_model=BoardResponse)
    def move_card(
        card_id: str,
        payload: CardMoveRequest,
        username: str = Depends(require_username),
    ) -> BoardResponse:
        return BoardResponse(
            board=board_store.move_card(
                username=username,
                card_id=card_id,
                target_column_id=payload.targetColumnId,
                expected_version=payload.version,
                before_card_id=payload.beforeCardId,
                after_card_id=payload.afterCardId,
            )
        )

    @app.delete("/api/cards/{card_id}", response_model=BoardResponse)
    def delete_card(
        card_id: str,
        version: int = Query(..., ge=1),
        username: str = Depends(require_username),
    ) -> BoardResponse:
        return BoardResponse(
            board=board_store.delete_card(
                username=username,
                card_id=card_id,
                expected_version=version,
            )
        )

    if frontend_dir.is_dir():
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    else:
        @app.get("/", response_class=HTMLResponse)
        def read_root() -> str:
            return PLACEHOLDER_HTML

    return app


def _create_id(prefix: str) -> str:
    import time
    import secrets

    random_part = secrets.token_hex(3)
    time_part = format(time.time_ns(), "x")
    return f"{prefix}-{random_part}{time_part}"


app = create_app()
