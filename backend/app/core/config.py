"""Central application configuration."""
import os
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field  # noqa: F401 (used by BaseSettings validators)
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR: Path = Path(__file__).resolve().parent.parent.parent
ENV_FILE: Path = BACKEND_DIR / ".env"

# ══════════════════════════════════════════════════════════════════════
#  Writable data directory
#  Locally this is `backend/` (exactly as before). On read-only hosts
#  such as Vercel / serverless we transparently fall back to the OS temp
#  dir so the app never crashes trying to create folders or write files.
#  You can also override it explicitly with env var JARVIS_DATA_DIR.
# ══════════════════════════════════════════════════════════════════════
def _safe_mkdir(p: Path) -> Path:
    try:
        p.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return p


def _pick_data_dir() -> Path:
    candidates: list[Path] = []
    env = os.environ.get("JARVIS_DATA_DIR")
    if env:
        candidates.append(Path(env))
    candidates.append(BACKEND_DIR)                        # normal local run
    candidates.append(Path(tempfile.gettempdir()) / "jarvis")  # serverless/read-only
    for c in candidates:
        try:
            c.mkdir(parents=True, exist_ok=True)
            probe = c / ".write_test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            return c
        except Exception:
            continue
    return Path(tempfile.gettempdir()) / "jarvis"


DATA_DIR: Path = _pick_data_dir()
LOGS_DIR: Path = DATA_DIR / "logs"
UPLOADS_DIR: Path = DATA_DIR / "uploads"


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
    def data_dir(self) -> Path:
        return _safe_mkdir(DATA_DIR)

    @property
    def logs_dir(self) -> Path:
        return _safe_mkdir(LOGS_DIR)

    @property
    def uploads_dir(self) -> Path:
        return _safe_mkdir(UPLOADS_DIR)

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
