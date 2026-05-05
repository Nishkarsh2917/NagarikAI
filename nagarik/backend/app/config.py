"""Centralised configuration. Read once, injected everywhere."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite:///./nagarik.db"

    # Storage
    storage_backend: str = "local"
    storage_local_path: str = "../data/storage"

    # LLM
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-haiku-4-5-20251001"

    # Admin
    admin_token: str = "dev-admin-token-change-me"

    # Scheduler
    enable_scheduler: bool = True
    ingestion_cron_hour: int = 0
    ingestion_cron_minute: int = 0
    ingestion_cron_tz: str = "Asia/Kolkata"

    # App
    env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def storage_local_path_abs(self) -> Path:
        # Resolve relative to backend/ directory, not cwd.
        return (Path(__file__).resolve().parent.parent / self.storage_local_path).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
