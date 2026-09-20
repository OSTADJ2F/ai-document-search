import hashlib
import threading
import time
from collections import defaultdict, deque
from functools import lru_cache

from fastapi import HTTPException, Request
from redis import Redis

from app.config import get_settings


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int, now: float | None = None) -> bool:
        timestamp = now if now is not None else time.time()
        with self._lock:
            events = self._events[key]
            while events and events[0] <= timestamp - 60:
                events.popleft()
            if len(events) >= limit:
                return False
            events.append(timestamp)
            return True


local_limiter = SlidingWindowLimiter()


@lru_cache
def _redis() -> Redis:
    return Redis.from_url(
        get_settings().redis_url,
        socket_connect_timeout=0.1,
        socket_timeout=0.1,
    )


def enforce_rate_limit(request: Request) -> None:
    settings = get_settings()
    identity = request.client.host if request.client else "unknown"
    raw_key = f"{identity}:{request.url.path}"
    key = hashlib.sha256(raw_key.encode()).hexdigest()
    minute = int(time.time() // 60)
    allowed = False
    try:
        redis_key = f"rate:{key}:{minute}"
        with _redis().pipeline() as pipeline:
            count, _ = pipeline.incr(redis_key).expire(redis_key, 61).execute()
        allowed = int(count) <= settings.rate_limit_per_minute
    except Exception:
        allowed = local_limiter.allow(key, settings.rate_limit_per_minute)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded; try again shortly")
