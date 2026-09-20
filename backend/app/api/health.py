from typing import Literal

from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from redis import Redis
from sqlalchemy import text

from app.config import get_settings
from app.database.session import engine

router = APIRouter(tags=["health"])


class DependencyHealth(BaseModel):
    status: Literal["ok", "unavailable"]
    detail: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    database: DependencyHealth
    redis: DependencyHealth


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return dependency_health()


@router.get("/ready", response_model=HealthResponse)
def readiness_check(response: Response) -> HealthResponse:
    health = dependency_health()
    if health.status == "degraded":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return health


def dependency_health() -> HealthResponse:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database = DependencyHealth(status="ok")
    except Exception as exc:  # pragma: no cover - exercised against unavailable services
        database = DependencyHealth(status="unavailable", detail=type(exc).__name__)

    settings = get_settings()
    try:
        Redis.from_url(settings.redis_url, socket_connect_timeout=0.25).ping()
        redis = DependencyHealth(status="ok")
    except Exception as exc:
        redis = DependencyHealth(status="unavailable", detail=type(exc).__name__)

    status = "ok" if database.status == redis.status == "ok" else "degraded"
    return HealthResponse(status=status, database=database, redis=redis)
