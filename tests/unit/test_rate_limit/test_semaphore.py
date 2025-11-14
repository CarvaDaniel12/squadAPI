"""
Unit Tests for Global Semaphore

Tests global concurrency limiting.
"""

import pytest
import asyncio
import time
from src.rate_limit.semaphore import GlobalSemaphore, get_global_semaphore


@pytest.mark.unit
@pytest.mark.asyncio
class TestGlobalSemaphore:
    """Test global semaphore"""
    
    async def test_init(self):
        """Should initialize with correct capacity"""
        semaphore = GlobalSemaphore(max_concurrent=10)
        
        assert semaphore.max_concurrent == 10
        assert semaphore.get_active_count() == 0
        assert semaphore.get_available_slots() == 10
    
    async def test_init_invalid_capacity(self):
        """Should raise error for invalid capacity"""
        with pytest.raises(ValueError, match="must be >= 1"):
            GlobalSemaphore(max_concurrent=0)
    
    async def test_acquire_single(self):
        """Should acquire and release single slot"""
        semaphore = GlobalSemaphore(max_concurrent=5)
        
        async with semaphore.acquire():
            assert semaphore.get_active_count() == 1
            assert semaphore.get_available_slots() == 4
        
        # After release
        assert semaphore.get_active_count() == 0
        assert semaphore.get_available_slots() == 5
    
    async def test_acquire_multiple_sequential(self):
        """Should handle sequential acquisitions"""
        semaphore = GlobalSemaphore(max_concurrent=5)
        
        for i in range(3):
            async with semaphore.acquire():
                assert semaphore.get_active_count() == 1
        
        # All released
        assert semaphore.get_active_count() == 0
    
    async def test_concurrent_within_limit(self):
        """Should allow concurrent requests within limit"""
        semaphore = GlobalSemaphore(max_concurrent=5)
        
        async def task():
            async with semaphore.acquire():
                await asyncio.sleep(0.1)
                return semaphore.get_active_count()
        
        # Start 5 concurrent tasks (at limit)
        results = await asyncio.gather(*[task() for _ in range(5)])
        
        # All should have seen active count of 5
        assert max(results) == 5
        
        # After completion, all released
        assert semaphore.get_active_count() == 0
    
    async def test_concurrent_exceeds_limit_queues(self):
        """Should queue requests when limit exceeded"""
        semaphore = GlobalSemaphore(max_concurrent=3)
        
        start_times = []
        
        async def task():
            start = time.time()
            async with semaphore.acquire():
                start_times.append(time.time() - start)
                await asyncio.sleep(0.1)
        
        # Start 6 concurrent tasks (double the limit)
        await asyncio.gather(*[task() for _ in range(6)])
        
        # First 3 should start immediately (< 0.01s)
        # Next 3 should wait (~0.1s)
        immediate = [t for t in start_times if t < 0.05]
        delayed = [t for t in start_times if t >= 0.05]
        
        assert len(immediate) == 3
        assert len(delayed) == 3
    
    async def test_is_at_capacity(self):
        """Should correctly report capacity status"""
        semaphore = GlobalSemaphore(max_concurrent=2)
        
        assert semaphore.is_at_capacity() is False
        
        # Acquire 1 slot
        async with semaphore.acquire():
            assert semaphore.is_at_capacity() is False
            
            # Acquire 2nd slot (now at capacity)
            async with semaphore.acquire():
                assert semaphore.is_at_capacity() is True
        
        # Released
        assert semaphore.is_at_capacity() is False
    
    async def test_get_stats(self):
        """Should return accurate statistics"""
        semaphore = GlobalSemaphore(max_concurrent=5)
        
        # Initial stats
        stats = semaphore.get_stats()
        assert stats['max_concurrent'] == 5
        assert stats['active_count'] == 0
        assert stats['available_slots'] == 5
        assert stats['total_acquired'] == 0
        assert stats['is_at_capacity'] is False
        
        # Acquire 2 slots
        async with semaphore.acquire():
            async with semaphore.acquire():
                stats = semaphore.get_stats()
                assert stats['active_count'] == 2
                assert stats['available_slots'] == 3
                assert stats['total_acquired'] == 2
    
    async def test_reset_stats(self):
        """Should reset statistics counters"""
        semaphore = GlobalSemaphore(max_concurrent=5)
        
        # Make some acquisitions
        for _ in range(3):
            async with semaphore.acquire():
                pass
        
        stats_before = semaphore.get_stats()
        assert stats_before['total_acquired'] == 3
        
        # Reset
        semaphore.reset_stats()
        
        stats_after = semaphore.get_stats()
        assert stats_after['total_acquired'] == 0
        assert stats_after['active_count'] == 0  # Still accurate
    
    async def test_wait_for_capacity_immediate(self):
        """Should return immediately when capacity available"""
        semaphore = GlobalSemaphore(max_concurrent=5)
        
        result = await semaphore.wait_for_capacity(timeout=1.0)
        
        assert result is True
    
    async def test_wait_for_capacity_timeout(self):
        """Should timeout if capacity not available"""
        semaphore = GlobalSemaphore(max_concurrent=1)
        
        async def hold_slot():
            async with semaphore.acquire():
                await asyncio.sleep(2.0)  # Hold for 2 seconds
        
        # Start task to hold slot
        holder_task = asyncio.create_task(hold_slot())
        
        # Wait a bit for holder to acquire
        await asyncio.sleep(0.1)
        
        # Try to wait for capacity with short timeout
        result = await semaphore.wait_for_capacity(timeout=0.2)
        
        assert result is False
        
        # Cleanup
        await holder_task


@pytest.mark.unit
@pytest.mark.asyncio
class TestGlobalSemaphoreFairness:
    """Test FIFO fairness of semaphore"""
    
    async def test_fifo_order(self):
        """Should process requests in FIFO order"""
        semaphore = GlobalSemaphore(max_concurrent=1)
        
        execution_order = []
        
        async def task(task_id):
            async with semaphore.acquire():
                execution_order.append(task_id)
                await asyncio.sleep(0.05)
        
        # Start 5 tasks
        await asyncio.gather(*[task(i) for i in range(5)])
        
        # Should execute in order (FIFO)
        assert execution_order == [0, 1, 2, 3, 4]


@pytest.mark.unit
def test_get_global_semaphore_singleton():
    """Should return same instance (singleton pattern)"""
    sem1 = get_global_semaphore(max_concurrent=10)
    sem2 = get_global_semaphore(max_concurrent=20)  # Different value ignored
    
    assert sem1 is sem2
    assert sem1.max_concurrent == 10  # First value used

