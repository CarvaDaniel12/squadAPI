"""
Unit Tests for Retry Logic

Tests exponential backoff and retry strategies.
"""

import pytest
import asyncio
import time
from src.providers.retry import (
    create_retry_decorator,
    call_with_retry,
    should_retry_status_code,
    classify_error,
    RetryableError,
    NetworkError,
    ServiceUnavailableError,
    RateLimitExceededError,
    RetryContext
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestRetryDecorator:
    """Test retry decorator"""
    
    async def test_success_no_retry(self):
        """Should succeed without retry"""
        call_count = 0
        
        @create_retry_decorator(max_attempts=3)
        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await successful_func()
        
        assert result == "success"
        assert call_count == 1  # Only called once
    
    async def test_retry_on_retryable_error(self):
        """Should retry on RetryableError"""
        call_count = 0
        
        @create_retry_decorator(max_attempts=3, base_delay=0.01, max_delay=0.1)
        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RetryableError("Temporary failure")
            return "success"
        
        result = await failing_func()
        
        assert result == "success"
        assert call_count == 3  # Retried 2 times, succeeded on 3rd
    
    async def test_max_attempts_exhausted(self):
        """Should raise after max attempts"""
        call_count = 0
        
        @create_retry_decorator(max_attempts=3, base_delay=0.01, max_delay=0.1)
        async def always_failing():
            nonlocal call_count
            call_count += 1
            raise RetryableError("Always fails")
        
        with pytest.raises(RetryableError):
            await always_failing()
        
        assert call_count == 3  # Tried 3 times
    
    async def test_exponential_backoff(self):
        """Should use exponential backoff"""
        call_times = []
        
        @create_retry_decorator(
            max_attempts=4,
            base_delay=0.1,
            exponential_base=2,
            max_delay=1.0,
            jitter=0.0  # No jitter for predictability
        )
        async def failing_func():
            call_times.append(time.time())
            raise RetryableError("Fail")
        
        start = time.time()
        try:
            await failing_func()
        except RetryableError:
            pass
        
        # Calculate delays between calls
        delays = [call_times[i+1] - call_times[i] for i in range(len(call_times)-1)]
        
        # Expected delays: 0.1, 0.2, 0.4 (exponential backoff)
        # Allow 50% tolerance for timing variations
        assert 0.05 < delays[0] < 0.15  # ~0.1s
        assert 0.15 < delays[1] < 0.25  # ~0.2s
        assert 0.3 < delays[2] < 0.5   # ~0.4s
    
    async def test_max_delay_cap(self):
        """Should cap delay at max_delay"""
        call_times = []
        
        @create_retry_decorator(
            max_attempts=5,
            base_delay=1.0,
            exponential_base=10,  # Very aggressive
            max_delay=0.2,  # But capped at 0.2s
            jitter=0.0
        )
        async def failing_func():
            call_times.append(time.time())
            raise RetryableError("Fail")
        
        try:
            await failing_func()
        except RetryableError:
            pass
        
        # All delays should be capped at 0.2s
        delays = [call_times[i+1] - call_times[i] for i in range(len(call_times)-1)]
        
        for delay in delays:
            assert delay < 0.3  # Should be ~0.2s (with tolerance)
    
    async def test_non_retryable_error(self):
        """Should not retry non-RetryableError"""
        call_count = 0
        
        @create_retry_decorator(max_attempts=3)
        async def non_retryable():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not retryable")
        
        with pytest.raises(ValueError):
            await non_retryable()
        
        assert call_count == 1  # Only called once, no retries


@pytest.mark.unit
@pytest.mark.asyncio
class TestCallWithRetry:
    """Test call_with_retry helper"""
    
    async def test_call_with_retry_success(self):
        """Should call function successfully"""
        async def my_func(x, y):
            return x + y
        
        result = await call_with_retry(my_func, 2, 3)
        
        assert result == 5
    
    async def test_call_with_retry_with_retries(self):
        """Should retry failed calls"""
        call_count = 0
        
        async def flaky_func(value):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RetryableError("Temporary")
            return value * 2
        
        result = await call_with_retry(flaky_func, 5, max_attempts=3)
        
        assert result == 10
        assert call_count == 2


@pytest.mark.unit
class TestShouldRetryStatusCode:
    """Test status code retry logic"""
    
    def test_retry_429(self):
        """Should retry 429 (rate limit)"""
        assert should_retry_status_code(429) is True
    
    def test_retry_5xx(self):
        """Should retry 5xx errors"""
        assert should_retry_status_code(500) is True
        assert should_retry_status_code(502) is True
        assert should_retry_status_code(503) is True
        assert should_retry_status_code(504) is True
    
    def test_no_retry_4xx(self):
        """Should not retry most 4xx errors"""
        assert should_retry_status_code(400) is False
        assert should_retry_status_code(401) is False
        assert should_retry_status_code(403) is False
        assert should_retry_status_code(404) is False
    
    def test_no_retry_2xx(self):
        """Should not retry 2xx success"""
        assert should_retry_status_code(200) is False
        assert should_retry_status_code(201) is False


@pytest.mark.unit
class TestClassifyError:
    """Test error classification"""
    
    def test_classify_rate_limit(self):
        """Should classify 429 as RateLimitExceededError"""
        error = classify_error(Exception("Too many requests"), status_code=429)
        
        assert isinstance(error, RateLimitExceededError)
    
    def test_classify_service_unavailable(self):
        """Should classify 5xx as ServiceUnavailableError"""
        error = classify_error(Exception("Server error"), status_code=503)
        
        assert isinstance(error, ServiceUnavailableError)
    
    def test_classify_network_error(self):
        """Should classify network errors"""
        timeout_error = TimeoutError("Connection timeout")
        error = classify_error(timeout_error)
        
        assert isinstance(error, NetworkError)
    
    def test_classify_already_retryable(self):
        """Should return already RetryableError as-is"""
        original = RetryableError("Already retryable")
        error = classify_error(original)
        
        assert error is original
    
    def test_classify_non_retryable(self):
        """Should return None for non-retryable errors"""
        error = classify_error(ValueError("Bad input"))
        
        assert error is None


@pytest.mark.unit
@pytest.mark.asyncio
class TestRetryContext:
    """Test retry context manager"""
    
    async def test_context_success(self):
        """Should track successful operation"""
        async with RetryContext("test_op") as ctx:
            ctx.record_attempt()
            # Success
        
        assert ctx.attempts == 1
        assert ctx.last_error is None
    
    async def test_context_with_retries(self):
        """Should track multiple attempts"""
        async with RetryContext("test_op") as ctx:
            ctx.record_attempt(error=RetryableError("Attempt 1"))
            ctx.record_attempt(error=RetryableError("Attempt 2"))
            ctx.record_attempt()  # Success
        
        assert ctx.attempts == 3
        assert isinstance(ctx.last_error, RetryableError)

