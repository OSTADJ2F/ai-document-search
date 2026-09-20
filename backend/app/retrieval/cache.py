import hashlib
import json
from abc import ABC, abstractmethod
from functools import lru_cache

from redis import Redis

from app.config import get_settings


class SearchCache(ABC):
    @abstractmethod
    def get(self, key: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value: str) -> None:
        raise NotImplementedError

    @staticmethod
    def key(user_id: str, payload: dict[str, object]) -> str:
        canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
        digest = hashlib.sha256(f"{user_id}:{canonical}".encode()).hexdigest()
        return f"search:{digest}"


class RedisSearchCache(SearchCache):
    def __init__(self, url: str, ttl_seconds: int):
        self.client = Redis.from_url(url, socket_connect_timeout=0.1, socket_timeout=0.1)
        self.ttl_seconds = ttl_seconds

    def get(self, key: str) -> str | None:
        try:
            value = self.client.get(key)
            return value.decode() if isinstance(value, bytes) else value
        except Exception:
            return None

    def set(self, key: str, value: str) -> None:
        try:
            self.client.setex(key, self.ttl_seconds, value)
        except Exception:
            pass


class NullSearchCache(SearchCache):
    def get(self, key: str) -> str | None:
        return None

    def set(self, key: str, value: str) -> None:
        return None


@lru_cache
def get_search_cache() -> SearchCache:
    settings = get_settings()
    if settings.search_cache_ttl_seconds <= 0:
        return NullSearchCache()
    return RedisSearchCache(settings.redis_url, settings.search_cache_ttl_seconds)
