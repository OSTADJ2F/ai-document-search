from fastapi.testclient import TestClient

from app.main import app


def test_health_reports_database_and_redis() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ok", "degraded"}
    assert payload["database"]["status"] == "ok"
    assert payload["redis"]["status"] in {"ok", "unavailable"}
    assert response.headers["X-Request-ID"]
