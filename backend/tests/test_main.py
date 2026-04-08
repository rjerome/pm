from pathlib import Path
from typing import List, Optional

from fastapi.testclient import TestClient

from backend.app.ai import (
    BoardAssistantResult,
    ConnectivityCheckResult,
    MissingOpenRouterApiKeyError,
    OpenRouterClient,
    OpenRouterRequestError,
)
from backend.app.main import create_app
from backend.app.models import AIConversationMessage


AUTH_HEADERS = {"Authorization": "Bearer pm-mvp-user-token"}


class FakeAIClient:
    def __init__(
        self,
        connectivity_result: Optional[ConnectivityCheckResult] = None,
        connectivity_error: Optional[Exception] = None,
        board_result: Optional[BoardAssistantResult] = None,
        board_error: Optional[Exception] = None,
    ) -> None:
        self.connectivity_result = connectivity_result or ConnectivityCheckResult(
            model="openai/gpt-oss-120b",
            reply="4",
        )
        self.connectivity_error = connectivity_error
        self.board_result = board_result or BoardAssistantResult(
            model="openai/gpt-oss-120b",
            reply="No board changes needed.",
            operations=[],
        )
        self.board_error = board_error
        self.connectivity_calls = 0
        self.board_calls = 0

    def run_connectivity_check(self) -> ConnectivityCheckResult:
        self.connectivity_calls += 1
        if self.connectivity_error is not None:
            raise self.connectivity_error
        return self.connectivity_result

    def run_board_assistant(
        self,
        board_snapshot: dict,
        message: str,
        history: List[AIConversationMessage],
    ) -> BoardAssistantResult:
        self.board_calls += 1
        if self.board_error is not None:
            raise self.board_error
        return self.board_result


def create_test_client(
    tmp_path: Path,
    ai_client: Optional[FakeAIClient] = None,
) -> tuple[TestClient, Path]:
    db_path = tmp_path / "pm.sqlite3"
    client = TestClient(
        create_app(
            Path("/tmp/frontend-out-missing"),
            db_path=db_path,
            ai_client=ai_client,
        )
    )
    return client, db_path


def test_root_serves_placeholder_html_when_frontend_build_is_missing(tmp_path: Path) -> None:
    client, _ = create_test_client(tmp_path)
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Project Management MVP" in response.text
    assert "/api/health" in response.text


def test_health_endpoint_returns_ok(tmp_path: Path) -> None:
    client, _ = create_test_client(tmp_path)
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_returns_token_for_valid_credentials(tmp_path: Path) -> None:
    client, _ = create_test_client(tmp_path)
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "token": "pm-mvp-user-token",
        "username": "user",
    }


def test_login_rejects_invalid_credentials(tmp_path: Path) -> None:
    client, _ = create_test_client(tmp_path)
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_me_requires_valid_bearer_token(tmp_path: Path) -> None:
    client, _ = create_test_client(tmp_path)

    unauthorized_response = client.get("/api/auth/me")
    authorized_response = client.get(
        "/api/auth/me",
        headers=AUTH_HEADERS,
    )

    assert unauthorized_response.status_code == 401
    assert unauthorized_response.json() == {"detail": "Unauthorized"}
    assert authorized_response.status_code == 200
    assert authorized_response.json() == {"username": "user"}


def test_ai_connectivity_check_returns_model_reply_for_authenticated_request(
    tmp_path: Path,
) -> None:
    fake_ai_client = FakeAIClient()
    client, _ = create_test_client(tmp_path, ai_client=fake_ai_client)

    response = client.post("/api/ai/connectivity-check", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert response.json() == {
        "model": "openai/gpt-oss-120b",
        "reply": "4",
    }
    assert fake_ai_client.connectivity_calls == 1


def test_ai_connectivity_check_requires_auth(tmp_path: Path) -> None:
    fake_ai_client = FakeAIClient()
    client, _ = create_test_client(tmp_path, ai_client=fake_ai_client)

    response = client.post("/api/ai/connectivity-check")

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}
    assert fake_ai_client.connectivity_calls == 0


def test_ai_connectivity_check_returns_clear_missing_key_error(tmp_path: Path) -> None:
    fake_ai_client = FakeAIClient(
        connectivity_error=MissingOpenRouterApiKeyError(
            "OPENROUTER_API_KEY is not configured."
        )
    )
    client, _ = create_test_client(tmp_path, ai_client=fake_ai_client)

    response = client.post("/api/ai/connectivity-check", headers=AUTH_HEADERS)

    assert response.status_code == 503
    assert response.json() == {"detail": "OPENROUTER_API_KEY is not configured."}


def test_ai_connectivity_check_returns_upstream_error_message(tmp_path: Path) -> None:
    fake_ai_client = FakeAIClient(
        connectivity_error=OpenRouterRequestError("OpenRouter rejected the API key.")
    )
    client, _ = create_test_client(tmp_path, ai_client=fake_ai_client)

    response = client.post("/api/ai/connectivity-check", headers=AUTH_HEADERS)

    assert response.status_code == 502
    assert response.json() == {"detail": "OpenRouter rejected the API key."}


def test_openrouter_client_parses_valid_structured_board_response() -> None:
    client = OpenRouterClient(api_key="test-key")
    client._post = lambda payload: {  # type: ignore[method-assign]
        "model": "openai/gpt-oss-120b",
        "choices": [
            {
                "message": {
                    "content": (
                        '{"reply":"I moved the work item.","operations":['
                        '{"type":"move_card","cardId":"card-1","targetColumnId":"col-review"}'
                        "]}"
                    )
                }
            }
        ],
    }

    result = client.run_board_assistant(
        board_snapshot={"version": 1, "columns": [], "cards": {}},
        message="Move card-1 to review",
        history=[],
    )

    assert result.reply == "I moved the work item."
    assert result.operations == [
        {
            "type": "move_card",
            "cardId": "card-1",
            "targetColumnId": "col-review",
            "beforeCardId": None,
            "afterCardId": None,
        }
    ]


def test_openrouter_client_rejects_partial_structured_board_response() -> None:
    client = OpenRouterClient(api_key="test-key")
    client._post = lambda payload: {  # type: ignore[method-assign]
        "model": "openai/gpt-oss-120b",
        "choices": [
            {
                "message": {
                    "content": '{"operations":[{"type":"delete_card","cardId":"card-1"}]}'
                }
            }
        ],
    }

    try:
        client.run_board_assistant(
            board_snapshot={"version": 1, "columns": [], "cards": {}},
            message="Delete card-1",
            history=[],
        )
    except OpenRouterRequestError as exc:
        assert str(exc) == (
            "OpenRouter returned a structured assistant response that did not match the expected schema."
        )
    else:
        raise AssertionError("Expected structured response validation to fail.")


def test_openrouter_client_retries_transient_structured_output_failure() -> None:
    responses = iter(
        [
            {
                "model": "openai/gpt-oss-120b",
                "choices": [
                    {
                        "message": {
                            "content": '{"operations":[{"type":"delete_card","cardId":"card-1"}]}'
                        }
                    }
                ],
            },
            {
                "model": "openai/gpt-oss-120b",
                "choices": [
                    {
                        "message": {
                            "content": '{"reply":"Done.","operations":[]}'
                        }
                    }
                ],
            },
        ]
    )
    client = OpenRouterClient(api_key="test-key")
    client._post = lambda payload: next(responses)  # type: ignore[method-assign]

    result = client.run_board_assistant(
        board_snapshot={"version": 1, "columns": [], "cards": {}},
        message="Do nothing",
        history=[],
    )

    assert result.reply == "Done."
    assert result.operations == []


def test_ai_chat_returns_reply_without_board_update_when_no_operations(
    tmp_path: Path,
) -> None:
    fake_ai_client = FakeAIClient(
        board_result=BoardAssistantResult(
            model="openai/gpt-oss-120b",
            reply="No changes needed right now.",
            operations=[],
        )
    )
    client, _ = create_test_client(tmp_path, ai_client=fake_ai_client)

    response = client.post(
        "/api/ai/chat",
        headers=AUTH_HEADERS,
        json={"message": "How does the board look?", "history": []},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["reply"] == "No changes needed right now."
    assert payload["operations"] == []
    assert payload["boardUpdated"] is False
    assert payload["board"]["version"] == 1


def test_ai_chat_applies_valid_board_operations_and_persists(tmp_path: Path) -> None:
    fake_ai_client = FakeAIClient(
        board_result=BoardAssistantResult(
            model="openai/gpt-oss-120b",
            reply="I renamed the first column and added a follow-up card.",
            operations=[
                {
                    "type": "rename_column",
                    "columnId": "col-backlog",
                    "title": "Ideas",
                },
                {
                    "type": "create_card",
                    "columnId": "col-review",
                    "title": "Prep release walkthrough",
                    "details": "Outline the talking points for the review session.",
                    "beforeCardId": None,
                    "afterCardId": "card-6",
                },
            ],
        )
    )
    client, db_path = create_test_client(tmp_path, ai_client=fake_ai_client)

    response = client.post(
        "/api/ai/chat",
        headers=AUTH_HEADERS,
        json={
            "message": "Rename backlog to Ideas and add a review prep card after QA.",
            "history": [{"role": "assistant", "content": "Sure, I can help with that."}],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["boardUpdated"] is True
    assert payload["reply"] == "I renamed the first column and added a follow-up card."
    assert payload["board"]["columns"][0]["title"] == "Ideas"
    review_column = next(
        column for column in payload["board"]["columns"] if column["id"] == "col-review"
    )
    created_card_id = review_column["cardIds"][1]
    created_card = payload["board"]["cards"][created_card_id]
    assert created_card["title"] == "Prep release walkthrough"
    assert created_card["details"] == "Outline the talking points for the review session."

    persisted_client = TestClient(
        create_app(Path("/tmp/frontend-out-missing"), db_path=db_path)
    )
    persisted_board = persisted_client.get("/api/board", headers=AUTH_HEADERS).json()["board"]
    assert persisted_board["columns"][0]["title"] == "Ideas"
    assert persisted_board["cards"][created_card_id]["title"] == "Prep release walkthrough"


def test_ai_chat_rejects_invalid_board_operations_without_persisting(
    tmp_path: Path,
) -> None:
    fake_ai_client = FakeAIClient(
        board_result=BoardAssistantResult(
            model="openai/gpt-oss-120b",
            reply="I tried to move the card.",
            operations=[
                {
                    "type": "move_card",
                    "cardId": "card-1",
                    "targetColumnId": "col-review",
                    "beforeCardId": "card-3",
                    "afterCardId": None,
                }
            ],
        )
    )
    client, _ = create_test_client(tmp_path, ai_client=fake_ai_client)

    response = client.post(
        "/api/ai/chat",
        headers=AUTH_HEADERS,
        json={"message": "Move card-1 before card-3 in review.", "history": []},
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "AI returned invalid board operations: beforeCardId must be in the target column"
    }

    board_response = client.get("/api/board", headers=AUTH_HEADERS)
    board = board_response.json()["board"]
    assert board["version"] == 1
    assert board["cards"]["card-1"]["columnId"] == "col-backlog"


def test_root_serves_built_frontend_when_static_export_exists(tmp_path: Path) -> None:
    frontend_dir = tmp_path / "frontend-out"
    frontend_dir.mkdir()
    (frontend_dir / "index.html").write_text(
        "<!doctype html><html><body><h1>Kanban Studio</h1></body></html>",
        encoding="utf-8",
    )

    client = TestClient(create_app(frontend_dir, db_path=tmp_path / "pm.sqlite3"))
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Kanban Studio" in response.text


def test_board_read_creates_database_and_seeds_board(tmp_path: Path) -> None:
    client, db_path = create_test_client(tmp_path)

    response = client.get("/api/board", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert db_path.exists()
    board = response.json()["board"]
    assert board["version"] == 1
    assert len(board["columns"]) == 5
    assert board["columns"][0]["id"] == "col-backlog"
    assert board["columns"][0]["cardIds"] == ["card-1", "card-2"]
    assert board["cards"]["card-1"]["title"] == "Align roadmap themes"


def test_card_can_be_queried_directly(tmp_path: Path) -> None:
    client, _ = create_test_client(tmp_path)

    response = client.get("/api/cards/card-1", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert response.json()["card"] == {
        "id": "card-1",
        "columnId": "col-backlog",
        "title": "Align roadmap themes",
        "details": "Draft quarterly themes with impact statements and metrics.",
        "sortOrder": 1000.0,
        "version": 1,
    }


def test_column_can_be_renamed_with_version_checking(tmp_path: Path) -> None:
    client, _ = create_test_client(tmp_path)

    success_response = client.patch(
        "/api/columns/col-backlog",
        headers=AUTH_HEADERS,
        json={"title": "Ideas", "version": 1},
    )
    conflict_response = client.patch(
        "/api/columns/col-backlog",
        headers=AUTH_HEADERS,
        json={"title": "Should Fail", "version": 1},
    )

    assert success_response.status_code == 200
    assert success_response.json()["board"]["columns"][0]["title"] == "Ideas"
    assert success_response.json()["board"]["columns"][0]["version"] == 2
    assert conflict_response.status_code == 409
    assert conflict_response.json() == {"detail": "Column version conflict"}


def test_card_create_update_move_delete_flow_persists(tmp_path: Path) -> None:
    client, db_path = create_test_client(tmp_path)

    create_response = client.post(
        "/api/cards",
        headers=AUTH_HEADERS,
        json={
            "columnId": "col-backlog",
            "title": "Document API",
            "details": "Write down the new mutation routes.",
        },
    )
    assert create_response.status_code == 201
    created_board = create_response.json()["board"]
    created_card_id = created_board["columns"][0]["cardIds"][-1]
    created_card = created_board["cards"][created_card_id]
    assert created_card["title"] == "Document API"

    update_response = client.patch(
        f"/api/cards/{created_card_id}",
        headers=AUTH_HEADERS,
        json={
            "title": "Document board API",
            "details": "Write down the normalized mutation routes.",
            "version": created_card["version"],
        },
    )
    assert update_response.status_code == 200
    updated_card = update_response.json()["board"]["cards"][created_card_id]
    assert updated_card["title"] == "Document board API"
    assert updated_card["version"] == 2

    move_response = client.post(
        f"/api/cards/{created_card_id}/move",
        headers=AUTH_HEADERS,
        json={
            "targetColumnId": "col-review",
            "version": updated_card["version"],
            "afterCardId": "card-6",
        },
    )
    assert move_response.status_code == 200
    moved_board = move_response.json()["board"]
    moved_card = moved_board["cards"][created_card_id]
    assert moved_card["columnId"] == "col-review"
    review_column = next(
        column for column in moved_board["columns"] if column["id"] == "col-review"
    )
    assert review_column["cardIds"] == ["card-6", created_card_id]

    persisted_client = TestClient(
        create_app(Path("/tmp/frontend-out-missing"), db_path=db_path)
    )
    persisted_board = persisted_client.get("/api/board", headers=AUTH_HEADERS).json()["board"]
    assert persisted_board["cards"][created_card_id]["columnId"] == "col-review"

    delete_response = persisted_client.delete(
        f"/api/cards/{created_card_id}?version=3",
        headers=AUTH_HEADERS,
    )
    assert delete_response.status_code == 200
    deleted_board = delete_response.json()["board"]
    assert created_card_id not in deleted_board["cards"]
    review_column_after_delete = next(
        column for column in deleted_board["columns"] if column["id"] == "col-review"
    )
    assert review_column_after_delete["cardIds"] == ["card-6"]


def test_card_move_rejects_stale_version(tmp_path: Path) -> None:
    client, _ = create_test_client(tmp_path)

    response = client.post(
        "/api/cards/card-1/move",
        headers=AUTH_HEADERS,
        json={
            "targetColumnId": "col-review",
            "version": 999,
            "afterCardId": "card-6",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Card version conflict"}


def test_board_routes_require_auth(tmp_path: Path) -> None:
    client, _ = create_test_client(tmp_path)

    response = client.get("/api/board")

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}
