"""
Application configuration.

All configuration is loaded from environment variables (or a .env file in
local development). No secrets or environment-specific values are ever
hardcoded here — this module only defines defaults that are safe for a
non-production, non-secret context (e.g. default port numbers).
"""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application settings.

    Values are sourced from environment variables. See `.env.example` for
    the full list of variables required to run the application.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Application ---
    APP_NAME: str = "Nexora AI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development")  # development | staging | production
    DEBUG: bool = Field(default=False)
    API_V1_PREFIX: str = "/api/v1"

    # --- Security / JWT ---
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=14)

    # --- Database ---
    DATABASE_URL: str = Field(
        ...,
        description="Async SQLAlchemy database URL, e.g. postgresql+asyncpg://user:pass@host:5432/db",
    )
    DATABASE_POOL_SIZE: int = Field(default=10)
    DATABASE_MAX_OVERFLOW: int = Field(default=20)
    DATABASE_ECHO: bool = Field(default=False)

    # --- Redis ---
    REDIS_URL: str = Field(default="redis://redis:6379/0")

    # --- CORS ---
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # --- Rate limiting ---
    RATE_LIMIT_AUTH: str = Field(
        default="5/minute",
        description="Rate limit applied to sensitive auth endpoints (login/register).",
    )
    RATE_LIMIT_DEFAULT: str = Field(default="100/minute")

    # --- Logging ---
    LOG_LEVEL: str = Field(default="INFO")
    LOG_JSON: bool = Field(default=True)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors_origins(cls, value):
        """Allow CORS_ORIGINS to be provided as a comma-separated string."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("ENVIRONMENT")
    @classmethod
    def _validate_environment(cls, value: str) -> str:
        allowed = {"development", "staging", "production", "test"}
        if value not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}, got '{value}'")
        return value

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    Using lru_cache means environment variables are read once per process,
    which is the correct behaviour for a running server. Tests that need to
    override settings should call `get_settings.cache_clear()` first.
    """
    return Settings()
