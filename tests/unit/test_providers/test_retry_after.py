"""
Unit Tests for Retry-After Handler

Tests Retry-After header parsing and handling.
"""

import pytest
import asyncio
import time
from datetime import datetime, timezone, timedelta
from src.providers.retry_after import (
    parse_retry_after,
    wait_for_retry_after,
    call_with_retry_after,
    extract_retry_after_from_response,
    RetryAfterHandler
)
from src.providers.retry import RateLimitExceededError


@pytest.mark.unit
class TestParseRetryAfter:
    """Test Retry-After header parsing"""
    
    def test_parse_delay_seconds(self):
        """Should parse delay-seconds format"""
        result = parse_retry_after("30")
        
        assert result == 30.0
    
    def test_parse_large_delay(self):
        """Should parse large delay values"""
        result = parse_retry_after("300")
        
        assert result == 300.0
    
    def test_parse_http_date(self):
        """Should parse HTTP-date format"""
        # Create a time 60 seconds in the future
        future_time = datetime.now(timezone.utc) + timedelta(seconds=60)
        http_date = future_time.strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        result = parse_retry_after(http_date)
        
        # Should be approximately 60 seconds (within 2s tolerance)
        assert 58.0 < result < 62.0
    
    def test_parse_invalid_format(self):
        """Should return None for invalid format"""
        result = parse_retry_after("invalid-format")
        
        assert result is None
    
    def test_parse_empty(self):
        """Should return None for empty value"""
        result = parse_retry_after(None)
        
        assert result is None
    
    def test_parse_zero(self):
        """Should return None for zero or negative"""
        result = parse_retry_after("0")
        
        assert result is None
    
    def test_parse_negative(self):
        """Should return None for negative delay"""
        result = parse_retry_after("-10")
        
        assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
class TestWaitForRetryAfter:
    """Test Retry-After wait logic"""
    
    async def test_wait_within_max(self):
        """Should wait for specified duration"""
        start = time.time()
        result = await wait_for_retry_after(0.1, max_wait=1.0)
        elapsed = time.time() - start
        
        assert result is True
        assert 0.08 < elapsed < 0.15  # Approximately 0.1s
    
    async def test_wait_exceeds_max(self):
        """Should not wait if exceeds max_wait"""
        start = time.time()
        result = await wait_for_retry_after(10.0, max_wait=1.0)
        elapsed = time.time() - start
        
        assert result is False
        assert elapsed < 0.1  # Should return immediately
    
    async def test_wait_at_boundary(self):
        """Should wait if exactly at max_wait"""
        start = time.time()
        result = await wait_for_retry_after(1.0, max_wait=1.0)
        elapsed = time.time() - start
        
        assert result is True
        assert 0.95 < elapsed < 1.1


@pytest.mark.unit
@pytest.mark.asyncio
class TestCallWithRetryAfter:
    """Test call_with_retry_after function"""
    
    async def test_success_no_retry(self):
        """Should succeed without retry"""
        call_count = 0
        
        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await call_with_retry_after(successful_func)
        
        assert result == "success"
        assert call_count == 1
    
    async def test_retry_with_retry_after(self):
        """Should respect Retry-After and retry"""
        call_count = 0
        
        async def func_with_retry_after():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RateLimitExceededError("Rate limited", retry_after=0.1)
            return "success"
        
        start = time.time()
        result = await call_with_retry_after(func_with_retry_after)
        elapsed = time.time() - start
        
        assert result == "success"
        assert call_count == 2
        assert elapsed >= 0.1  # Should have waited
    
    async def test_retry_after_exceeds_max_wait(self):
        """Should give up if Retry-After exceeds max_wait"""
        call_count = 0
        
        async def func_long_retry():
            nonlocal call_count
            call_count += 1
            raise RateLimitExceededError("Rate limited", retry_after=10.0)
        
        with pytest.raises(RateLimitExceededError):
            await call_with_retry_after(func_long_retry, max_wait=1.0)
        
        assert call_count == 1  # Should not retry
    
    async def test_fallback_to_exponential(self):
        """Should fall back to exponential backoff if no Retry-After"""
        call_count = 0
        
        async def func_no_retry_after():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RateLimitExceededError("Rate limited", retry_after=None)
            return "success"
        
        # Note: This will use exponential backoff from call_with_retry
        # which has its own retry logic
        result = await call_with_retry_after(
            func_no_retry_after,
            fallback_to_exponential=True
        )
        
        assert result == "success"
        assert call_count >= 2
    
    async def test_no_fallback(self):
        """Should give up if no Retry-After and fallback disabled"""
        call_count = 0
        
        async def func_no_retry_after():
            nonlocal call_count
            call_count += 1
            raise RateLimitExceededError("Rate limited", retry_after=None)
        
        with pytest.raises(RateLimitExceededError):
            await call_with_retry_after(
                func_no_retry_after,
                fallback_to_exponential=False
            )
        
        assert call_count == 1


@pytest.mark.unit
class TestExtractRetryAfterFromResponse:
    """Test extracting Retry-After from response"""
    
    def test_extract_from_headers_dict(self):
        """Should extract from headers dict"""
        headers = {"Retry-After": "30"}
        
        result = extract_retry_after_from_response(None, headers=headers)
        
        assert result == 30.0
    
    def test_extract_case_insensitive(self):
        """Should handle case-insensitive header names"""
        headers = {"retry-after": "45"}
        
        result = extract_retry_after_from_response(None, headers=headers)
        
        assert result == 45.0
    
    def test_extract_from_response_object(self):
        """Should extract from response.headers"""
        class MockResponse:
            def __init__(self):
                self.headers = {"Retry-After": "60"}
        
        response = MockResponse()
        result = extract_retry_after_from_response(response)
        
        assert result == 60.0
    
    def test_extract_missing_header(self):
        """Should return None if header missing"""
        headers = {"Content-Type": "application/json"}
        
        result = extract_retry_after_from_response(None, headers=headers)
        
        assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
class TestRetryAfterHandler:
    """Test RetryAfterHandler"""
    
    async def test_handle_429_with_retry_after(self):
        """Should handle 429 with Retry-After"""
        handler = RetryAfterHandler()
        
        start = time.time()
        result = await handler.handle_429('groq', retry_after=0.1, max_wait=1.0)
        elapsed = time.time() - start
        
        assert result is True
        assert elapsed >= 0.1
        
        stats = handler.get_stats()
        assert stats['total_429s'] == 1
        assert stats['retry_after_present'] == 1
        assert stats['retry_after_respected'] == 1
    
    async def test_handle_429_without_retry_after(self):
        """Should handle 429 without Retry-After"""
        handler = RetryAfterHandler()
        
        result = await handler.handle_429('groq', retry_after=None)
        
        assert result is True  # Fall back to exponential
        
        stats = handler.get_stats()
        assert stats['total_429s'] == 1
        assert stats['retry_after_present'] == 0
    
    async def test_handle_429_exceeds_max(self):
        """Should reject if Retry-After exceeds max_wait"""
        handler = RetryAfterHandler()
        
        result = await handler.handle_429('groq', retry_after=10.0, max_wait=1.0)
        
        assert result is False
        
        stats = handler.get_stats()
        assert stats['retry_after_exceeded'] == 1
    
    async def test_get_stats_percentages(self):
        """Should calculate statistics correctly"""
        handler = RetryAfterHandler()
        
        # Simulate multiple 429s
        await handler.handle_429('groq', retry_after=0.05)
        await handler.handle_429('groq', retry_after=None)
        await handler.handle_429('groq', retry_after=0.05)
        
        stats = handler.get_stats()
        
        assert stats['total_429s'] == 3
        assert stats['retry_after_present'] == 2
        assert stats['retry_after_present_pct'] == pytest.approx(66.67, rel=0.1)
        assert stats['retry_after_respected'] == 2
        assert stats['total_wait_time'] == pytest.approx(0.1, abs=0.02)
    
    def test_reset_stats(self):
        """Should reset statistics"""
        handler = RetryAfterHandler()
        handler.total_429s = 10
        handler.retry_after_present = 5
        
        handler.reset_stats()
        
        stats = handler.get_stats()
        assert stats['total_429s'] == 0
        assert stats['retry_after_present'] == 0

