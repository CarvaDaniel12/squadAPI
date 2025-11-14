"""
Unit Tests for Token Bucket Rate Limiter

Tests token bucket algorithm implementation with burst support.
"""

import pytest
import asyncio
import time
from src.rate_limit.token_bucket import TokenBucketRateLimiter
from src.models.rate_limit import ProviderRateLimitConfig, RateLimitError


@pytest.mark.unit
@pytest.mark.asyncio
class TestTokenBucketRateLimiter:
    """Test token bucket rate limiting"""
    
    async def test_create_limiter(self):
        """Should create limiter with correct configuration"""
        limiter = TokenBucketRateLimiter(redis_client=None)  # In-memory
        
        config = ProviderRateLimitConfig(
            rpm=12,
            tpm=20000,
            burst=2,
            window_size=60
        )
        
        result = limiter.create_limiter('groq', config)
        
        assert result is not None
        assert 'groq' in limiter.limiters
    
    async def test_acquire_allows_burst(self):
        """Should allow burst requests immediately"""
        limiter = TokenBucketRateLimiter(redis_client=None)
        
        config = ProviderRateLimitConfig(
            rpm=12,
            tpm=20000,
            burst=2,
            window_size=60
        )
        limiter.create_limiter('groq', config)
        
        # First 2 requests should be immediate (burst capacity)
        start = time.time()
        
        async with limiter.acquire('groq'):
            pass  # First request
        
        async with limiter.acquire('groq'):
            pass  # Second request (still in burst)
        
        elapsed = time.time() - start
        
        # Should be very fast (< 100ms for 2 requests)
        assert elapsed < 0.1
    
    async def test_acquire_delays_after_burst(self):
        """Should delay requests after burst capacity exhausted"""
        limiter = TokenBucketRateLimiter(redis_client=None)
        
        config = ProviderRateLimitConfig(
            rpm=12,  # 12 requests per minute = 0.2 tokens/second
            tpm=20000,
            burst=2,
            window_size=60
        )
        limiter.create_limiter('groq', config)
        
        # Burst: 2 immediate requests
        async with limiter.acquire('groq'):
            pass
        async with limiter.acquire('groq'):
            pass
        
        # 3rd request should wait for token refill
        start = time.time()
        async with limiter.acquire('groq'):
            pass
        elapsed = time.time() - start
        
        # Should have waited for token refill (60s / 12 req = 5s per token)
        # With some tolerance for timing
        assert elapsed > 4.0  # At least 4 seconds
        assert elapsed < 6.0  # But not more than 6 seconds
    
    async def test_acquire_with_unknown_provider(self):
        """Should raise error for unknown provider"""
        limiter = TokenBucketRateLimiter(redis_client=None)
        
        with pytest.raises(ValueError, match="No limiter configured"):
            async with limiter.acquire('unknown'):
                pass
    
    async def test_concurrent_requests_limited(self):
        """Should enforce rate limit across concurrent requests"""
        limiter = TokenBucketRateLimiter(redis_client=None)
        
        config = ProviderRateLimitConfig(
            rpm=6,  # 6 RPM = 0.1 tokens/second
            tpm=20000,
            burst=2,
            window_size=60
        )
        limiter.create_limiter('groq', config)
        
        async def make_request():
            async with limiter.acquire('groq'):
                return time.time()
        
        # Try to make 4 requests concurrently
        start = time.time()
        results = await asyncio.gather(*[make_request() for _ in range(4)])
        elapsed = time.time() - start
        
        # First 2 should be immediate (burst)
        # Next 2 should wait for refill (10s per token at 6 RPM)
        assert elapsed > 15.0  # At least 15 seconds for 4 requests (2 burst + 2 * 10s)
    
    async def test_reset_clears_state(self):
        """Should reset limiter state"""
        limiter = TokenBucketRateLimiter(redis_client=None)
        
        config = ProviderRateLimitConfig(
            rpm=12,
            tpm=20000,
            burst=2,
            window_size=60
        )
        limiter.create_limiter('groq', config)
        
        # Exhaust burst
        async with limiter.acquire('groq'):
            pass
        async with limiter.acquire('groq'):
            pass
        
        # Reset
        await limiter.reset('groq')
        
        # Should be able to burst again
        start = time.time()
        async with limiter.acquire('groq'):
            pass
        elapsed = time.time() - start
        
        # After reset, should be immediate again
        assert elapsed < 0.1


@pytest.mark.unit
@pytest.mark.asyncio
class TestTokenBucketIntegration:
    """Integration tests with multiple providers"""
    
    async def test_multiple_providers_independent(self):
        """Each provider should have independent rate limits"""
        limiter = TokenBucketRateLimiter(redis_client=None)
        
        groq_config = ProviderRateLimitConfig(rpm=12, tpm=20000, burst=2, window_size=60)
        cerebras_config = ProviderRateLimitConfig(rpm=30, tpm=180000, burst=5, window_size=60)
        
        limiter.create_limiter('groq', groq_config)
        limiter.create_limiter('cerebras', cerebras_config)
        
        # Exhaust Groq burst
        async with limiter.acquire('groq'):
            pass
        async with limiter.acquire('groq'):
            pass
        
        # Cerebras should still have burst available
        start = time.time()
        async with limiter.acquire('cerebras'):
            pass
        elapsed = time.time() - start
        
        assert elapsed < 0.1  # Cerebras should be immediate

