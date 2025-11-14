"""
Unit Tests for Auto-Throttler

Tests automatic throttling and restoration logic.
"""

import pytest
import time
from src.rate_limit.auto_throttle import AutoThrottler
from src.models.provider import ProviderRateLimitError


@pytest.mark.unit
class TestAutoThrottler:
    """Test auto-throttling system"""
    
    def test_initialization(self):
        """Should initialize with correct settings"""
        throttler = AutoThrottler(
            spike_threshold=5,
            spike_window_seconds=30,
            throttle_reduction=0.15
        )
        
        assert throttler.spike_threshold == 5
        assert throttler.spike_window == 30
        assert throttler.throttle_reduction == 0.15
    
    def test_initialize_provider(self):
        """Should initialize provider state"""
        throttler = AutoThrottler()
        
        throttler.initialize_provider("groq", original_rpm=30)
        
        assert "groq" in throttler.states
        assert throttler.states["groq"].original_rpm == 30
        assert throttler.states["groq"].current_rpm == 30
        assert throttler.states["groq"].throttle_factor == 1.0
        assert throttler.states["groq"].is_throttled is False
    
    def test_record_error_below_threshold(self):
        """Should record errors but not throttle below threshold"""
        throttler = AutoThrottler(spike_threshold=3)
        throttler.initialize_provider("groq", original_rpm=30)
        
        # Record 2 errors (below threshold of 3)
        for _ in range(2):
            throttler.record_error("groq", ProviderRateLimitError("groq", "429"))
        
        # Should not be throttled yet
        assert throttler.is_throttled("groq") is False
        assert throttler.get_current_rpm("groq") == 30
    
    def test_record_error_triggers_throttle(self):
        """Should throttle when spike threshold reached"""
        throttler = AutoThrottler(
            spike_threshold=3,
            throttle_reduction=0.20  # 20% reduction
        )
        throttler.initialize_provider("groq", original_rpm=30)
        
        # Record 3 errors (meets threshold)
        for _ in range(3):
            throttler.record_error("groq", ProviderRateLimitError("groq", "429"))
        
        # Should be throttled
        assert throttler.is_throttled("groq") is True
        assert throttler.get_current_rpm("groq") == 24  # 30 * 0.8
        
        stats = throttler.get_stats()
        assert stats['total_throttles'] == 1
    
    def test_throttle_multiple_times(self):
        """Should throttle multiple times (cascading)"""
        throttler = AutoThrottler(spike_threshold=2, throttle_reduction=0.20)
        throttler.initialize_provider("groq", original_rpm=100)
        
        # First spike
        for _ in range(2):
            throttler.record_error("groq", ProviderRateLimitError("groq", "429"))
        
        assert throttler.get_current_rpm("groq") == 80  # 100 * 0.8
        
        # Clear history to allow second throttle
        time.sleep(0.1)
        throttler.states["groq"].last_spike_time = time.time() - 40
        
        # Second spike
        for _ in range(2):
            throttler.record_error("groq", ProviderRateLimitError("groq", "429"))
        
        # Should be throttled again
        assert throttler.get_current_rpm("groq") == 64  # 80 * 0.8
    
    def test_throttle_floor(self):
        """Should not throttle below 20% of original"""
        throttler = AutoThrottler(spike_threshold=1, throttle_reduction=0.50)
        throttler.initialize_provider("groq", original_rpm=100)
        
        # Throttle many times
        for i in range(10):
            throttler.states["groq"].last_spike_time = time.time() - 40
            throttler.record_error("groq", ProviderRateLimitError("groq", "429"))
        
        # Should not go below 20%
        current_rpm = throttler.get_current_rpm("groq")
        assert current_rpm >= 20  # 20% of 100
    
    def test_check_restore_not_stable(self):
        """Should not restore if not stable"""
        throttler = AutoThrottler(stable_duration_minutes=5)
        throttler.initialize_provider("groq", original_rpm=30)
        
        # Throttle
        for _ in range(3):
            throttler.record_error("groq", ProviderRateLimitError("groq", "429"))
        
        assert throttler.is_throttled("groq") is True
        
        # Try to restore immediately (not stable)
        restored = throttler.check_restore("groq")
        
        assert restored is False  # Too soon
    
    def test_check_restore_after_stable(self):
        """Should restore after stable period"""
        throttler = AutoThrottler(
            stable_duration_minutes=2,
            restore_increment=0.10
        )
        throttler.initialize_provider("groq", original_rpm=30)
        
        # Throttle
        for _ in range(3):
            throttler.record_error("groq", ProviderRateLimitError("groq", "429"))
        
        throttled_rpm = throttler.get_current_rpm("groq")
        assert throttled_rpm == 24  # 30 * 0.8
        
        # Simulate stable period (2 calls = 2 stable minutes)
        # Each call increments consecutive_stable_minutes
        restored_count = 0
        for i in range(2):
            was_restored = throttler.check_restore("groq")
            if was_restored:
                restored_count += 1
        
        # Should restore after reaching stable_duration (2 minutes)
        assert restored_count >= 1
        
        # Should have increased RPM
        current_rpm = throttler.get_current_rpm("groq")
        # After restore: 24 * 1.1 = 26.4  26
        assert current_rpm >= 26
    
    def test_restore_caps_at_original(self):
        """Should not restore above original RPM"""
        throttler = AutoThrottler(
            stable_duration_minutes=1,
            restore_increment=0.50  # Large increment
        )
        throttler.initialize_provider("groq", original_rpm=30)
        
        # Throttle slightly
        throttler.states["groq"].current_rpm = 28
        throttler.states["groq"].throttle_factor = 0.93
        throttler.states["groq"].is_throttled = True
        
        # Restore
        for _ in range(5):
            throttler.check_restore("groq")
        
        # Should cap at original
        assert throttler.get_current_rpm("groq") <= 30
        assert throttler.is_throttled("groq") is False
    
    def test_get_stats(self):
        """Should return comprehensive statistics"""
        throttler = AutoThrottler()
        throttler.initialize_provider("groq", original_rpm=30)
        throttler.initialize_provider("cerebras", original_rpm=60)
        
        # Throttle groq
        for _ in range(3):
            throttler.record_error("groq", ProviderRateLimitError("groq", "429"))
        
        stats = throttler.get_stats()
        
        assert stats['total_spikes'] == 1
        assert stats['total_throttles'] == 1
        assert 'throttled_providers' in stats
        assert 'groq' in stats['throttled_providers']
        assert 'provider_states' in stats


