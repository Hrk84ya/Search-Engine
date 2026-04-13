"""Redis-backed rate limiting dependencies."""

from fastapi import HTTPException, Request, status
from app.services.cache import get_redis


def rate_limit(max_requests: int, window_seconds: int = 60):
    """Create a rate limit dependency.

    Args:
        max_requests: Maximum requests allowed in the window.
        window_seconds: Time window in seconds (default 60).
    """

    async def _check(request: Request):
        r = await get_redis()
        if r is None:
            return  # skip rate limiting if Redis is unavailable

        client_ip = request.client.host
        endpoint = request.url.path
        key = f"ratelimit:{endpoint}:{client_ip}"

        current = await r.incr(key)
        if current == 1:
            await r.expire(key, window_seconds)

        if current > max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {max_requests} requests per {window_seconds}s.",
            )

    return _check
