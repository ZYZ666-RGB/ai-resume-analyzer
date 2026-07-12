from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # Environment variables still work without python-dotenv.
    pass


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


def _as_float(value: str | None, default: float) -> float:
    try:
        return float(value) if value is not None else default
    except ValueError:
        return default


class Settings(BaseModel):
    app_name: str = "AI Resume Analyzer"
    app_env: str = "development"
    debug: bool = False
    port: int = 8000
    api_prefix: str = "/api"

    dashscope_api_key: str | None = None
    dashscope_model: str = "qwen3.7-plus"
    dashscope_timeout: float = Field(default=120.0, gt=0)
    dashscope_base_url: str = (
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    )

    redis_enabled: bool = True
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str | None = None
    redis_db: int = 0
    redis_ttl: int = 86400

    max_upload_size_mb: int = 10
    max_pdf_pages: int = Field(default=50, gt=0)
    return_cleaned_text: bool = False
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @classmethod
    def from_environment(cls) -> "Settings":
        origins = [
            item.strip()
            for item in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
            if item.strip()
        ]
        api_key = os.getenv("DASHSCOPE_API_KEY", "").strip() or None
        password = os.getenv("REDIS_PASSWORD", "").strip() or None
        return cls(
            app_name=os.getenv("APP_NAME", "AI Resume Analyzer"),
            app_env=os.getenv("APP_ENV", "development"),
            debug=_as_bool(os.getenv("DEBUG"), False),
            port=_as_int(os.getenv("PORT"), 8000),
            dashscope_api_key=api_key,
            dashscope_model=os.getenv("DASHSCOPE_MODEL", "qwen3.7-plus"),
            dashscope_timeout=_as_float(os.getenv("DASHSCOPE_TIMEOUT"), 120.0),
            dashscope_base_url=os.getenv(
                "DASHSCOPE_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            ),
            redis_enabled=_as_bool(os.getenv("REDIS_ENABLED"), True),
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=_as_int(os.getenv("REDIS_PORT"), 6379),
            redis_password=password,
            redis_db=_as_int(os.getenv("REDIS_DB"), 0),
            redis_ttl=_as_int(os.getenv("REDIS_TTL"), 86400),
            max_upload_size_mb=_as_int(os.getenv("MAX_UPLOAD_SIZE_MB"), 10),
            max_pdf_pages=_as_int(os.getenv("MAX_PDF_PAGES"), 50),
            return_cleaned_text=_as_bool(os.getenv("RETURN_CLEANED_TEXT"), False),
            cors_origins=origins or ["http://localhost:5173"],
        )


@lru_cache
def get_settings() -> Settings:
    return Settings.from_environment()
