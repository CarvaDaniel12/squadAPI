"""
Token Bucket Rate Limiter

Implements token bucket algorithm using pyrate-limiter with Redis backend.
Provides burst support with token refill rate.
"""

import asyncio
import logging
import math
import time
from dataclasses import dataclass, field
from typing import Optional, Union
from contextlib import asynccontextmanager

try:
    import redis.asyncio as redis
    from pyrate_limiter import Duration, Rate, Limiter
    from pyrate_limiter.buckets import RedisBucket
except ImportError:
    redis = None
    Duration = None
    Rate = None
    Limiter = None
    RedisBucket = None

from ..models.rate_limit import ProviderRateLimitConfig, RateLimitError


logger = logging.getLogger(__name__)


@dataclass
class _InMemoryTokenBucket:
    """Simple async-safe token bucket used when Redis isn't available."""

    capacity: float
    tokens: float
    refill_rate: float  # tokens per second
    window_size: int
    last_refill: float = field(default_factory=time.monotonic)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        if elapsed <= 0:
            return
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    async def request_delay(self) -> float:
        """Returns 0 when a token is granted, or number of seconds to wait."""
        async with self.lock:
            self._refill()
            if self.tokens >= 1:
                self.tokens -= 1
                return 0.0

            if self.refill_rate <= 0:
                return math.inf

            needed = 1 - self.tokens
            # Do not mutate tokens here; caller will re-check after sleeping
            return needed / self.refill_rate

    async def reset(self) -> None:
        async with self.lock:
            self.tokens = self.capacity
            self.last_refill = time.monotonic()


class TokenBucketRateLimiter:
    """Token bucket rate limiter with Redis backend"""

    def __init__(self, redis_client: Optional['redis.Redis'] = None):
        """
        Initialize token bucket rate limiter

        Args:
            redis_client: Redis async client (optional, will use in-memory if None)
        """
        if redis is None or Limiter is None:
            raise ImportError("pyrate-limiter and redis are required. Install: pip install pyrate-limiter redis")

        self.redis = redis_client
        self.limiters: dict[str, Union[Limiter, _InMemoryTokenBucket]] = {}
        self._use_memory = redis_client is None

        if self._use_memory:
            logger.warning("Token bucket using in-memory storage (no Redis). Not suitable for production!")

    def create_limiter(self, provider: str, config: ProviderRateLimitConfig) -> Union[Limiter, _InMemoryTokenBucket]:
        """
        Create a rate limiter for a specific provider

        Args:
            provider: Provider name (e.g., 'groq')
            config: Provider rate limit configuration

        Returns:
            Configured Limiter instance
        """
        # Create rate with burst support
        # Rate(capacity, duration) = capacity requests per duration
        rate = Rate(config.rpm, Duration.MINUTE)

        max_delay_ms = int(config.window_size * 1000)

        if self.redis and not self._use_memory:
            # Use Redis bucket for persistence
            bucket = RedisBucket(self.redis, f"ratelimit:bucket:{provider}")
            limiter: Union[Limiter, _InMemoryTokenBucket] = Limiter(rate, bucket=bucket, max_delay=max_delay_ms)
        else:
            burst_capacity = max(1, config.burst)
            refill_rate = config.rpm / 60.0  # tokens per second
            limiter = _InMemoryTokenBucket(
                capacity=float(burst_capacity),
                tokens=float(burst_capacity),
                refill_rate=refill_rate,
                window_size=config.window_size,
            )

        self.limiters[provider] = limiter
        logger.info(
            f"Created token bucket for {provider}: "
            f"rpm={config.rpm}, burst={config.burst}"
        )

        return limiter

    @asynccontextmanager
    async def acquire(self, provider: str):
        """
        Context manager to acquire a token from the bucket

        Usage:
            async with limiter.acquire('groq'):
                # Make LLM call here
                response = await provider.call(...)

        Args:
            provider: Provider name

        Yields:
            None (context manager)

        Raises:
            RateLimitError: If no tokens available and delay would exceed max_delay
        """
        limiter = self.limiters.get(provider)
        if limiter is None:
            raise ValueError(f"No limiter configured for provider: {provider}")

        try:
            # Try to acquire token
            # This will block if no tokens are available (up to max_delay)
            logger.debug(f"Acquiring token for {provider}")

            if isinstance(limiter, _InMemoryTokenBucket):
                await self._acquire_in_memory(provider, limiter)
            else:
                # pyrate-limiter buckets are keyed by the provided identity
                # Use the provider name so every coroutine competes for the same bucket
                item_hash = provider

                # Acquire with async delay
                result = limiter.try_acquire(item_hash)

                if asyncio.iscoroutine(result):
                    result = await result

                if not result:
                    raise RateLimitError(
                        provider=provider,
                        message="Rate limit exceeded"
                    )

            logger.debug(f"Token acquired for {provider}")
            yield

        except Exception as e:
            logger.error(f"Token bucket error for {provider}: {e}")
            raise RateLimitError(
                provider=provider,
                message=f"Rate limit exceeded: {str(e)}"
            )

    async def _acquire_in_memory(self, provider: str, bucket: _InMemoryTokenBucket) -> None:
        while True:
            delay = await bucket.request_delay()

            if delay == 0:
                return

            if math.isinf(delay) or delay > bucket.window_size:
                raise RateLimitError(provider=provider, message="Rate limit misconfigured")

            await asyncio.sleep(delay)

    def get_available_tokens(self, provider: str) -> int:
        """
        Get number of available tokens for a provider

        Args:
            provider: Provider name

        Returns:
            Number of tokens available (0 if exhausted)
        """
        limiter = self.limiters.get(provider)
        if limiter is None:
            return 0

        if isinstance(limiter, _InMemoryTokenBucket):
            limiter._refill()
            return int(limiter.tokens)

        # This is an approximation - pyrate-limiter doesn't expose token count directly
        # We'd need to inspect the bucket state
        return -1  # Unknown

    async def reset(self, provider: Optional[str] = None):
        """
        Reset rate limiter state (for testing)

        Args:
            provider: Provider to reset (all if None)
        """
        if provider:
            limiter = self.limiters.get(provider)
            if isinstance(limiter, _InMemoryTokenBucket):
                await limiter.reset()
            elif self.redis and not self._use_memory:
                await self.redis.delete(f"ratelimit:bucket:{provider}")
            logger.info(f"Reset token bucket for {provider}")
        else:
            if self.redis and not self._use_memory:
                # Delete all bucket keys
                keys = await self.redis.keys("ratelimit:bucket:*")
                if keys:
                    await self.redis.delete(*keys)
            else:
                for limiter in self.limiters.values():
                    if isinstance(limiter, _InMemoryTokenBucket):
                        await limiter.reset()
            logger.info("Reset all token buckets")

