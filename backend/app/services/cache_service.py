from __future__ import annotations

import json
import logging
from typing import Any

from app.core.config import Settings

try:
    import redis.asyncio as redis_module
except ImportError:  # pragma: no cover - only used for dependency-light local runs
    redis_module = None

logger = logging.getLogger(__name__)


class CacheService:
    """Best-effort Redis JSON cache. Every Redis failure is a safe cache miss."""

    def __init__(self, settings: Settings, client: Any | None = None):
        self.settings = settings
        self._client = client
        if client is None and settings.redis_enabled and redis_module is not None:
            self._client = redis_module.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                db=settings.redis_db,
                decode_responses=True,
                socket_connect_timeout=0.3,
                socket_timeout=0.5,
            )
        if settings.redis_enabled and redis_module is None:
            logger.warning("redis_degraded reason=dependency_unavailable")

    async def get_json(self, key: str) -> dict[str, Any] | None:
        if not self.settings.redis_enabled or self._client is None:
            return None
        try:
            raw = await self._client.get(key)
            if raw is None:
                return None
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            value = json.loads(raw)
            return value if isinstance(value, dict) else None
        except Exception as exc:
            # Redis clients expose backend-specific exception classes. The cache is
            # deliberately a non-critical boundary, so all failures become misses.
            logger.warning("redis_degraded operation=get error_type=%s", type(exc).__name__)
            return None

    async def set_json(self, key: str, value: dict[str, Any]) -> bool:
        if not self.settings.redis_enabled or self._client is None:
            return False
        try:
            payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            await self._client.set(key, payload, ex=self.settings.redis_ttl)
            return True
        except Exception as exc:
            logger.warning("redis_degraded operation=set error_type=%s", type(exc).__name__)
            return False

    async def close(self) -> None:
        if self._client is None:
            return
        close_method = getattr(self._client, "aclose", None) or getattr(self._client, "close", None)
        if close_method is not None:
            result = close_method()
            if hasattr(result, "__await__"):
                await result
