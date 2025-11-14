"""
Global Semaphore

Limits total concurrent requests across all providers.
Prevents overwhelming network, Redis, or system resources.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional


logger = logging.getLogger(__name__)


class GlobalSemaphore:
    """
    Global semaphore to limit concurrent LLM requests

    Enforces system-wide concurrency limit (e.g., max 12 concurrent requests)
    regardless of provider. This prevents resource exhaustion.
    """

    def __init__(self, max_concurrent: int = 12):
        """
        Initialize global semaphore

        Args:
            max_concurrent: Maximum concurrent requests allowed (default: 12)
        """
        if max_concurrent < 1:
            raise ValueError("max_concurrent must be >= 1")

        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._active_count = 0
        self._total_acquired = 0
        self._total_queued = 0

        logger.info(f"Global semaphore initialized: max_concurrent={max_concurrent}")

    @asynccontextmanager
    async def acquire(self):
        """
        Acquire semaphore slot (context manager)

        Usage:
            async with global_semaphore.acquire():
                # Execute LLM call here
                response = await provider.call(...)

        Yields:
            None (context manager)
        """
        # Check if we'll need to wait
        if self.semaphore.locked():
            self._total_queued += 1
            logger.debug(f"Request queued, {self._active_count}/{self.max_concurrent} slots in use")

        # Acquire semaphore (will block if at capacity)
        async with self.semaphore:
            self._active_count += 1
            self._total_acquired += 1

            logger.debug(
                f"Semaphore acquired: {self._active_count}/{self.max_concurrent} active"
            )

            try:
                yield
            finally:
                self._active_count -= 1
                logger.debug(
                    f"Semaphore released: {self._active_count}/{self.max_concurrent} active"
                )

    def get_active_count(self) -> int:
        """Get number of currently active requests"""
        return self._active_count

    def get_available_slots(self) -> int:
        """Get number of available semaphore slots"""
        return self.max_concurrent - self._active_count

    def get_capacity(self) -> int:
        """Get maximum concurrent capacity"""
        return self.max_concurrent

    def is_at_capacity(self) -> bool:
        """Check if semaphore is at capacity"""
        return self._active_count >= self.max_concurrent

    def get_stats(self) -> dict:
        """
        Get semaphore statistics

        Returns:
            Dict with stats (active, available, total_acquired, total_queued)
        """
        return {
            'max_concurrent': self.max_concurrent,
            'active_count': self._active_count,
            'available_slots': self.get_available_slots(),
            'total_acquired': self._total_acquired,
            'total_queued': self._total_queued,
            'is_at_capacity': self.is_at_capacity()
        }

    def reset_stats(self):
        """Reset statistics counters (for testing)"""
        self._total_acquired = 0
        self._total_queued = 0
        logger.info("Global semaphore stats reset")

    async def wait_for_capacity(self, timeout: Optional[float] = None) -> bool:
        """
        Wait until there's available capacity

        Args:
            timeout: Maximum time to wait in seconds (None = wait forever)

        Returns:
            True if capacity available, False if timeout
        """
        try:
            async with asyncio.timeout(timeout) if timeout else asyncio.nullcontext():
                # Try to acquire and immediately release
                async with self.semaphore:
                    pass
                return True
        except asyncio.TimeoutError:
            return False


# Global singleton instance
_global_semaphore: Optional[GlobalSemaphore] = None


def get_global_semaphore(max_concurrent: int = 12) -> GlobalSemaphore:
    """
    Get or create global semaphore singleton

    Args:
        max_concurrent: Maximum concurrent requests (only used on first call)

    Returns:
        GlobalSemaphore instance
    """
    global _global_semaphore

    if _global_semaphore is None:
        _global_semaphore = GlobalSemaphore(max_concurrent)

    return _global_semaphore

