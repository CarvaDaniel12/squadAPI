"""
Rate Limiting Metrics

Prometheus metrics for rate limiting observability.
Tracks requests, 429 errors, token usage, and window occupancy.
"""

import logging
from typing import Optional

try:
    from prometheus_client import Counter, Gauge, Histogram
except ImportError:
    Counter = None
    Gauge = None
    Histogram = None

# Import shared request metrics from requests.py to avoid duplication
from .requests import llm_requests_total, llm_requests_429_total
from .observability import llm_tokens_total


logger = logging.getLogger(__name__)


# ============================================================================
# COUNTERS (cumulative, always increasing)
# ============================================================================

if Counter:
    # Total retry attempts by provider
    llm_retries_total = Counter(
        'llm_retries_total',
        'Total retry attempts',
        ['provider', 'reason']  # reason: rate_limit, network, server_error
    )

else:
    llm_retries_total = None
    logger.warning("prometheus_client not installed, metrics disabled")
# ============================================================================
# GAUGES (current value, can go up or down)
# ============================================================================

if Gauge:
    # Available tokens in token bucket by provider
    llm_bucket_tokens_available = Gauge(
        'llm_bucket_tokens_available',
        'Available tokens in token bucket',
        ['provider']
    )

    # Current window occupancy (requests in last 60s) by provider
    llm_window_occupancy = Gauge(
        'llm_window_occupancy',
        'Requests in sliding window (last N seconds)',
        ['provider']
    )

    # Global semaphore active slots
    llm_semaphore_active = Gauge(
        'llm_semaphore_active',
        'Active requests (global semaphore)',
        []
    )

    # Global semaphore available slots
    llm_semaphore_available = Gauge(
        'llm_semaphore_available',
        'Available semaphore slots',
        []
    )

    # Rate limit status (1 = limited, 0 = not limited)
    llm_rate_limited_status = Gauge(
        'llm_rate_limited_status',
        'Rate limit status (1 = limited, 0 = available)',
        ['provider']
    )

else:
    llm_bucket_tokens_available = None
    llm_window_occupancy = None
    llm_semaphore_active = None
    llm_semaphore_available = None
    llm_rate_limited_status = None


# ============================================================================
# HISTOGRAMS (distribution of values)
# ============================================================================

if Histogram:
    # Latency distribution for LLM requests
    llm_request_latency_seconds = Histogram(
        'llm_request_latency_seconds',
        'LLM request latency in seconds',
        ['provider'],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
    )

    # Wait time due to rate limiting
    llm_rate_limit_wait_seconds = Histogram(
        'llm_rate_limit_wait_seconds',
        'Wait time due to rate limiting',
        ['provider'],
        buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0)
    )

else:
    llm_request_latency_seconds = None
    llm_rate_limit_wait_seconds = None


# ============================================================================
# METRIC RECORDING FUNCTIONS
# ============================================================================

def record_request(provider: str, agent: str, status: str):
    """
    Record an LLM request

    Args:
        provider: Provider name (e.g., 'groq')
        agent: Agent ID (e.g., 'analyst')
        status: Request status ('success', 'error', 'rate_limited')
    """
    if llm_requests_total:
        llm_requests_total.labels(provider=provider, agent=agent, status=status).inc()


def record_429_error(provider: str, agent: str = 'unknown'):
    """
    Record a 429 rate limit error

    Args:
        provider: Provider name
        agent: Agent ID (default: 'unknown')
    """
    if llm_requests_429_total:
        llm_requests_429_total.labels(provider=provider).inc()

    # Also increment general counter
    record_request(provider, agent, 'rate_limited')


def record_retry(provider: str, reason: str):
    """
    Record a retry attempt

    Args:
        provider: Provider name
        reason: Retry reason ('rate_limit', 'network', 'server_error')
    """
    if llm_retries_total:
        llm_retries_total.labels(provider=provider, reason=reason).inc()


def record_tokens(provider: str, input_tokens: int, output_tokens: int):
    """
    Record token usage

    Args:
        provider: Provider name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    """
    if llm_tokens_total:
        llm_tokens_total.labels(provider=provider, type='input').inc(input_tokens)
        llm_tokens_total.labels(provider=provider, type='output').inc(output_tokens)


def update_bucket_tokens(provider: str, available: int):
    """
    Update token bucket availability gauge

    Args:
        provider: Provider name
        available: Number of available tokens
    """
    if llm_bucket_tokens_available:
        llm_bucket_tokens_available.labels(provider=provider).set(available)


def update_window_occupancy(provider: str, count: int):
    """
    Update sliding window occupancy gauge

    Args:
        provider: Provider name
        count: Number of requests in window
    """
    if llm_window_occupancy:
        llm_window_occupancy.labels(provider=provider).set(count)


def update_semaphore_stats(active: int, available: int):
    """
    Update global semaphore statistics

    Args:
        active: Number of active requests
        available: Number of available slots
    """
    if llm_semaphore_active:
        llm_semaphore_active.set(active)

    if llm_semaphore_available:
        llm_semaphore_available.set(available)


def update_rate_limited_status(provider: str, is_limited: bool):
    """
    Update rate limit status gauge

    Args:
        provider: Provider name
        is_limited: True if provider is currently rate limited
    """
    if llm_rate_limited_status:
        llm_rate_limited_status.labels(provider=provider).set(1 if is_limited else 0)


def record_latency(provider: str, latency_seconds: float):
    """
    Record request latency

    Args:
        provider: Provider name
        latency_seconds: Request latency in seconds
    """
    if llm_request_latency_seconds:
        llm_request_latency_seconds.labels(provider=provider).observe(latency_seconds)


def record_rate_limit_wait(provider: str, wait_seconds: float):
    """
    Record time spent waiting due to rate limiting

    Args:
        provider: Provider name
        wait_seconds: Wait time in seconds
    """
    if llm_rate_limit_wait_seconds:
        llm_rate_limit_wait_seconds.labels(provider=provider).observe(wait_seconds)


# ============================================================================
# BULK UPDATE (for efficiency)
# ============================================================================

def update_rate_limiter_state(provider: str, state: dict):
    """
    Update multiple metrics from rate limiter state

    Args:
        provider: Provider name
        state: State dict from CombinedRateLimiter.get_state()
    """
    # Update window occupancy
    if 'window_count' in state:
        update_window_occupancy(provider, state['window_count'])

    # Update rate limited status
    if 'is_limited' in state:
        update_rate_limited_status(provider, state['is_limited'])


def update_semaphore_state(stats: dict):
    """
    Update semaphore metrics from stats

    Args:
        stats: Stats dict from GlobalSemaphore.get_stats()
    """
    if 'active_count' in stats and 'available_slots' in stats:
        update_semaphore_stats(stats['active_count'], stats['available_slots'])


# ============================================================================
# UTILITY
# ============================================================================

def is_metrics_enabled() -> bool:
    """Check if metrics collection is enabled"""
    return Counter is not None and Gauge is not None

