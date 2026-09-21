from fastapi.testclient import TestClient

from app.main import app


class HealthyConnection:
    def __enter__(self):  # type: ignore[no-untyped-def]
        return self

    def __exit__(self, *args):  # type: ignore[no-untyped-def]
        return None

    def execute(self, statement):  # type: ignore[no-untyped-def]
        return None


class HealthyEngine:
    def connect(self) -> HealthyConnection:
        return HealthyConnection()


class HealthyRedis:
    def ping(self) -> bool:
        return True


def test_health_reports_database_and_redis(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr("app.api.health.engine", HealthyEngine())
    monkeypatch.setattr("app.api.health.Redis.from_url", lambda *args, **kwargs: HealthyRedis())
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"]["status"] == "ok"
    assert payload["redis"]["status"] == "ok"
    assert response.headers["X-Request-ID"]


def test_readiness_fails_when_a_dependency_is_unavailable(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr("app.api.health.engine", HealthyEngine())
    monkeypatch.setattr("app.api.health.Redis.from_url", lambda *args, **kwargs: None)
    response = TestClient(app).get("/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
