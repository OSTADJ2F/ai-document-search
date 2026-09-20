import pytest
from pydantic import ValidationError

from app.config import Settings
from app.security.rate_limit import SlidingWindowLimiter


def test_sliding_window_rate_limit() -> None:
    limiter = SlidingWindowLimiter()
    assert limiter.allow("user", limit=2, now=0)
    assert limiter.allow("user", limit=2, now=1)
    assert not limiter.allow("user", limit=2, now=2)
    assert limiter.allow("user", limit=2, now=61)


def test_production_rejects_default_or_short_secrets() -> None:
    with pytest.raises(ValidationError):
        Settings(app_env="production", secret_key="short")
    settings = Settings(app_env="production", secret_key="x" * 40)
    assert settings.app_env == "production"
