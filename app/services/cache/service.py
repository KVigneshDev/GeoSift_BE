"""Redis-backed cache service.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Awaitable, Callable, Mapping

from app.core.redis_client import get_redis_client

logger = logging.getLogger(__name__)

# 60 minutes — tuned for filter-aggregate queries.
DEFAULT_TTL_SECONDS = 600 * 6


class CacheService:
    """Stateless wrapper around Redis with JSON serialization."""

    @staticmethod
    def create_cache_key(
        bbox: Mapping[str, float] | None,
        data_type: str,
    ) -> str:
        """Build a deterministic cache key for a bounding-box query.

        Coordinates are rounded to 3 decimals so nearby viewports share cache entries
        """
        bbox = bbox or {"swLng": 0, "swLat": 0, "neLng": 0, "neLat": 0}

        def r(n: float) -> float:
            return round(n * 1e3) / 1e3

        return (
            f"{data_type}:"
            f"{r(bbox['swLng'])}_{r(bbox['swLat'])}_"
            f"{r(bbox['neLng'])}_{r(bbox['neLat'])}"
        )

    @staticmethod
    async def get(key: str) -> Any | None:
        client = await get_redis_client()
        raw = await client.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            # Corrupted entry — treat as a miss.
            return None

    @staticmethod
    async def set(key: str, value: Any, ttl: int = DEFAULT_TTL_SECONDS) -> None:
        client = await get_redis_client()
        await client.set(key, json.dumps(value, default=str), ex=ttl)

    @staticmethod
    async def delete(key: str) -> None:
        client = await get_redis_client()
        await client.delete(key)

    @staticmethod
    async def get_or_set(
        key: str,
        fn: Callable[[], Awaitable[Any]],
        ttl: int = DEFAULT_TTL_SECONDS,
    ) -> Any:
        """Return the cached value or compute, store, and return it."""
        cached = await CacheService.get(key)
        if cached is not None:
            return cached

        result = await fn()
        await CacheService.set(key, result, ttl)
        return result
