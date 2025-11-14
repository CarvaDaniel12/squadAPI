"""
Unit tests for Rate Limiter Prometheus Metrics

Tests Story 6.1.5: Rate Limiter Prometheus Metrics - Simplified Version
"""

import pytest
from prometheus_client import REGISTRY

from src.rate_limit.combined import (
    CombinedRateLimiter,
    rate_limit_rpm_limit,
    rate_limit_burst_capacity,
    rate_limit_tokens_capacity,
    rate_limit_window_occupancy
)
from src.models.rate_limit import ProviderRateLimitConfig


def get_metric_value(metric_name: str, provider: str) -> float:
    """Helper to get Prometheus metric value by name and provider label"""
    for metric in REGISTRY.collect():
        if metric.name == metric_name:
            for sample in metric.samples:
                if sample.labels.get('provider') == provider:
                    return sample.value
    return None


@pytest.fixture
def combined_limiter():
    """Create combined rate limiter for testing"""
    return CombinedRateLimiter(redis_client=None)  # Use in-memory


@pytest.mark.asyncio
async def test_metrics_initialized_on_register_provider(combined_limiter):
    """Test that Prometheus metrics are initialized when provider is registered"""
    # Arrange
    config = ProviderRateLimitConfig(rpm=30, tpm=30000, burst=5, window_size=60)

    # Act
    combined_limiter.register_provider("groq", config)

    # Assert
    assert get_metric_value('rate_limit_rpm_limit', provider='groq') == 30
    assert get_metric_value('rate_limit_burst_capacity', provider='groq') == 5
    assert get_metric_value('rate_limit_tokens_capacity', provider='groq') == 5


@pytest.mark.asyncio
async def test_window_occupancy_updates_after_acquire(combined_limiter):
    """Test that window_occupancy metric updates after acquiring rate limit"""
    # Arrange
    config = ProviderRateLimitConfig(rpm=60, tpm=60000, burst=10, window_size=60)
    combined_limiter.register_provider("cerebras", config)

    # Act
    async with combined_limiter.acquire("cerebras"):
        # During acquisition, window should have 1 request
        occupancy = get_metric_value('rate_limit_window_occupancy', provider='cerebras')
        assert occupancy == 1


@pytest.mark.asyncio
async def test_metrics_independent_per_provider(combined_limiter):
    """Test that metrics are tracked independently per provider"""
    # Arrange
    config_groq = ProviderRateLimitConfig(rpm=30, tpm=30000, burst=5, window_size=60)
    config_cerebras = ProviderRateLimitConfig(rpm=60, tpm=60000, burst=10, window_size=60)

    combined_limiter.register_provider("groq", config_groq)
    combined_limiter.register_provider("cerebras", config_cerebras)

    # Act
    async with combined_limiter.acquire("groq"):
        pass

    async with combined_limiter.acquire("cerebras"):
        pass
    async with combined_limiter.acquire("cerebras"):
        pass

    # Assert
    groq_occupancy = get_metric_value('rate_limit_window_occupancy', provider='groq')
    cerebras_occupancy = get_metric_value('rate_limit_window_occupancy', provider='cerebras')

    assert groq_occupancy == 1
    assert cerebras_occupancy == 2

    assert get_metric_value('rate_limit_rpm_limit', provider='groq') == 30
    assert get_metric_value('rate_limit_rpm_limit', provider='cerebras') == 60
