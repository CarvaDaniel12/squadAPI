"""
Combined Rate Limiter

Combines Token Bucket and Sliding Window algorithms for robust rate limiting.
- Token Bucket: Burst support with token refill
- Sliding Window: Precise rate tracking without boundary clustering

Both must pass for request to proceed.
"""

import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

from prometheus_client import Gauge

from .token_bucket import TokenBucketRateLimiter
from .sliding_window import SlidingWindowRateLimiter
from .atomic_operations import AtomicRateLimiter
from ..models.rate_limit import ProviderRateLimitConfig, RateLimitError
from ..config.rate_limits import RateLimitConfigLoader


logger = logging.getLogger(__name__)

# Prometheus metrics for rate limiting observability
rate_limit_tokens_available = Gauge(
    'rate_limit_tokens_available',
    'Available tokens in semaphore (concurrent request slots)',
    ['provider']
)

rate_limit_tokens_capacity = Gauge(
    'rate_limit_tokens_capacity',
    'Maximum semaphore capacity (max concurrent requests)',
    ['provider']
)

rate_limit_window_occupancy = Gauge(
    'rate_limit_window_occupancy',
    'Current requests in sliding window',
    ['provider']
)

rate_limit_rpm_limit = Gauge(
    'rate_limit_rpm_limit',
    'Configured RPM limit',
    ['provider']
)

rate_limit_burst_capacity = Gauge(
    'rate_limit_burst_capacity',
    'Configured burst capacity',
    ['provider']
)


class CombinedRateLimiter:
    """
    Combined rate limiter using both Token Bucket and Sliding Window

    Strategy:
    1. Check sliding window first (cheaper, fast rejection)
    2. Acquire token bucket (may delay for token refill)
    3. Add request to sliding window
    4. Execute request
    """

    def __init__(
        self,
        redis_client: Optional['redis.Redis'] = None,
        config_loader: Optional[RateLimitConfigLoader] = None
    ):
        """
        Initialize combined rate limiter

        Args:
            redis_client: Redis async client (optional)
            config_loader: Configuration loader (optional, uses default if None)
        """
        self.redis = redis_client
        self.token_bucket = TokenBucketRateLimiter(redis_client)
        self.sliding_window = SlidingWindowRateLimiter(redis_client)
        self.atomic_limiter = AtomicRateLimiter(redis_client)

        # Load configuration
        if config_loader is None:
            from ..config.rate_limits import get_rate_limit_config
            config_loader = get_rate_limit_config()

        self.config_loader = config_loader
        self._configs: dict[str, ProviderRateLimitConfig] = {}
        self._use_atomic = redis_client is not None  # Use atomic operations only with Redis

    def register_provider(self, provider: str, config: Optional[ProviderRateLimitConfig] = None):
        """
        Register a provider with rate limiting configuration

        Args:
            provider: Provider name (e.g., 'groq')
            config: Provider configuration (loads from YAML if None)
        """
        if config is None:
            # Load from configuration file
            config = self.config_loader.get_provider_config(provider)
            if config is None:
                raise ValueError(f"No rate limit config found for provider: {provider}")

        # Store config
        self._configs[provider] = config

        # Create token bucket limiter
        self.token_bucket.create_limiter(provider, config)

        # Set static configuration metrics
        rate_limit_rpm_limit.labels(provider=provider).set(config.rpm)
        rate_limit_burst_capacity.labels(provider=provider).set(config.burst)
        # Note: tokens_capacity will be set when we know actual concurrent limit
        # For now, using burst as proxy (may need adjustment based on actual limiter design)
        rate_limit_tokens_capacity.labels(provider=provider).set(config.burst or config.rpm)

        logger.info(
            f"Registered provider '{provider}' with rate limits: "
            f"rpm={config.rpm}, burst={config.burst}"
        )

    def get_provider_config(self, provider: str) -> ProviderRateLimitConfig:
        """Get configuration for a provider"""
        if provider not in self._configs:
            raise ValueError(f"Provider not registered: {provider}")
        return self._configs[provider]

    @asynccontextmanager
    async def acquire(self, provider: str):
        """
        Acquire rate limit permission using atomic operations to prevent race conditions

        This method uses Redis Lua scripts for atomic operations when available,
        falling back to the original non-atomic method when Redis is not available.

        Usage:
            async with combined_limiter.acquire('groq'):
                response = await provider.call(...)

        Args:
            provider: Provider name

        Yields:
            None (context manager)

        Raises:
            RateLimitError: If rate limit exceeded
        """
        config = self.get_provider_config(provider)

        # Use atomic operations if Redis is available (eliminates race conditions)
        if self._use_atomic:
            async with self._acquire_atomic(provider, config):
                yield
        else:
            # Fallback to original method (with race condition risk)
            logger.warning("Using non-atomic rate limiting - race conditions possible without Redis")
            async with self._acquire_fallback(provider, config):
                yield

    @asynccontextmanager
    async def _acquire_atomic(self, provider: str, config: ProviderRateLimitConfig):
        """
        Atomic rate limit acquisition using Redis Lua scripts

        This completely eliminates race conditions by performing check-and-increment
        as a single atomic operation on the Redis server.

        Args:
            provider: Provider name
            config: Provider configuration
        """
        try:
            # Step 1: Acquire atomic slot (check + increment in single operation)
            logger.debug(f"Acquiring atomic slot for {provider}")
            if not await self.atomic_limiter.acquire_sliding_window_slot(
                provider=provider,
                window_size=config.window_size,
                rpm_limit=config.rpm
            ):
                # Rate limit exceeded
                logger.warning(f"Atomic rate limit exceeded for {provider}")
                raise RateLimitError(
                    provider=provider,
                    message=f"Rate limit exceeded - atomic operation prevented violation"
                )

            # Step 2: Acquire token bucket atomically
            logger.debug(f"Acquiring atomic token bucket for {provider}")
            token_bucket_capacity = config.burst or config.rpm
            refill_rate = config.rpm / 60.0  # tokens per second

            if not await self.atomic_limiter.acquire_token_bucket_token(
                provider=provider,
                capacity=token_bucket_capacity,
                refill_rate=refill_rate
            ):
                # This shouldn't happen if sliding window passed, but handle it
                logger.warning(f"Atomic token bucket failed for {provider} after sliding window passed")
                raise RateLimitError(
                    provider=provider,
                    message=f"Token bucket unavailable after atomic sliding window check"
                )

            # Step 3: Update metrics using atomic stats
            atomic_stats = await self.atomic_limiter.get_atomic_stats(provider)
            window_count = atomic_stats.get('window_count', 0)
            rate_limit_window_occupancy.labels(provider=provider).set(window_count)

            logger.info(f"Atomic rate limit acquired for {provider}: {window_count}/{config.rpm}")

            # Step 4: Yield to caller (execute request)
            yield

        except RateLimitError:
            # Re-raise rate limit errors
            raise
        except Exception as e:
            logger.error(f"Atomic rate limiter error for {provider}: {e}")
            raise RateLimitError(
                provider=provider,
                message=f"Atomic rate limiter internal error: {str(e)}"
            )

    @asynccontextmanager
    async def _acquire_fallback(self, provider: str, config: ProviderRateLimitConfig):
        """
        Fallback rate limit acquisition (original method with race condition risk)

        This method has the race condition but is kept for compatibility when
        Redis is not available.

        Args:
            provider: Provider name
            config: Provider configuration
        """
        try:
            # Step 1: Check sliding window (fast rejection if over limit) - RACE CONDITION HERE
            logger.debug(f"Checking sliding window for {provider} (fallback mode)")
            if not await self.sliding_window.check_limit(
                provider,
                rpm_limit=config.rpm,
                window_size=config.window_size
            ):
                # Window is full - wait for capacity
                logger.warning(f"Sliding window full for {provider}, waiting for capacity...")
                await self.sliding_window.wait_for_capacity(
                    provider,
                    rpm_limit=config.rpm,
                    window_size=config.window_size,
                    timeout=30.0
                )

            # Step 2: Acquire token bucket (may delay for refill)
            logger.debug(f"Acquiring token bucket for {provider} (fallback mode)")
            async with self.token_bucket.acquire(provider):
                # Step 3: Add to sliding window - RACE CONDITION HERE
                await self.sliding_window.add_request(provider, window_size=config.window_size)

                # Step 4: Update Prometheus metrics
                window_count = await self.sliding_window.get_window_count(
                    provider,
                    window_size=config.window_size
                )
                rate_limit_window_occupancy.labels(provider=provider).set(window_count)

                logger.warning(f"Rate limit acquired for {provider} (with race condition risk): {window_count}/{config.rpm}")

                # Step 5: Yield to caller (execute request)
                yield

        except RateLimitError:
            # Re-raise rate limit errors
            raise
        except Exception as e:
            logger.error(f"Rate limiter error for {provider}: {e}")
            raise RateLimitError(
                provider=provider,
                message=f"Rate limiter internal error: {str(e)}"
            )

    async def get_state(self, provider: str) -> dict:
        """
        Get current rate limit state for a provider

        Args:
            provider: Provider name

        Returns:
            Dict with state information
        """
        config = self.get_provider_config(provider)

        window_count = await self.sliding_window.get_window_count(
            provider,
            window_size=config.window_size
        )

        return {
            'provider': provider,
            'rpm_limit': config.rpm,
            'burst_capacity': config.burst,
            'window_count': window_count,
            'window_limit': config.rpm,
            'is_limited': window_count >= config.rpm
        }

    async def reset(self, provider: Optional[str] = None):
        """
        Reset rate limiter state (for testing)

        Args:
            provider: Provider to reset (all if None)
        """
        await self.token_bucket.reset(provider)
        await self.sliding_window.reset(provider)

        # Reset atomic state if using Redis
        if self._use_atomic:
            await self.atomic_limiter.reset_atomic_state(provider)

        logger.info(f"Reset combined rate limiter for {provider or 'all providers'}")

    async def warmup(self, providers: list[str]):
        """
        Pre-register multiple providers

        Args:
            providers: List of provider names to register
        """
        for provider in providers:
            try:
                self.register_provider(provider)
            except Exception as e:
                logger.warning(f"Failed to register provider {provider}: {e}")

        logger.info(f"Warmed up rate limiters for {len(self._configs)} providers")

    def get_atomic_status(self) -> dict:
        """
        Get status of atomic rate limiting system

        Returns:
            Dictionary with atomic rate limiting configuration and status
        """
        return {
            'atomic_enabled': self._use_atomic,
            'redis_available': self.redis is not None,
            'atomic_limiter_initialized': hasattr(self, 'atomic_limiter'),
            'total_providers': len(self._configs),
            'provider_configs': {
                name: {
                    'rpm': config.rpm,
                    'burst': config.burst,
                    'window_size': config.window_size
                }
                for name, config in self._configs.items()
            }
        }

    def enable_atomic_fallback_warnings(self):
        """Enable warnings when falling back to non-atomic mode"""
        if not self._use_atomic:
            logger.warning(
                "⚠️  ATOMIC RATE LIMITING DISABLED ⚠️\n"
                "Running with race condition risk!\n"
                "To enable atomic operations:\n"
                "1. Install Redis: docker run -d -p 6379:6379 redis:alpine\n"
                "2. Set REDIS_URL environment variable\n"
                "3. Restart application\n"
                "Current providers: " + ", ".join(self._configs.keys())
            )
