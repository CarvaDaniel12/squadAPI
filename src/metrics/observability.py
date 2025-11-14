"""
Observability Metrics - Complete Suite

Comprehensive Prometheus metrics for latency, tokens, and provider health.
Consolidates all observability metrics in one place.
"""

import logging
from typing import Optional
import time

try:
    from prometheus_client import Counter, Histogram, Gauge, Info
    PROMETHEUS_AVAILABLE = True
except ImportError:
    Counter = None
    Histogram = None
    Gauge = None
    Info = None
    PROMETHEUS_AVAILABLE = False


logger = logging.getLogger(__name__)


# ============================================================================
# LATENCY METRICS (Story 5.2)
# ============================================================================

if PROMETHEUS_AVAILABLE:
    # Request duration histogram
    llm_request_duration_seconds = Histogram(
        'llm_request_duration_seconds',
        'LLM request latency in seconds',
        ['provider', 'agent'],
        buckets=(0.5, 1, 2, 5, 10, 30)  # Buckets for P50, P95, P99 calculation
    )
    
    # Provider-specific latency
    llm_provider_latency_seconds = Histogram(
        'llm_provider_latency_seconds',
        'Provider API call latency',
        ['provider'],
        buckets=(0.1, 0.5, 1, 2, 5, 10, 30)
    )

else:
    llm_request_duration_seconds = None
    llm_provider_latency_seconds = None


# ============================================================================
# TOKEN CONSUMPTION METRICS (Story 5.3)
# ============================================================================

if PROMETHEUS_AVAILABLE:
    # Token consumption histogram
    llm_tokens_consumed = Histogram(
        'llm_tokens_consumed',
        'Tokens consumed per request',
        ['provider', 'type'],  # type: input or output
        buckets=(100, 500, 1000, 2000, 5000, 10000)
    )
    
    # Total token counter
    llm_tokens_total = Counter(
        'llm_tokens_total',
        'Total tokens consumed',
        ['provider', 'type']  # type: input or output
    )
    
    # Quota usage gauge (percentage of free tier)
    llm_quota_usage_percent = Gauge(
        'llm_quota_usage_percent',
        'Quota usage as percentage of free tier limit',
        ['provider', 'quota_type']  # quota_type: rpm, rpd, tpm
    )

else:
    llm_tokens_consumed = None
    llm_tokens_total = None
    llm_quota_usage_percent = None


# ============================================================================
# AGENT-SPECIFIC METRICS
# ============================================================================

if PROMETHEUS_AVAILABLE:
    # Agent activity gauge
    llm_agent_active = Gauge(
        'llm_agent_active',
        'Currently active agents',
        ['agent']
    )
    
    # Agent tier distribution
    llm_agent_tier_usage = Counter(
        'llm_agent_tier_usage',
        'Agent requests by tier',
        ['agent', 'tier']  # tier: boss, worker, creative
    )

else:
    llm_agent_active = None
    llm_agent_tier_usage = None


# ============================================================================
# RECORDING FUNCTIONS
# ============================================================================

def record_latency(provider: str, agent: str, latency_seconds: float):
    """Record request latency"""
    if llm_request_duration_seconds:
        llm_request_duration_seconds.labels(
            provider=provider,
            agent=agent
        ).observe(latency_seconds)


def record_provider_latency(provider: str, latency_seconds: float):
    """Record provider-specific latency"""
    if llm_provider_latency_seconds:
        llm_provider_latency_seconds.labels(provider=provider).observe(latency_seconds)


def record_tokens(provider: str, input_tokens: int, output_tokens: int):
    """Record token consumption"""
    if llm_tokens_consumed:
        llm_tokens_consumed.labels(provider=provider, type='input').observe(input_tokens)
        llm_tokens_consumed.labels(provider=provider, type='output').observe(output_tokens)
    
    if llm_tokens_total:
        llm_tokens_total.labels(provider=provider, type='input').inc(input_tokens)
        llm_tokens_total.labels(provider=provider, type='output').inc(output_tokens)


def update_quota_usage(provider: str, quota_type: str, usage_percent: float):
    """Update quota usage gauge"""
    if llm_quota_usage_percent:
        llm_quota_usage_percent.labels(
            provider=provider,
            quota_type=quota_type
        ).set(usage_percent)


def set_agent_active(agent: str, is_active: bool):
    """Set agent active status"""
    if llm_agent_active:
        llm_agent_active.labels(agent=agent).set(1 if is_active else 0)


def record_agent_tier_usage(agent: str, tier: str):
    """Record agent tier usage"""
    if llm_agent_tier_usage:
        llm_agent_tier_usage.labels(agent=agent, tier=tier).inc()


# ============================================================================
# CONTEXT MANAGERS FOR AUTO-TIMING
# ============================================================================

class LatencyTracker:
    """Context manager for automatic latency tracking"""
    
    def __init__(self, provider: str, agent: str):
        self.provider = provider
        self.agent = agent
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        set_agent_active(self.agent, True)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            latency_seconds = time.time() - self.start_time
            record_latency(self.provider, self.agent, latency_seconds)
            record_provider_latency(self.provider, latency_seconds)
        
        set_agent_active(self.agent, False)
        return False


# For async usage
class AsyncLatencyTracker:
    """Async context manager for latency tracking"""
    
    def __init__(self, provider: str, agent: str):
        self.provider = provider
        self.agent = agent
        self.start_time = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        set_agent_active(self.agent, True)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            latency_seconds = time.time() - self.start_time
            record_latency(self.provider, self.agent, latency_seconds)
            record_provider_latency(self.provider, latency_seconds)
        
        set_agent_active(self.agent, False)
        return False


# ============================================================================
# UTILITY
# ============================================================================

def get_observability_stats() -> dict:
    """Get observability metrics status"""
    return {
        'prometheus_available': PROMETHEUS_AVAILABLE,
        'latency_metrics': llm_request_duration_seconds is not None,
        'token_metrics': llm_tokens_consumed is not None,
        'agent_metrics': llm_agent_active is not None
    }




