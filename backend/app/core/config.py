"""Central application configuration."""
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field  # noqa: F401 (used by BaseSettings validators)
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR: Path = Path(__file__).resolve().parent.parent.parent
ENV_FILE: Path = BACKEND_DIR / ".env"
LOGS_DIR: Path = BACKEND_DIR / "logs"
UPLOADS_DIR: Path = BACKEND_DIR / "uploads"


class Settings(BaseSettings):
    # ---- General ----
    APP_NAME: str = "Jarvis"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # ---- LLM: provider selection ----
    # auto | pollinations | groq | gemini | openai | openrouter | ollama
    LLM_PROVIDER: str = "auto"
    LLM_API_KEY: str = ""        # optional — leave blank for the free default
    LLM_MODEL: str = ""          # optional — override the provider's default model
    LLM_TIMEOUT_SEC: int = Field(default=60, ge=5)

    # ---- LLM: local Ollama (only used when LLM_PROVIDER=ollama) ----
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"

    # ---- API server ----
    API_HOST: str = "127.0.0.1"
    API_PORT: int = Field(default=8000, ge=1, le=65535)

    # ---- Regional ----
    TIMEZONE: str = "Asia/Kolkata"
    DEFAULT_LOCATION: str = "Ludhiana"
    NEWS_COUNTRY: str = "IN"

    # ---- Feature flags ----
    ENABLE_CALENDAR: bool = True
    AUTO_OPEN_BROWSER: bool = True

    @property
    def logs_dir(self) -> Path:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        return LOGS_DIR

    @property
    def uploads_dir(self) -> Path:
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        return UPLOADS_DIR

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
