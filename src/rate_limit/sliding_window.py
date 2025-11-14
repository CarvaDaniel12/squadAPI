"""
Sliding Window Rate Limiter

Implements sliding window algorithm using Redis sorted sets.
Tracks requests in last N seconds with precise timestamp tracking.
"""

import asyncio
import time
import uuid
import logging
from typing import Optional

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

from ..models.rate_limit import RateLimitError


logger = logging.getLogger(__name__)


class SlidingWindowRateLimiter:
    """Sliding window rate limiter with Redis backend"""

    def __init__(self, redis_client: Optional['redis.Redis'] = None):
        """
        Initialize sliding window rate limiter

        Args:
            redis_client: Redis async client (optional, will use in-memory if None)
        """
        if redis is None:
            raise ImportError("redis is required. Install: pip install redis")

        self.redis = redis_client
        self._use_memory = redis_client is None

        # In-memory fallback (for testing without Redis)
        self._memory_store: dict[str, list[float]] = {}

        if self._use_memory:
            logger.warning("Sliding window using in-memory storage (no Redis). Not suitable for production!")

    async def add_request(self, provider: str, window_size: int = 60) -> None:
        """
        Add a request timestamp to the sliding window

        Args:
            provider: Provider name
            window_size: Window size in seconds (default: 60)
        """
        key = f"window:{provider}"
        now = time.time()
        request_id = str(uuid.uuid4())

        if self.redis and not self._use_memory:
            # Add to Redis sorted set (score = timestamp)
            await self.redis.zadd(key, {request_id: now})

            # Cleanup old entries (> window_size seconds ago)
            cutoff = now - window_size
            await self.redis.zremrangebyscore(key, '-inf', cutoff)

            # Set expiry (cleanup key after window_size of no activity)
            await self.redis.expire(key, window_size)

            logger.debug(f"Added request to window: {provider} at {now}")
        else:
            # In-memory fallback
            if key not in self._memory_store:
                self._memory_store[key] = []

            self._memory_store[key].append(now)

            # Cleanup old entries
            cutoff = now - window_size
            self._memory_store[key] = [
                ts for ts in self._memory_store[key] if ts > cutoff
            ]

            logger.debug(f"Added request to in-memory window: {provider}")

    async def get_window_count(self, provider: str, window_size: int = 60) -> int:
        """
        Get current number of requests in sliding window

        Args:
            provider: Provider name
            window_size: Window size in seconds (default: 60)

        Returns:
            Number of requests in current window
        """
        key = f"window:{provider}"
        now = time.time()
        cutoff = now - window_size

        if self.redis and not self._use_memory:
            # Count entries in Redis sorted set within window
            count = await self.redis.zcount(key, cutoff, now)
            return count
        else:
            # In-memory fallback
            if key not in self._memory_store:
                return 0

            # Count timestamps within window
            count = sum(1 for ts in self._memory_store[key] if ts > cutoff)
            return count

    async def check_limit(self, provider: str, rpm_limit: int, window_size: int = 60) -> bool:
        """
        Check if request is within rate limit

        Args:
            provider: Provider name
            rpm_limit: Requests per minute limit
            window_size: Window size in seconds (default: 60)

        Returns:
            True if within limit, False if limit exceeded
        """
        key = f"window:{provider}"
        now = time.time()
        cutoff = now - window_size

        if self.redis and not self._use_memory:
            # Count requests in window using Redis
            count = await self.redis.zcount(key, cutoff, now)

            logger.debug(f"Sliding window check: {provider} has {count}/{rpm_limit} requests")
            return count < rpm_limit
        else:
            # In-memory fallback
            if key not in self._memory_store:
                return True

            # Filter to window
            recent = [ts for ts in self._memory_store[key] if ts > cutoff]
            count = len(recent)

            logger.debug(f"Sliding window check (memory): {provider} has {count}/{rpm_limit} requests")
            return count < rpm_limit

    async def get_window_count(self, provider: str, window_size: int = 60) -> int:
        """
        Get current number of requests in the window

        Args:
            provider: Provider name
            window_size: Window size in seconds

        Returns:
            Number of requests in current window
        """
        key = f"window:{provider}"
        now = time.time()
        cutoff = now - window_size

        if self.redis and not self._use_memory:
            count = await self.redis.zcount(key, cutoff, now)
            return count
        else:
            if key not in self._memory_store:
                return 0

            recent = [ts for ts in self._memory_store[key] if ts > cutoff]
            return len(recent)

    async def reset(self, provider: Optional[str] = None):
        """
        Reset sliding window state (for testing)

        Args:
            provider: Provider to reset (all if None)
        """
        if provider:
            key = f"window:{provider}"
            if self.redis and not self._use_memory:
                await self.redis.delete(key)
            else:
                self._memory_store.pop(key, None)

            logger.info(f"Reset sliding window for {provider}")
        else:
            if self.redis and not self._use_memory:
                # Delete all window keys
                keys = await self.redis.keys("window:*")
                if keys:
                    await self.redis.delete(*keys)
            else:
                self._memory_store.clear()

            logger.info("Reset all sliding windows")

    async def wait_for_capacity(
        self,
        provider: str,
        rpm_limit: int,
        window_size: int = 60,
        timeout: float = 30.0
    ) -> None:
        """
        Wait until there's capacity in the window

        Args:
            provider: Provider name
            rpm_limit: Requests per minute limit
            window_size: Window size in seconds
            timeout: Maximum time to wait (seconds)

        Raises:
            RateLimitError: If timeout exceeded
        """
        start = time.time()

        while not await self.check_limit(provider, rpm_limit, window_size):
            elapsed = time.time() - start
            if elapsed > timeout:
                raise RateLimitError(
                    provider=provider,
                    message=f"Sliding window timeout after {timeout}s"
                )

            # Wait a bit before checking again
            await asyncio.sleep(0.1)

        logger.debug(f"Capacity available for {provider}")

