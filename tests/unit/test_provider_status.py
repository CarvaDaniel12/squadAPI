"""Unit tests for provider status tracking."""

import pytest
from datetime import datetime, timezone, timedelta
from src.metrics.provider_status import (
    ProviderMetrics,
    ProviderStatusTracker,
    ProviderStatusEnum,
    ProviderStatus,
    ProviderStatusResponse
)


@pytest.fixture
def tracker():
    """Create a tracker instance."""
    return ProviderStatusTracker()


class TestProviderMetrics:
    """Tests for ProviderMetrics dataclass."""

    def test_provider_metrics_calculation_failure_rate(self):
        """Test failure rate calculation."""
        metrics = ProviderMetrics()
        metrics.total_requests = 100
        metrics.total_failures = 5

        assert metrics.failure_rate == 0.05

    def test_provider_metrics_calculation_failure_rate_no_requests(self):
        """Test failure rate when no requests made."""
        metrics = ProviderMetrics()
        assert metrics.failure_rate == 0.0

    def test_provider_metrics_calculation_avg_latency(self):
        """Test average latency calculation."""
        metrics = ProviderMetrics()
        metrics.latencies.extend([100, 200, 300])

        assert metrics.avg_latency_ms == 200

    def test_provider_metrics_calculation_avg_latency_empty(self):
        """Test average latency when no latencies recorded."""
        metrics = ProviderMetrics()
        assert metrics.avg_latency_ms == 0

    def test_provider_metrics_calculation_p95_latency(self):
        """Test 95th percentile latency calculation."""
        metrics = ProviderMetrics()
        # Add 100 latencies from 100ms to 1000ms
        for i in range(1, 101):
            metrics.latencies.append(i * 10)

        p95 = metrics.p95_latency_ms
        assert p95 >= 900  # Should be around 95th percentile


class TestProviderStatusTracker:
    """Tests for ProviderStatusTracker."""

    def test_record_request_success(self, tracker):
        """Test recording a successful request."""
        tracker.record_request("groq", latency_ms=500, success=True)

        assert tracker.providers["groq"].total_requests == 1
        assert tracker.providers["groq"].total_failures == 0
        assert tracker.providers["groq"].last_request_time is not None

    def test_record_request_failure(self, tracker):
        """Test recording a failed request."""
        tracker.record_request("groq", latency_ms=500, success=False, error="Timeout")

        assert tracker.providers["groq"].total_requests == 1
        assert tracker.providers["groq"].total_failures == 1
        assert tracker.providers["groq"].last_error == "Timeout"
        assert tracker.providers["groq"].last_error_time is not None

    def test_record_rate_limit(self, tracker):
        """Test recording a rate limit hit."""
        tracker.record_rate_limit("groq")

        assert tracker.providers["groq"].last_429_time is not None

    def test_set_rpm_current(self, tracker):
        """Test setting current RPM usage."""
        tracker.set_rpm_current("groq", 15)

        assert tracker.providers["groq"].rpm_current == 15

    def test_get_status_healthy(self, tracker):
        """Test status determination for healthy provider."""
        config = {
            "rpm_limit": 30,
            "enabled": True,
            "model": "llama-3.1-70b"
        }

        tracker.record_request("groq", latency_ms=500, success=True)
        tracker.set_rpm_current("groq", 10)

        status = tracker.get_status("groq", config)

        assert status.status == ProviderStatusEnum.HEALTHY
        assert status.rpm_available == 20
        assert status.failure_rate == 0.0

    def test_get_status_degraded_high_latency(self, tracker):
        """Test status determination when latency is high."""
        config = {
            "rpm_limit": 30,
            "enabled": True,
            "model": "llama-3.1-70b"
        }

        tracker.record_request("groq", latency_ms=2500, success=True)
        tracker.set_rpm_current("groq", 10)

        status = tracker.get_status("groq", config)

        assert status.status == ProviderStatusEnum.DEGRADED

    def test_get_status_degraded_high_failure_rate(self, tracker):
        """Test status determination when failure rate is high (but no recent errors)."""
        config = {
            "rpm_limit": 30,
            "enabled": True,
            "model": "llama-3.1-70b"
        }

        # Record 100 requests with 2 failures (2% failure rate)
        for _ in range(98):
            tracker.record_request("groq", latency_ms=500, success=True)
        for _ in range(2):
            tracker.record_request("groq", latency_ms=500, success=False)

        tracker.set_rpm_current("groq", 10)

        # Clear the recent error time to simulate old errors
        metrics = tracker.providers["groq"]
        metrics.last_error_time = datetime.now(timezone.utc) - timedelta(minutes=1)

        status = tracker.get_status("groq", config)

        assert status.status == ProviderStatusEnum.DEGRADED

    def test_get_status_degraded_low_rpm_available(self, tracker):
        """Test status determination when RPM available is low."""
        config = {
            "rpm_limit": 30,
            "enabled": True,
            "model": "llama-3.1-70b"
        }

        tracker.record_request("groq", latency_ms=500, success=True)
        tracker.set_rpm_current("groq", 27)  # Only 3 RPM available

        status = tracker.get_status("groq", config)

        assert status.status == ProviderStatusEnum.DEGRADED

    def test_get_status_unavailable_rpm_zero(self, tracker):
        """Test status determination when RPM is exhausted."""
        config = {
            "rpm_limit": 30,
            "enabled": True,
            "model": "llama-3.1-70b"
        }

        tracker.record_request("groq", latency_ms=500, success=True)
        tracker.set_rpm_current("groq", 30)  # All RPM used

        status = tracker.get_status("groq", config)

        assert status.status == ProviderStatusEnum.UNAVAILABLE

    def test_get_status_unavailable_recent_error(self, tracker):
        """Test status determination when recent error occurred."""
        config = {
            "rpm_limit": 30,
            "enabled": True,
            "model": "llama-3.1-70b"
        }

        tracker.record_request("groq", latency_ms=500, success=False, error="Connection error")
        tracker.set_rpm_current("groq", 5)

        status = tracker.get_status("groq", config)

        assert status.status == ProviderStatusEnum.UNAVAILABLE

    def test_get_status_unavailable_disabled(self, tracker):
        """Test status determination when provider is disabled."""
        config = {
            "rpm_limit": 30,
            "enabled": False,
            "model": "llama-3.1-70b"
        }

        tracker.record_request("groq", latency_ms=500, success=True)
        tracker.set_rpm_current("groq", 5)

        status = tracker.get_status("groq", config)

        assert status.status == ProviderStatusEnum.UNAVAILABLE


class TestProviderStatusModel:
    """Tests for ProviderStatus Pydantic model."""

    def test_provider_status_model_serialization(self, tracker):
        """Test that ProviderStatus can be serialized to JSON."""
        config = {
            "rpm_limit": 30,
            "enabled": True,
            "model": "llama-3.1-70b"
        }

        tracker.record_request("groq", latency_ms=500, success=True)
        tracker.set_rpm_current("groq", 10)

        status = tracker.get_status("groq", config)

        # Should be serializable to JSON
        json_data = status.model_dump_json()
        assert json_data is not None
        assert "groq" in json_data
        assert "llama-3.1-70b" in json_data
        assert "healthy" in json_data
