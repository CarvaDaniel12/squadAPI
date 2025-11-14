"""
Unit Tests for Sliding Window Rate Limiter

Tests sliding window algorithm with Redis sorted sets.
"""

import pytest
import asyncio
import time
from src.rate_limit.sliding_window import SlidingWindowRateLimiter
from src.models.rate_limit import RateLimitError


@pytest.mark.unit
@pytest.mark.asyncio
class TestSlidingWindowRateLimiter:
    """Test sliding window rate limiting"""
    
    async def test_add_request(self):
        """Should add request to window"""
        limiter = SlidingWindowRateLimiter(redis_client=None)  # In-memory
        
        await limiter.add_request('groq', window_size=60)
        
        count = await limiter.get_window_count('groq', window_size=60)
        assert count == 1
    
    async def test_check_limit_empty_window(self):
        """Should allow requests when window is empty"""
        limiter = SlidingWindowRateLimiter(redis_client=None)
        
        result = await limiter.check_limit('groq', rpm_limit=12, window_size=60)
        
        assert result is True
    
    async def test_check_limit_within_limit(self):
        """Should allow requests within limit"""
        limiter = SlidingWindowRateLimiter(redis_client=None)
        
        # Add 5 requests (limit is 12)
        for _ in range(5):
            await limiter.add_request('groq', window_size=60)
        
        result = await limiter.check_limit('groq', rpm_limit=12, window_size=60)
        
        assert result is True
    
    async def test_check_limit_exceeds_limit(self):
        """Should block requests when limit exceeded"""
        limiter = SlidingWindowRateLimiter(redis_client=None)
        
        # Add 12 requests (at limit)
        for _ in range(12):
            await limiter.add_request('groq', window_size=60)
        
        result = await limiter.check_limit('groq', rpm_limit=12, window_size=60)
        
        assert result is False
    
    async def test_cleanup_old_entries(self):
        """Should remove entries older than window_size"""
        limiter = SlidingWindowRateLimiter(redis_client=None)
        
        # Add requests with short window (1 second)
        await limiter.add_request('groq', window_size=1)
        
        count_before = await limiter.get_window_count('groq', window_size=1)
        assert count_before == 1
        
        # Wait for window to expire
        await asyncio.sleep(1.5)
        
        count_after = await limiter.get_window_count('groq', window_size=1)
        assert count_after == 0
    
    async def test_sliding_window_precision(self):
        """Should track requests with precision (not minute boundaries)"""
        limiter = SlidingWindowRateLimiter(redis_client=None)
        
        # Add 12 requests quickly (fill window)
        for _ in range(12):
            await limiter.add_request('groq', window_size=10)
        
        # Should be at limit
        assert await limiter.check_limit('groq', rpm_limit=12, window_size=10) is False
        
        # Wait 2 seconds
        await asyncio.sleep(2)
        
        # Still at limit (window is 10s, not sliding yet)
        count = await limiter.get_window_count('groq', window_size=10)
        assert count == 12
        
        # Wait for full window to expire
        await asyncio.sleep(9)
        
        # Now should be clear
        count = await limiter.get_window_count('groq', window_size=10)
        assert count == 0
    
    async def test_concurrent_requests_counted(self):
        """Should correctly count concurrent requests"""
        limiter = SlidingWindowRateLimiter(redis_client=None)
        
        # Add 10 concurrent requests
        await asyncio.gather(*[
            limiter.add_request('groq', window_size=60)
            for _ in range(10)
        ])
        
        count = await limiter.get_window_count('groq', window_size=60)
        assert count == 10
    
    async def test_reset_clears_window(self):
        """Should reset window state"""
        limiter = SlidingWindowRateLimiter(redis_client=None)
        
        # Fill window
        for _ in range(12):
            await limiter.add_request('groq', window_size=60)
        
        assert await limiter.check_limit('groq', rpm_limit=12, window_size=60) is False
        
        # Reset
        await limiter.reset('groq')
        
        # Should be empty now
        assert await limiter.check_limit('groq', rpm_limit=12, window_size=60) is True
        count = await limiter.get_window_count('groq', window_size=60)
        assert count == 0
    
    async def test_wait_for_capacity_immediate(self):
        """Should return immediately when capacity available"""
        limiter = SlidingWindowRateLimiter(redis_client=None)
        
        start = time.time()
        await limiter.wait_for_capacity('groq', rpm_limit=12, window_size=60, timeout=5.0)
        elapsed = time.time() - start
        
        # Should be immediate
        assert elapsed < 0.1
    
    async def test_wait_for_capacity_timeout(self):
        """Should timeout if capacity not available"""
        limiter = SlidingWindowRateLimiter(redis_client=None)
        
        # Fill window
        for _ in range(12):
            await limiter.add_request('groq', window_size=60)
        
        # Should timeout
        with pytest.raises(RateLimitError, match="timeout"):
            await limiter.wait_for_capacity('groq', rpm_limit=12, window_size=60, timeout=0.5)


@pytest.mark.unit
@pytest.mark.asyncio
class TestSlidingWindowMultiProvider:
    """Test sliding window with multiple providers"""
    
    async def test_independent_windows(self):
        """Each provider should have independent windows"""
        limiter = SlidingWindowRateLimiter(redis_client=None)
        
        # Fill Groq window
        for _ in range(12):
            await limiter.add_request('groq', window_size=60)
        
        # Groq at limit
        assert await limiter.check_limit('groq', rpm_limit=12, window_size=60) is False
        
        # Cerebras should be empty
        assert await limiter.check_limit('cerebras', rpm_limit=30, window_size=60) is True
        
        cerebras_count = await limiter.get_window_count('cerebras', window_size=60)
        assert cerebras_count == 0
    
    async def test_reset_specific_provider(self):
        """Should reset only specified provider"""
        limiter = SlidingWindowRateLimiter(redis_client=None)
        
        # Add requests to both providers
        for _ in range(5):
            await limiter.add_request('groq', window_size=60)
        for _ in range(10):
            await limiter.add_request('cerebras', window_size=60)
        
        # Reset only Groq
        await limiter.reset('groq')
        
        # Groq should be empty, Cerebras unchanged
        groq_count = await limiter.get_window_count('groq', window_size=60)
        cerebras_count = await limiter.get_window_count('cerebras', window_size=60)
        
        assert groq_count == 0
        assert cerebras_count == 10

