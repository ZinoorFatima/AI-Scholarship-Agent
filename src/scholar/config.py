"""Runtime configuration, loaded from environment / .env."""
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings resolved from environment variables (and a local .env file)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Credentials
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")

    # Models — Pro for the writing-heavy essay stage, Flash for the rest.
    essay_model: str = Field(default="gemini-2.5-pro", alias="SCHOLAR_ESSAY_MODEL")
    default_model: str = Field(default="gemini-2.5-flash", alias="SCHOLAR_DEFAULT_MODEL")

    # Where run artifacts are persisted.
    runs_dir: str = Field(default="runs", alias="SCHOLAR_RUNS_DIR")


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return a cached Settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
