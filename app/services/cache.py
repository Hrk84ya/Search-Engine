"""Redis caching layer for search results."""

import json
import hashlib
from typing import Optional

import redis.asyncio as redis
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()

_redis_client: Optional[redis.Redis] = None


async def get_redis() -> Optional[redis.Redis]:
    """Get or create Redis connection. Returns None if unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        _redis_client = redis.from_url(
            settings.redis_url, decode_responses=True
        )
        await _redis_client.ping()
        logger.info("Redis connected")
        return _redis_client
    except Exception as e:
        logger.warning(f"Redis unavailable, caching disabled: {e}")
        _redis_client = None
        return None


def _cache_key(query: str, top_k: int) -> str:
    raw = f"{query}:{top_k}"
    return f"search:{hashlib.sha256(raw.encode()).hexdigest()}"


async def get_cached_result(query: str, top_k: int) -> Optional[dict]:
    r = await get_redis()
    if r is None:
        return None
    try:
        key = _cache_key(query, top_k)
        data = await r.get(key)
        if data:
            logger.info(f"Cache hit for query: '{query[:40]}'")
            return json.loads(data)
    except Exception:
        pass
    return None


async def set_cached_result(query: str, top_k: int, result: dict, ttl: int = 300):
    r = await get_redis()
    if r is None:
        return
    try:
        key = _cache_key(query, top_k)
        await r.setex(key, ttl, json.dumps(result, default=str))
        logger.info(f"Cached result for query: '{query[:40]}'")
    except Exception:
        pass
