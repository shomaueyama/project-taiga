from fastapi.testclient import TestClient

from taiga.main import app


def test_health() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_live() -> None:
    response = TestClient(app).get("/api/v1/health/live")
    assert response.status_code == 200
