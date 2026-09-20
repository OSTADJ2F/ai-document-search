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


def test_readiness_fails_when_a_dependency_is_unavailable(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr("app.api.health.Redis.from_url", lambda *args, **kwargs: None)
    response = TestClient(app).get("/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
