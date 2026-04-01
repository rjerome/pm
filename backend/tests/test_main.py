from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_root_serves_placeholder_html_when_frontend_build_is_missing() -> None:
    client = TestClient(create_app(Path("/tmp/frontend-out-missing")))
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Project Management MVP" in response.text
    assert "/api/health" in response.text


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(create_app(Path("/tmp/frontend-out-missing")))
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_returns_token_for_valid_credentials() -> None:
    client = TestClient(create_app(Path("/tmp/frontend-out-missing")))
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "token": "pm-mvp-user-token",
        "username": "user",
    }


def test_login_rejects_invalid_credentials() -> None:
    client = TestClient(create_app(Path("/tmp/frontend-out-missing")))
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_me_requires_valid_bearer_token() -> None:
    client = TestClient(create_app(Path("/tmp/frontend-out-missing")))

    unauthorized_response = client.get("/api/auth/me")
    authorized_response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer pm-mvp-user-token"},
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

    client = TestClient(create_app(frontend_dir))
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Kanban Studio" in response.text
