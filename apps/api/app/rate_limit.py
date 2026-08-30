import time
import os
import redis.asyncio as redis
from fastapi import HTTPException

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

try:
    redis_client = redis.from_url(REDIS_URL)
except Exception:
    redis_client = None

async def check_rate_limit(key: str, limit: int = 100, window: int = 60):
    """
    Simple token bucket / rolling window rate limiter using Redis.
    Allows `limit` requests per `window` seconds for a given `key`.
    """
    if not redis_client:
        return # Skip if redis is not configured
        
    current_time = int(time.time())
    window_start = current_time - window
    
    # Clean up old requests outside the window
    await redis_client.zremrangebyscore(key, 0, window_start)
    
    # Count requests in current window
    request_count = await redis_client.zcard(key)
    
    if request_count >= limit:
        raise HTTPException(status_code=429, detail="Too Many Requests")
        
    # Record new request
    await redis_client.zadd(key, {str(current_time) + "_" + os.urandom(4).hex(): current_time})
    # Set expiration so keys don't live forever
    await redis_client.expire(key, window)
