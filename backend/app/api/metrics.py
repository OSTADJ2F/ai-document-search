from typing import cast

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from redis import Redis

from app.config import get_settings
from app.observability import QUEUE_DEPTH

router = APIRouter(tags=["observability"])


@router.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    try:
        redis = Redis.from_url(
            get_settings().redis_url, socket_connect_timeout=0.1, socket_timeout=0.1
        )
        QUEUE_DEPTH.set(cast(float, redis.llen("rq:queue:ingestion")))
    except Exception:
        pass
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
