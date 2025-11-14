"""
Retry-After Header Support

Handles HTTP 429 responses with Retry-After header.
Respects API guidance instead of using exponential backoff.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable, TypeVar
from datetime import datetime, timezone

from .retry import RateLimitExceededError, call_with_retry


logger = logging.getLogger(__name__)

T = TypeVar('T')


def parse_retry_after(retry_after_header: Optional[str]) -> Optional[float]:
    """
    Parse Retry-After header value
    
    Supports two formats:
    1. Delay-seconds: "30" (wait 30 seconds)
    2. HTTP-date: "Wed, 21 Oct 2015 07:28:00 GMT" (wait until this time)
    
    Args:
        retry_after_header: Value of Retry-After header
        
    Returns:
        Wait time in seconds, or None if header invalid/missing
    """
    if not retry_after_header:
        return None
    
    # Try parsing as delay-seconds (integer)
    try:
        delay = int(retry_after_header)
        if delay > 0:
            logger.debug(f"Retry-After: {delay} seconds (delay format)")
            return float(delay)
    except ValueError:
        pass
    
    # Try parsing as HTTP-date
    try:
        # Parse HTTP-date format: "Wed, 21 Oct 2015 07:28:00 GMT"
        target_time = datetime.strptime(
            retry_after_header,
            "%a, %d %b %Y %H:%M:%S GMT"
        ).replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        delay = (target_time - now).total_seconds()
        
        if delay > 0:
            logger.debug(f"Retry-After: {delay:.1f} seconds (HTTP-date format)")
            return delay
    except ValueError:
        pass
    
    # Could not parse
    logger.warning(f"Invalid Retry-After header format: {retry_after_header}")
    return None


async def wait_for_retry_after(retry_after: float, max_wait: float = 300.0) -> bool:
    """
    Wait for Retry-After duration (with safety cap)
    
    Args:
        retry_after: Wait time in seconds from Retry-After header
        max_wait: Maximum time to wait (default: 300s = 5 minutes)
        
    Returns:
        True if waited successfully, False if wait time exceeded max_wait
    """
    if retry_after > max_wait:
        logger.warning(
            f"Retry-After={retry_after}s exceeds max_wait={max_wait}s, not waiting"
        )
        return False
    
    logger.info(f"Waiting {retry_after:.1f}s as instructed by Retry-After header")
    await asyncio.sleep(retry_after)
    return True


async def call_with_retry_after(
    func: Callable[..., T],
    *args,
    max_wait: float = 300.0,
    fallback_to_exponential: bool = True,
    **kwargs
) -> T:
    """
    Call function with Retry-After header support
    
    If function raises RateLimitExceededError with retry_after value:
    1. Wait for specified duration (up to max_wait)
    2. Retry the call
    3. If no retry_after, fall back to exponential backoff (if enabled)
    
    Usage:
        result = await call_with_retry_after(
            provider.call,
            system_prompt=prompt,
            user_prompt=query
        )
    
    Args:
        func: Async function to call
        *args: Positional arguments for func
        max_wait: Maximum time to wait for Retry-After (default: 300s)
        fallback_to_exponential: Use exponential backoff if no Retry-After (default: True)
        **kwargs: Keyword arguments for func
        
    Returns:
        Result of func call
        
    Raises:
        RateLimitExceededError: If retry unsuccessful
    """
    attempt = 0
    max_attempts = 3
    
    while attempt < max_attempts:
        attempt += 1
        
        try:
            return await func(*args, **kwargs)
            
        except RateLimitExceededError as e:
            logger.warning(f"Rate limit exceeded (attempt {attempt}/{max_attempts}): {e}")
            
            # Check for Retry-After
            if e.retry_after is not None:
                logger.info(f"Retry-After header present: {e.retry_after}s")
                
                # Wait for Retry-After duration
                if await wait_for_retry_after(e.retry_after, max_wait=max_wait):
                    logger.info(f"Retrying after {e.retry_after}s delay...")
                    continue
                else:
                    # Retry-After too long, give up
                    logger.error(f"Retry-After={e.retry_after}s exceeds max_wait, giving up")
                    raise
            
            elif fallback_to_exponential and attempt < max_attempts:
                # No Retry-After, use exponential backoff
                logger.info("No Retry-After header, falling back to exponential backoff")
                return await call_with_retry(func, *args, max_attempts=max_attempts-attempt+1, **kwargs)
            
            else:
                # No retry strategy available
                logger.error("No Retry-After header and exponential backoff disabled, giving up")
                raise
    
    # All attempts exhausted
    raise RateLimitExceededError(
        f"Failed after {max_attempts} attempts with Retry-After handling"
    )


def extract_retry_after_from_response(
    response: Any,
    headers: Optional[Dict[str, str]] = None
) -> Optional[float]:
    """
    Extract Retry-After value from HTTP response
    
    Supports multiple response types (httpx, aiohttp, etc.)
    
    Args:
        response: HTTP response object
        headers: Optional dict of headers (if response doesn't have .headers)
        
    Returns:
        Wait time in seconds, or None if not found
    """
    # Try to get headers from response
    if headers is None:
        if hasattr(response, 'headers'):
            headers = response.headers
        elif hasattr(response, 'getheaders'):
            # Old-style response
            headers = dict(response.getheaders())
        else:
            logger.warning("Could not extract headers from response")
            return None
    
    # Look for Retry-After header (case-insensitive)
    for key, value in headers.items():
        if key.lower() == 'retry-after':
            return parse_retry_after(value)
    
    return None


class RetryAfterHandler:
    """
    Handler for Retry-After responses with statistics
    
    Tracks Retry-After usage and provides insights.
    """
    
    def __init__(self):
        self.total_429s = 0
        self.retry_after_present = 0
        self.retry_after_respected = 0
        self.retry_after_exceeded = 0
        self.total_wait_time = 0.0
    
    async def handle_429(
        self,
        provider: str,
        retry_after: Optional[float],
        max_wait: float = 300.0
    ) -> bool:
        """
        Handle a 429 response
        
        Args:
            provider: Provider name (for logging)
            retry_after: Retry-After value in seconds (if present)
            max_wait: Maximum allowed wait time
            
        Returns:
            True if should retry, False if should give up
        """
        self.total_429s += 1
        
        if retry_after is None:
            logger.warning(f"429 from {provider} without Retry-After header")
            return True  # Fall back to exponential backoff
        
        self.retry_after_present += 1
        
        if retry_after > max_wait:
            logger.warning(
                f"429 from {provider}, Retry-After={retry_after}s exceeds max_wait={max_wait}s"
            )
            self.retry_after_exceeded += 1
            return False
        
        # Respect Retry-After
        logger.info(f"429 from {provider}, respecting Retry-After={retry_after}s")
        await wait_for_retry_after(retry_after, max_wait=max_wait)
        
        self.retry_after_respected += 1
        self.total_wait_time += retry_after
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Retry-After handling statistics"""
        return {
            'total_429s': self.total_429s,
            'retry_after_present': self.retry_after_present,
            'retry_after_present_pct': (
                100 * self.retry_after_present / self.total_429s
                if self.total_429s > 0 else 0
            ),
            'retry_after_respected': self.retry_after_respected,
            'retry_after_exceeded': self.retry_after_exceeded,
            'total_wait_time': self.total_wait_time,
            'avg_wait_time': (
                self.total_wait_time / self.retry_after_respected
                if self.retry_after_respected > 0 else 0
            )
        }
    
    def reset_stats(self):
        """Reset statistics (for testing)"""
        self.total_429s = 0
        self.retry_after_present = 0
        self.retry_after_respected = 0
        self.retry_after_exceeded = 0
        self.total_wait_time = 0.0

