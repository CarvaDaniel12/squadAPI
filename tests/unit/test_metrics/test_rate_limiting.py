"""
Unit Tests for Rate Limiting Metrics

Tests Prometheus metrics recording for rate limiting.
Note: These tests verify that metrics functions execute without errors.
Actual prometheus_client integration is tested separately.
"""

import pytest

from src.metrics.rate_limiting import (
    record_request,
    record_429_error,
    record_retry,
    record_tokens,
    update_bucket_tokens,
    update_window_occupancy,
    update_semaphore_stats,
    update_rate_limited_status,
    record_latency,
    record_rate_limit_wait,
    update_rate_limiter_state,
    update_semaphore_state,
    is_metrics_enabled
)


@pytest.mark.unit
class TestMetricsRecording:
    """Test metrics recording functions"""

    def test_record_request(self):
        """Should record request without error"""
        # Should not raise even if prometheus_client not available
        record_request('groq', 'analyst', 'success')

    def test_record_429_error(self):
        """Should record 429 error"""
        record_429_error('groq', 'analyst')

    def test_record_retry(self):
        """Should record retry attempt"""
        record_retry('groq', 'rate_limit')

    def test_record_tokens(self):
        """Should record token usage"""
        record_tokens('groq', input_tokens=100, output_tokens=50)

    def test_update_bucket_tokens(self):
        """Should update bucket tokens gauge"""
        update_bucket_tokens('groq', available=5)

    def test_update_window_occupancy(self):
        """Should update window occupancy gauge"""
        update_window_occupancy('groq', count=10)

    def test_update_semaphore_stats(self):
        """Should update semaphore statistics"""
        update_semaphore_stats(active=3, available=9)

    def test_update_rate_limited_status(self):
        """Should update rate limited status"""
        update_rate_limited_status('groq', is_limited=True)
        update_rate_limited_status('groq', is_limited=False)

    def test_record_latency(self):
        """Should record request latency"""
        record_latency('groq', latency_seconds=1.5)

    def test_record_rate_limit_wait(self):
        """Should record rate limit wait time"""
        record_rate_limit_wait('groq', wait_seconds=5.0)


@pytest.mark.unit
class TestBulkUpdates:
    """Test bulk metric updates"""

    def test_update_rate_limiter_state(self):
        """Should update multiple metrics from state"""
        state = {
            'provider': 'groq',
            'window_count': 10,
            'is_limited': True
        }

        update_rate_limiter_state('groq', state)

    def test_update_semaphore_state(self):
        """Should update semaphore metrics from stats"""
        stats = {
            'active_count': 5,
            'available_slots': 7,
            'total_acquired': 100
        }

        update_semaphore_state(stats)


@pytest.mark.unit
class TestUtility:
    """Test utility functions"""

    def test_is_metrics_enabled(self):
        """Should check if metrics are enabled"""
        # With mocked prometheus_client, should return True
        result = is_metrics_enabled()

        # Result depends on whether prometheus_client is available
        assert isinstance(result, bool)

