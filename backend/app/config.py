from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "development-only-change-me"
    access_token_expire_minutes: int = 60
    cors_origins: list[str] = ["http://localhost:3000"]
    database_url: str = "sqlite:///./document_search.db"
    redis_url: str = "redis://localhost:6379/0"
    storage_backend: str = "local"
    local_storage_path: Path = Path("data/uploads")
    max_upload_size_mb: int = Field(default=20, ge=1, le=100)
    embedding_provider: str = "local"
    generation_provider: str = "extractive"
    openai_api_key: str | None = None
    process_documents_inline: bool = False
    rate_limit_per_minute: int = Field(default=60, ge=10, le=1000)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str) and not value.startswith("["):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @model_validator(mode="after")
    def validate_production_secret(self) -> "Settings":
        if self.app_env == "production" and (
            len(self.secret_key) < 32 or self.secret_key == "development-only-change-me"
        ):
            raise ValueError(
                "Production SECRET_KEY must be a unique value of at least 32 characters"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
