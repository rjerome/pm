from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import create_app


AUTH_HEADERS = {"Authorization": "Bearer pm-mvp-user-token"}


def create_test_client(tmp_path: Path) -> tuple[TestClient, Path]:
    db_path = tmp_path / "pm.sqlite3"
    client = TestClient(create_app(Path("/tmp/frontend-out-missing"), db_path=db_path))
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
