"""
Unit Tests for Combined Rate Limiter

Tests combined Token Bucket + Sliding Window algorithm.
"""

import pytest
import asyncio
import time
from src.rate_limit.combined import CombinedRateLimiter
from src.models.rate_limit import ProviderRateLimitConfig, RateLimitError


@pytest.mark.unit
@pytest.mark.asyncio
class TestCombinedRateLimiter:
    """Test combined rate limiting"""

    async def test_register_provider(self):
        """Should register provider with configuration"""
        limiter = CombinedRateLimiter(redis_client=None)

        config = ProviderRateLimitConfig(
            rpm=12,
            tpm=20000,
            burst=2,
            window_size=60
        )

        limiter.register_provider('groq', config)

        assert 'groq' in limiter._configs
        assert limiter._configs['groq'] == config

    async def test_acquire_allows_burst(self):
        """Should allow burst requests immediately"""
        limiter = CombinedRateLimiter(redis_client=None)

        config = ProviderRateLimitConfig(
            rpm=12,
            tpm=20000,
            burst=2,
            window_size=60
        )
        limiter.register_provider('groq', config)

        # First 2 requests should be immediate (burst)
        start = time.time()

        async with limiter.acquire('groq'):
            pass

        async with limiter.acquire('groq'):
            pass

        elapsed = time.time() - start

        # Should be fast
        assert elapsed < 0.2

    async def test_acquire_enforces_window(self):
        """Should enforce sliding window limit"""
        limiter = CombinedRateLimiter(redis_client=None)

        config = ProviderRateLimitConfig(
            rpm=5,  # Only 5 requests per minute
            tpm=20000,
            burst=5,  # Burst must cover rpm to avoid token shortage during test
            window_size=10  # Use short window for testing
        )
        limiter.register_provider('groq', config)

        # Make 5 requests (fill window)
        for _ in range(5):
            async with limiter.acquire('groq'):
                pass

        # Get state
        state = await limiter.get_state('groq')
        assert state['window_count'] == 5
        assert state['is_limited'] is True

    async def test_get_state(self):
        """Should return current rate limit state"""
        limiter = CombinedRateLimiter(redis_client=None)

        config = ProviderRateLimitConfig(
            rpm=12,
            tpm=20000,
            burst=2,
            window_size=60
        )
        limiter.register_provider('groq', config)

        # Make 3 requests
        for _ in range(3):
            async with limiter.acquire('groq'):
                pass

        state = await limiter.get_state('groq')

        assert state['provider'] == 'groq'
        assert state['rpm_limit'] == 12
        assert state['burst_capacity'] == 2
        assert state['window_count'] == 3
        assert state['is_limited'] is False

    async def test_reset_clears_state(self):
        """Should reset both token bucket and sliding window"""
        limiter = CombinedRateLimiter(redis_client=None)

        config = ProviderRateLimitConfig(
            rpm=12,
            tpm=20000,
            burst=2,
            window_size=60
        )
        limiter.register_provider('groq', config)

        # Make requests
        for _ in range(5):
            async with limiter.acquire('groq'):
                pass

        state_before = await limiter.get_state('groq')
        assert state_before['window_count'] == 5

        # Reset
        await limiter.reset('groq')

        state_after = await limiter.get_state('groq')
        assert state_after['window_count'] == 0

    async def test_unknown_provider_error(self):
        """Should raise error for unregistered provider"""
        limiter = CombinedRateLimiter(redis_client=None)

        with pytest.raises(ValueError, match="not registered"):
            async with limiter.acquire('unknown'):
                pass

    async def test_warmup_multiple_providers(self):
        """Should register multiple providers at once"""
        limiter = CombinedRateLimiter(redis_client=None)

        # Create configs manually (since we don't have config file in test)
        configs = {
            'groq': ProviderRateLimitConfig(rpm=12, tpm=20000, burst=2, window_size=60),
            'cerebras': ProviderRateLimitConfig(rpm=30, tpm=180000, burst=5, window_size=60)
        }

        for provider, config in configs.items():
            limiter.register_provider(provider, config)

        # Both should be registered
        assert 'groq' in limiter._configs
        assert 'cerebras' in limiter._configs


@pytest.mark.unit
@pytest.mark.asyncio
class TestCombinedRateLimiterIntegration:
    """Integration tests for combined rate limiting"""

    async def test_concurrent_requests_both_algorithms(self):
        """Should enforce limits using both algorithms"""
        limiter = CombinedRateLimiter(redis_client=None)

        config = ProviderRateLimitConfig(
            rpm=30,  # 30 requests per minute
            tpm=20000,
            burst=3,  # 3 burst capacity
            window_size=10  # 10 second window
        )
        limiter.register_provider('groq', config)

        async def make_request():
            async with limiter.acquire('groq'):
                await asyncio.sleep(0.01)  # Tiny delay to simulate work
                return time.time()

        # Try to make 4 requests
        start = time.time()
        results = await asyncio.gather(*[make_request() for _ in range(4)])
        elapsed = time.time() - start

        # First 3 should be burst (immediate)
        # 4th may need to wait briefly for refill or window
        # At 30 RPM, refill rate is 2s per token (60s / 30 req)
        # We're being generous with timing to avoid flaky tests
        assert elapsed < 5.0  # Should complete within 5 seconds

        # All 4 should complete
        assert len(results) == 4

    async def test_multiple_providers_independent(self):
        """Each provider should have independent rate limits"""
        limiter = CombinedRateLimiter(redis_client=None)

        groq_config = ProviderRateLimitConfig(rpm=12, tpm=20000, burst=2, window_size=60)
        cerebras_config = ProviderRateLimitConfig(rpm=30, tpm=180000, burst=5, window_size=60)

        limiter.register_provider('groq', groq_config)
        limiter.register_provider('cerebras', cerebras_config)

        # Exhaust Groq burst
        for _ in range(2):
            async with limiter.acquire('groq'):
                pass

        # Cerebras should still have full burst
        start = time.time()
        for _ in range(5):
            async with limiter.acquire('cerebras'):
                pass
        elapsed = time.time() - start

        # Cerebras should be fast (burst available)
        assert elapsed < 0.5

        # Check states
        groq_state = await limiter.get_state('groq')
        cerebras_state = await limiter.get_state('cerebras')

        assert groq_state['window_count'] == 2
        assert cerebras_state['window_count'] == 5

