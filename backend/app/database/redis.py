"""
Redis client management.
"""

from redis.asyncio import Redis

from app.core.config import get_settings


def create_redis_client() -> Redis:
    """Create an async Redis client from environment-backed settings."""
    settings = get_settings()
    return Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
