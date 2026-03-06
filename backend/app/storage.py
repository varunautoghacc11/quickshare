import json
import logging
from typing import Optional
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

_redis_client: Optional[aioredis.Redis] = None


async def init_redis(url: str) -> aioredis.Redis:
    global _redis_client
    _redis_client = aioredis.from_url(url, decode_responses=True)
    # Ping to verify connection
    await _redis_client.ping()
    logger.info("Redis connection established")
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        logger.info("Redis connection closed")


def get_redis() -> aioredis.Redis:
    if _redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return _redis_client


async def store_share(code: str, data: dict, ttl: int) -> None:
    """Store share data in Redis with TTL (seconds)."""
    client = get_redis()
    key = f"share:{code}"
    serialized = json.dumps(data)
    await client.setex(key, ttl, serialized)
    logger.info(f"Stored share with code {code}, TTL={ttl}s")


async def retrieve_share(code: str) -> Optional[dict]:
    """Retrieve share data from Redis. Returns None if not found or expired."""
    client = get_redis()
    key = f"share:{code}"
    data = await client.get(key)
    if data is None:
        return None
    return json.loads(data)


async def delete_share(code: str) -> None:
    """Delete a share from Redis."""
    client = get_redis()
    key = f"share:{code}"
    await client.delete(key)
    logger.info(f"Deleted share with code {code}")


async def get_ttl(code: str) -> int:
    """Get remaining TTL in seconds for a share. Returns -2 if not found."""
    client = get_redis()
    key = f"share:{code}"
    return await client.ttl(key)
