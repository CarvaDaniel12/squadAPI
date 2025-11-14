"""
Retry Logic with Exponential Backoff

Implements retry strategies for LLM API calls using tenacity.
Handles transient errors, rate limits, and network issues.
"""

import asyncio
import logging
import random
from typing import Optional, Callable, Any, TypeVar

try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
        before_sleep_log,
        RetryCallState
    )
except ImportError:
    retry = None
    stop_after_attempt = None
    wait_exponential = None
    retry_if_exception_type = None
    before_sleep_log = None
    RetryCallState = None

from ..config.rate_limits import get_rate_limit_config


logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryableError(Exception):
    """Base class for errors that should trigger a retry"""
    pass


class NetworkError(RetryableError):
    """Network-related errors"""
    pass


class ServiceUnavailableError(RetryableError):
    """Service temporarily unavailable (500, 502, 503, 504)"""
    pass


class RateLimitExceededError(RetryableError):
    """Rate limit exceeded (429)"""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


def create_retry_decorator(
    max_attempts: Optional[int] = None,
    exponential_base: Optional[int] = None,
    base_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    jitter: Optional[float] = None
):
    """
    Create a retry decorator with custom configuration
    
    Args:
        max_attempts: Maximum retry attempts (default: from config)
        exponential_base: Exponential backoff base (default: from config)
        base_delay: Base delay in seconds (default: from config)
        max_delay: Maximum delay in seconds (default: from config)
        jitter: Jitter factor (%) (default: from config)
        
    Returns:
        Tenacity retry decorator
    """
    if retry is None:
        raise ImportError("tenacity is required. Install: pip install tenacity")
    
    # Load defaults from config
    config_loader = get_rate_limit_config()
    retry_config = config_loader.get_retry_config()
    
    max_attempts = max_attempts or retry_config.max_attempts
    exponential_base = exponential_base or retry_config.exponential_base
    base_delay = base_delay or retry_config.base_delay
    max_delay = max_delay or retry_config.max_delay
    jitter_factor = jitter or retry_config.jitter
    
    # Custom wait function with jitter
    def wait_with_jitter(retry_state: RetryCallState) -> float:
        """Calculate wait time with exponential backoff and jitter"""
        attempt_number = retry_state.attempt_number
        
        # Exponential backoff: base_delay * (exponential_base ^ attempt)
        wait_time = base_delay * (exponential_base ** (attempt_number - 1))
        
        # Cap at max_delay
        wait_time = min(wait_time, max_delay)
        
        # Add jitter (jitter_factor%)
        jitter_amount = wait_time * jitter_factor * random.uniform(-1, 1)
        wait_time += jitter_amount
        
        # Ensure non-negative
        wait_time = max(0.0, wait_time)
        
        return wait_time
    
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_with_jitter,
        retry=retry_if_exception_type(RetryableError),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )


async def call_with_retry(
    func: Callable[..., T],
    *args,
    max_attempts: Optional[int] = None,
    **kwargs
) -> T:
    """
    Call an async function with retry logic
    
    Usage:
        result = await call_with_retry(provider.call, system_prompt, user_prompt)
    
    Args:
        func: Async function to call
        *args: Positional arguments for func
        max_attempts: Maximum retry attempts (optional)
        **kwargs: Keyword arguments for func
        
    Returns:
        Result of func call
        
    Raises:
        RetryableError: If all retries exhausted
    """
    retry_decorator = create_retry_decorator(max_attempts=max_attempts)
    
    @retry_decorator
    async def _retry_wrapper():
        return await func(*args, **kwargs)
    
    return await _retry_wrapper()


def should_retry_status_code(status_code: int) -> bool:
    """
    Check if HTTP status code should trigger a retry
    
    Args:
        status_code: HTTP status code
        
    Returns:
        True if should retry, False otherwise
    """
    config_loader = get_rate_limit_config()
    retry_config = config_loader.get_retry_config()
    
    return status_code in retry_config.retryable_status_codes


def classify_error(exception: Exception, status_code: Optional[int] = None) -> Optional[RetryableError]:
    """
    Classify an exception as retryable or not
    
    Args:
        exception: The exception to classify
        status_code: HTTP status code (if applicable)
        
    Returns:
        RetryableError subclass if retryable, None otherwise
    """
    # Already a RetryableError
    if isinstance(exception, RetryableError):
        return exception
    
    # Check status code
    if status_code:
        if status_code == 429:
            return RateLimitExceededError(str(exception))
        elif status_code in [500, 502, 503, 504]:
            return ServiceUnavailableError(str(exception))
    
    # Check exception type
    exception_name = exception.__class__.__name__.lower()
    
    # Network errors
    if any(keyword in exception_name for keyword in ['timeout', 'connection', 'network']):
        return NetworkError(str(exception))
    
    # Not retryable
    return None


class RetryContext:
    """Context manager for retry operations with statistics"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.attempts = 0
        self.total_retry_time = 0.0
        self.last_error: Optional[Exception] = None
    
    async def __aenter__(self):
        self.attempts = 0
        self.total_retry_time = 0.0
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(
                f"Retry context '{self.operation_name}' failed after {self.attempts} attempts: {exc_val}"
            )
        else:
            logger.debug(
                f"Retry context '{self.operation_name}' succeeded after {self.attempts} attempts"
            )
        return False
    
    def record_attempt(self, error: Optional[Exception] = None):
        """Record a retry attempt"""
        self.attempts += 1
        if error:
            self.last_error = error


