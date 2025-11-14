"""
Unit Tests for Request Tracking Metrics

Tests Prometheus request metrics recording.
"""

import pytest
from src.metrics.requests import (
    record_request,
    record_success,
    record_failure,
    record_429,
    record_fallback,
    is_metrics_enabled,
    get_request_stats
)


@pytest.mark.unit
class TestRequestMetrics:
    """Test request tracking metrics"""
    
    def test_record_request(self):
        """Should record request without error"""
        record_request('groq', 'analyst', 'success')
    
    def test_record_success(self):
        """Should record successful request"""
        record_success('groq', 'analyst')
    
    def test_record_failure(self):
        """Should record failed request"""
        record_failure('groq', 'analyst', 'timeout')
    
    def test_record_429(self):
        """Should record 429 error"""
        record_429('groq')
    
    def test_record_fallback(self):
        """Should record fallback usage"""
        record_fallback('analyst', 'groq', 'cerebras')
    
    def test_is_metrics_enabled(self):
        """Should check if metrics are enabled"""
        result = is_metrics_enabled()
        assert isinstance(result, bool)
    
    def test_get_request_stats(self):
        """Should return stats dict"""
        stats = get_request_stats()
        
        assert isinstance(stats, dict)
        assert 'metrics_enabled' in stats
        assert 'counters' in stats


@pytest.mark.unit
class TestRequestMetricsLabels:
    """Test metric label combinations"""
    
    def test_multiple_providers(self):
        """Should handle multiple providers"""
        record_success('groq', 'analyst')
        record_success('cerebras', 'analyst')
        record_success('gemini', 'analyst')
    
    def test_multiple_agents(self):
        """Should handle multiple agents"""
        record_success('groq', 'analyst')
        record_success('groq', 'dev')
        record_success('groq', 'architect')
    
    def test_different_statuses(self):
        """Should handle different status values"""
        record_request('groq', 'analyst', 'success')
        record_request('groq', 'analyst', 'failure')
        record_request('groq', 'analyst', 'timeout')
    
    def test_different_error_types(self):
        """Should handle different error types"""
        record_failure('groq', 'analyst', 'rate_limit')
        record_failure('groq', 'analyst', 'timeout')
        record_failure('groq', 'analyst', 'api_error')
        record_failure('groq', 'analyst', 'unknown')


@pytest.mark.unit
class TestRequestMetricsConcurrency:
    """Test concurrent metric recording"""
    
    def test_concurrent_recording(self):
        """Should handle concurrent metric updates"""
        import concurrent.futures
        
        def record_many():
            for i in range(10):
                record_success('groq', 'analyst')
        
        # Simulate concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(record_many) for _ in range(5)]
            concurrent.futures.wait(futures)
        
        # Should not raise any errors
        assert True




