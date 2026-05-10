from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_HOST: str = "0.0.0.0"
    # Render injects PORT; local .env can use APP_PORT.
    APP_PORT: int = Field(default=8080, validation_alias=AliasChoices("PORT", "APP_PORT"))

    DATABASE_URL: str = "sqlite:///./data/mock.db"

    LWA_JWT_SECRET: str = "dev-secret-change-me"
    LWA_JWT_ALG: str = "HS256"
    ACCESS_TOKEN_TTL_SEC: int = 3600

    STRICT_AUTH: bool = False

    REPORT_MIN_DELAY_SEC: float = 2.0
    REPORT_MAX_DELAY_SEC: float = 5.0
    DOWNLOAD_URL_TTL_SEC: int = 900

    # Absolute base for report download URLs. On Render, RENDER_EXTERNAL_URL is set automatically;
    # we use it when this is still the default localhost value.
    PUBLIC_BASE_URL: str = "http://localhost:8080"
    RENDER_EXTERNAL_URL: str | None = None

    REPORTS_STORAGE_DIR: str = "storage/reports"

    @model_validator(mode="after")
    def resolve_public_base_url(self):
        base = self.PUBLIC_BASE_URL.rstrip("/")
        if self.RENDER_EXTERNAL_URL and base == "http://localhost:8080":
            base = self.RENDER_EXTERNAL_URL.rstrip("/")
        self.PUBLIC_BASE_URL = base
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
