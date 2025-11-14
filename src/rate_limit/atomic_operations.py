"""
Atomic Operations for Rate Limiting

Provides thread-safe, atomic rate limiting operations using Redis Lua scripts
to prevent race conditions in multi-LLM API environments.
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


# Lua script for atomic rate limit check and increment
ATOMIC_SLIDING_WINDOW_SCRIPT = """
-- Atomic sliding window rate limiter
-- KEYS[1]: window key
-- ARGV[1]: window_size (seconds)
-- ARGV[2]: rpm_limit
-- ARGV[3]: current_time
-- ARGV[4]: request_id (unique identifier)
-- ARGV[5]: provider_name (for logging)

local key = KEYS[1]
local window_size = tonumber(ARGV[1])
local rpm_limit = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local request_id = ARGV[4]
local provider_name = ARGV[5]

-- Calculate cutoff time for window
local cutoff = now - window_size

-- Remove old entries (cleanup)
local removed = redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)
-- redis.call('LPUSH', key .. ':log', string.format('[%s] Cleaned %d old entries', now, removed))

-- Count current entries in window
local count = redis.call('ZCARD', key)

-- Check if we can add this request
if count < rpm_limit then
    -- Add the new request
    redis.call('ZADD', key, now, request_id)
    -- Set expiry on the key
    redis.call('EXPIRE', key, window_size)

    -- Log success (optional, for debugging)
    redis.call('LPUSH', key .. ':log', string.format('[%s] ACCEPT: %s (%d/%d)', now, provider_name, count + 1, rpm_limit))

    return 1  -- Success
else
    -- Log rejection
    redis.call('LPUSH', key .. ':log', string.format('[%s] REJECT: %s (%d/%d)', now, provider_name, count, rpm_limit))

    return 0  -- Failure - rate limit exceeded
end
"""


# Lua script for atomic token bucket operations
ATOMIC_TOKEN_BUCKET_SCRIPT = """
-- Atomic token bucket operations
-- KEYS[1]: bucket key
-- ARGV[1]: capacity
-- ARGV[2]: refill_rate (tokens per second)
-- ARGV[3]: current_time
-- ARGV[4]: provider_name

local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local provider_name = ARGV[4]

-- Get current bucket state
local bucket_data = redis.call('HMGET', key, 'tokens', 'last_refill')
local current_tokens = tonumber(bucket_data[1]) or capacity
local last_refill = tonumber(bucket_data[2]) or now

-- Calculate time elapsed and refill tokens
local elapsed = now - last_refill
if elapsed > 0 then
    local tokens_to_add = elapsed * refill_rate
    current_tokens = math.min(capacity, current_tokens + tokens_to_add)
    last_refill = now
end

-- Check if we have tokens available
if current_tokens >= 1 then
    -- Consume one token
    current_tokens = current_tokens - 1

    -- Update bucket state
    redis.call('HMSET', key, 'tokens', current_tokens, 'last_refill', last_refill)
    redis.call('EXPIRE', key, 300)  -- 5 minute expiry

    -- Log success
    redis.call('LPUSH', key .. ':log', string.format('[%s] CONSUME: %s (%.2f tokens left)', now, provider_name, current_tokens))

    return 1  -- Success
else
    -- Log failure
    redis.call('LPUSH', key .. ':log', string.format('[%s] WAIT: %s (%.2f tokens)', now, provider_name, current_tokens))

    return 0  -- Failure - no tokens available
end
"""


class AtomicRateLimiter:
    """
    Thread-safe rate limiter using Redis Lua scripts for atomic operations.

    This eliminates race conditions by ensuring check-then-act operations
    are executed atomically on the Redis server.
    """

    def __init__(self, redis_client: Optional['redis.Redis'] = None):
        """
        Initialize atomic rate limiter

        Args:
            redis_client: Redis async client (required for production)
        """
        if redis is None:
            raise ImportError("redis package is required. Install: pip install redis")

        self.redis = redis_client
        self._sliding_window_script_sha = None
        self._token_bucket_script_sha = None

        if not self.redis:
            logger.warning("AtomicRateLimiter initialized without Redis client")

    async def _load_scripts(self):
        """Load Lua scripts into Redis and cache their SHAs"""
        try:
            if self.redis:
                self._sliding_window_script_sha = await self.redis.script_load(ATOMIC_SLIDING_WINDOW_SCRIPT)
                self._token_bucket_script_sha = await self.redis.script_load(ATOMIC_TOKEN_BUCKET_SCRIPT)
                logger.debug("Loaded atomic rate limiting scripts into Redis")
        except Exception as e:
            logger.error(f"Failed to load atomic scripts: {e}")
            raise

    async def acquire_sliding_window_slot(
        self,
        provider: str,
        window_size: int = 60,
        rpm_limit: int = 10
    ) -> bool:
        """
        Atomically acquire a slot in the sliding window rate limiter

        This operation is completely atomic - it checks the limit and increments
        the counter in a single Redis operation, preventing race conditions.

        Args:
            provider: Provider name (e.g., 'groq', 'gemini')
            window_size: Window size in seconds (default: 60)
            rpm_limit: Requests per minute limit (default: 10)

        Returns:
            True if slot acquired, False if rate limit exceeded

        Raises:
            RateLimitError: If Redis operation fails
        """
        if not self.redis:
            raise RuntimeError("Redis client required for atomic operations")

        # Load scripts if not already loaded
        if not self._sliding_window_script_sha:
            await self._load_scripts()

        key = f"atomic:window:{provider}"
        now = time.time()
        request_id = str(uuid.uuid4())

        try:
            # Execute atomic script
            result = await self.redis.evalsha(
                self._sliding_window_script_sha,
                1,  # number of keys
                key,  # key
                window_size,  # argv[1]
                rpm_limit,    # argv[2]
                now,          # argv[3]
                request_id,   # argv[4]
                provider      # argv[5]
            )

            # Redis returns 1 for success, 0 for failure
            success = bool(result)

            if success:
                logger.debug(f"Atomic rate limit acquired for {provider}: {rpm_limit}/{window_size}s window")
            else:
                logger.warning(f"Atomic rate limit exceeded for {provider}: {rpm_limit}/{window_size}s window")

            return success

        except Exception as e:
            logger.error(f"Atomic sliding window operation failed for {provider}: {e}")
            raise RateLimitError(
                provider=provider,
                message=f"Atomic rate limit operation failed: {str(e)}"
            )

    async def acquire_token_bucket_token(
        self,
        provider: str,
        capacity: int = 10,
        refill_rate: float = 0.167  # 10 tokens / 60 seconds
    ) -> bool:
        """
        Atomically acquire a token from the token bucket

        Args:
            provider: Provider name
            capacity: Maximum token capacity
            refill_rate: Tokens refilled per second

        Returns:
            True if token acquired, False if no tokens available

        Raises:
            RateLimitError: If Redis operation fails
        """
        if not self.redis:
            raise RuntimeError("Redis client required for atomic operations")

        # Load scripts if not already loaded
        if not self._token_bucket_script_sha:
            await self._load_scripts()

        key = f"atomic:bucket:{provider}"
        now = time.time()

        try:
            # Execute atomic script
            result = await self.redis.evalsha(
                self._token_bucket_script_sha,
                1,  # number of keys
                key,         # key
                capacity,    # argv[1]
                refill_rate, # argv[2]
                now,         # argv[3]
                provider     # argv[4]
            )

            # Redis returns 1 for success, 0 for failure
            success = bool(result)

            if success:
                logger.debug(f"Atomic token acquired for {provider}: capacity={capacity}, rate={refill_rate}")
            else:
                logger.warning(f"Atomic token bucket empty for {provider}: capacity={capacity}")

            return success

        except Exception as e:
            logger.error(f"Atomic token bucket operation failed for {provider}: {e}")
            raise RateLimitError(
                provider=provider,
                message=f"Atomic token bucket operation failed: {str(e)}"
            )

    async def get_atomic_stats(self, provider: str) -> dict:
        """
        Get current state of atomic rate limiter for a provider

        Args:
            provider: Provider name

        Returns:
            Dictionary with current state information
        """
        if not self.redis:
            return {"error": "No Redis client available"}

        try:
            # Get sliding window count
            window_key = f"atomic:window:{provider}"
            now = time.time()
            cutoff = now - 60  # 1 minute window

            window_count = await self.redis.zcount(window_key, cutoff, now)

            # Get token bucket state
            bucket_key = f"atomic:bucket:{provider}"
            bucket_data = await self.redis.hmget(bucket_key, 'tokens', 'last_refill')
            tokens = float(bucket_data[0]) if bucket_data[0] else 0

            return {
                'provider': provider,
                'window_count': window_count,
                'available_tokens': tokens,
                'window_key': window_key,
                'bucket_key': bucket_key,
                'last_updated': now
            }

        except Exception as e:
            logger.error(f"Failed to get atomic stats for {provider}: {e}")
            return {"error": str(e)}

    async def reset_atomic_state(self, provider: str = None):
        """
        Reset atomic rate limiter state (for testing)

        Args:
            provider: Provider to reset (all if None)
        """
        if not self.redis:
            return

        try:
            if provider:
                # Reset specific provider
                window_key = f"atomic:window:{provider}"
                bucket_key = f"atomic:bucket:{provider}"

                await self.redis.delete(window_key, bucket_key)
                logger.info(f"Reset atomic state for provider: {provider}")
            else:
                # Reset all providers
                window_keys = await self.redis.keys("atomic:window:*")
                bucket_keys = await self.redis.keys("atomic:bucket:*")

                if window_keys or bucket_keys:
                    await self.redis.delete(*(window_keys + bucket_keys))
                logger.info("Reset all atomic rate limiter state")

        except Exception as e:
            logger.error(f"Failed to reset atomic state: {e}")

    async def wait_for_atomic_slot(
        self,
        provider: str,
        window_size: int = 60,
        rpm_limit: int = 10,
        timeout: float = 30.0
    ) -> bool:
        """
        Wait for a slot to become available with atomic operations

        Args:
            provider: Provider name
            window_size: Window size in seconds
            rpm_limit: RPM limit
            timeout: Maximum time to wait in seconds

        Returns:
            True if slot acquired, False if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            if await self.acquire_sliding_window_slot(provider, window_size, rpm_limit):
                return True

            # Wait a bit before retrying
            await asyncio.sleep(0.1)

        logger.warning(f"Timeout waiting for atomic slot for {provider}")
        return False
