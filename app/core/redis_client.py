"""Redis client bootstrap.
We keep a single connection-pooled client per process and lazy-initialize it on first
use (see `get_redis_client()`). The client is async and compatible with FastAPI's event loop.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from redis.asyncio import Redis
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from app.core.config import settings

logger = logging.getLogger(__name__)

# --- Global Client Logic ---
_redis_client: Any = None #

# --- In-Memory Fallback Class ---
class InMemoryCache:
    """Mimics basic Redis async methods for in-memory storage."""
    def __init__(self):
        self._storage: Dict[str, str] = {}
        logger.info("[cache] Initialized Local In-Memory Fallback")

    async def get(self, key: str) -> Optional[str]:
        return self._storage.get(key)

    async def set(self, key: str, value: str, ex: int = None) -> bool:
        self._storage[key] = value
        # Simple TTL could be added here, but for basic use, this works
        return True

    async def delete(self, key: str) -> int:
        return 1 if self._storage.pop(key, None) else 0

    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        self._storage.clear()


async def get_redis_client() -> Any:
    """Return Redis client or fallback to In-Memory if connection fails."""
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    # Check if URL exists; if not, go straight to fallback
    if not settings.redis_url or "localhost" in settings.redis_url:
        logger.warning("[redis] No production Redis URL found. Using In-Memory fallback.")
        _redis_client = InMemoryCache()
        return _redis_client

    try:
        # Attempt to initialize real Redis
        client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            retry=Retry(ExponentialBackoff(cap=3.0, base=0.2), retries=2),
            retry_on_error=[RedisConnectionError, RedisTimeoutError],
        )
        # Verify connection immediately
        await client.ping()
        _redis_client = client
        logger.info("[redis] Connected successfully to external Redis.")
    except (Exception, RedisConnectionError) as exc:
        logger.error("[redis] Connection failed (%s). Falling back to In-Memory.", exc)
        _redis_client = InMemoryCache()

    return _redis_client

async def close_redis_client() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
