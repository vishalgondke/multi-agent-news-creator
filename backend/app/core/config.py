"""Centralised settings, loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    # llm_provider: "openai" | "gemini" | "groq" | "auto"
    #   auto -> use whichever key is present (priority: openai > gemini > groq)
    llm_provider: str = "auto"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Google Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Groq (OpenAI-compatible API)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # optional services
    elevenlabs_api_key: str = ""

    # database
    # db_backend: "mysql" (Docker) or "sqlite" (zero-setup local file)
    db_backend: str = "sqlite"
    sqlite_path: str = "./marketnews.db"

    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "marketnews"
    db_user: str = "appuser"
    db_password: str = "apppass"

    redis_url: str = "redis://localhost:6379/0"

    # scheduling
    schedule_tz: str = "Asia/Kolkata"
    schedule_hour: int = 0
    schedule_minute: int = 0

    media_dir: str = "./media"
    cors_origins: str = "http://localhost:5173"

    mock_mode: int = 0

    @property
    def database_url(self) -> str:
        if self.db_backend == "sqlite":
            return f"sqlite+aiosqlite:///{self.sqlite_path}"
        return (
            f"mysql+aiomysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def resolved_provider(self) -> str:
        """Which LLM backend to actually use, given keys + llm_provider setting."""
        if self.llm_provider == "openai":
            return "openai" if self.openai_api_key else "none"
        if self.llm_provider == "gemini":
            return "gemini" if self.gemini_api_key else "none"
        if self.llm_provider == "groq":
            return "groq" if self.groq_api_key else "none"
        # auto: prefer openai, then gemini, then groq
        if self.openai_api_key:
            return "openai"
        if self.gemini_api_key:
            return "gemini"
        if self.groq_api_key:
            return "groq"
        return "none"

    @property
    def mock_collect(self) -> bool:
        # collection needs no API key (just internet) -> only mock when forced
        return bool(self.mock_mode)

    @property
    def mock_llm(self) -> bool:
        # LLM steps need a provider key -> mock when forced OR no usable provider
        return bool(self.mock_mode) or self.resolved_provider == "none"

    # back-compat alias (LLM is the key-dependent path)
    @property
    def mock(self) -> bool:
        return self.mock_llm


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
