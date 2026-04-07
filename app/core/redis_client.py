"""Redis client bootstrap.
We keep a single connection-pooled client per process and lazy-initialize it on first
use (see `get_redis_client()`). The client is async and compatible with FastAPI's event loop.
"""
from __future__ import annotations

import logging

from redis.asyncio import Redis
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: Redis | None = None


async def get_redis_client() -> Redis:
    """Return a process-wide Redis client, creating it on first call."""
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    _redis_client = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        retry=Retry(ExponentialBackoff(cap=3.0, base=0.2), retries=3),
        retry_on_error=[RedisConnectionError, RedisTimeoutError],
        health_check_interval=30,
    )

    try:
        _redis_client.ping()
        logger.info("[redis] Client is ready and connected!")
    except Exception as exc:  # noqa: BLE001
        logger.error("[redis] Error: %s", exc)

    return _redis_client


async def close_redis_client() -> None:
    """Close the Redis client (called on app shutdown)."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
