"""
Prometheus metrics for LLM request tracking.
Tracks request counts, success/failure rates, and error types.
"""
try:
    from prometheus_client import Counter
    PROMETHEUS_AVAILABLE = True
except ImportError:
    Counter = None
    PROMETHEUS_AVAILABLE = False

# Total requests counter
if PROMETHEUS_AVAILABLE:
    llm_requests_total = Counter(
        'llm_requests_total',
        'Total number of LLM requests',
        ['provider', 'agent', 'status']  # labels
    )

    # Success counter (convenience metric)
    llm_requests_success = Counter(
        'llm_requests_success',
        'Number of successful LLM requests',
        ['provider', 'agent']
    )

    # Failure counter with error type
    llm_requests_failure = Counter(
        'llm_requests_failure',
        'Number of failed LLM requests',
        ['provider', 'agent', 'error_type']
    )

    # 429 rate limit errors (critical metric)
    llm_requests_429_total = Counter(
        'llm_requests_429_total',
        'Number of 429 rate limit errors',
        ['provider']
    )
else:
    llm_requests_total = None
    llm_requests_success = None
    llm_requests_failure = None
    llm_requests_429_total = None


def record_request_start(provider: str, agent: str):
    """
    Called when request starts.
    Currently no-op, reserved for future use (in-flight tracking).
    """
    pass


def record_request_success(provider: str, agent: str):
    """
    Record a successful LLM request.

    Args:
        provider: Provider name (groq, cerebras, gemini, etc.)
        agent: Agent ID (analyst, pm, architect, etc.)
    """
    if llm_requests_total:
        llm_requests_total.labels(
            provider=provider,
            agent=agent,
            status='success'
        ).inc()

    if llm_requests_success:
        llm_requests_success.labels(
            provider=provider,
            agent=agent
        ).inc()


def record_request_failure(provider: str, agent: str, error_type: str):
    """
    Record a failed LLM request.

    Args:
        provider: Provider name
        agent: Agent ID
        error_type: Error category (rate_limit, timeout, network, api_error, unknown)
    """
    if llm_requests_total:
        llm_requests_total.labels(
            provider=provider,
            agent=agent,
            status='failure'
        ).inc()

    if llm_requests_failure:
        llm_requests_failure.labels(
            provider=provider,
            agent=agent,
            error_type=error_type
        ).inc()


def record_429_error(provider: str):
    """
    Record a 429 rate limit error (critical metric).

    Args:
        provider: Provider that returned 429
    """
    if llm_requests_429_total:
        llm_requests_429_total.labels(provider=provider).inc()


def classify_error(exception: Exception) -> str:
    """
    Classify exception into error_type for metrics.

    Args:
        exception: The exception that occurred

    Returns:
        Error type string (rate_limit, timeout, network, api_error, unknown)
    """
    error_class = exception.__class__.__name__
    error_msg = str(exception).lower()

    # Rate limit errors
    if '429' in error_msg or 'rate limit' in error_msg:
        return 'rate_limit'

    # Timeout errors
    if 'timeout' in error_msg or error_class in ['TimeoutError', 'asyncio.TimeoutError']:
        return 'timeout'

    # Network errors
    if error_class in ['ConnectionError', 'ClientConnectorError', 'aiohttp.ClientError']:
        return 'network'

    # API errors (400-level except 429)
    if 'api' in error_msg or '400' in error_msg or '401' in error_msg or '403' in error_msg:
        return 'api_error'

    # Unknown
    return 'unknown'


# Backward compatibility functions
def record_success(provider: str, agent: str):
    """Backward compatibility wrapper"""
    return record_request_success(provider, agent)


def record_failure(provider: str, agent: str, error_type: str):
    """Backward compatibility wrapper"""
    return record_request_failure(provider, agent, error_type)


def record_429(provider: str):
    """Backward compatibility wrapper"""
    return record_429_error(provider)


def record_request(provider: str, agent: str, status: str):
    """
    Generic request recorder (for backward compatibility with tests)

    Args:
        provider: Provider name
        agent: Agent ID
        status: Request status (success, failure, timeout, etc.)
    """
    if status == 'success':
        record_request_success(provider, agent)
    else:
        record_request_failure(provider, agent, status)


def record_fallback(from_provider: str, to_provider: str, agent: str):
    """
    Record provider fallback event

    Args:
        from_provider: Original provider that failed
        to_provider: Fallback provider used
        agent: Agent ID
    """
    # For now, just record as a failure on original and success on fallback
    # Could add dedicated fallback metric in future
    pass


def is_metrics_enabled() -> bool:
    """Check if Prometheus metrics are available"""
    return PROMETHEUS_AVAILABLE


def get_request_stats() -> dict:
    """
    Get current request statistics (for testing/debugging)

    Returns:
        Dict with metric counts (not real Prometheus values, just for tests)
    """
    # Note: This is a stub for testing
    # Real Prometheus metrics don't provide easy access to current values
    return {
        'metrics_enabled': PROMETHEUS_AVAILABLE,
        'counters': {
            'llm_requests_total': 'N/A',
            'llm_requests_success': 'N/A',
            'llm_requests_failure': 'N/A',
            'llm_requests_429_total': 'N/A'
        }
    }




