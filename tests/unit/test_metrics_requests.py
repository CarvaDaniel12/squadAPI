"""
Unit tests for Prometheus request metrics.
"""
import pytest
from src.metrics.requests import (
    llm_requests_total,
    llm_requests_success,
    llm_requests_failure,
    llm_requests_429_total,
    record_request_success,
    record_request_failure,
    record_429_error,
    classify_error
)


def test_record_request_success():
    """Test successful request increments correct metrics."""
    # Get initial values
    initial_total = llm_requests_total.labels(
        provider='groq',
        agent='analyst',
        status='success'
    )._value.get()

    initial_success = llm_requests_success.labels(
        provider='groq',
        agent='analyst'
    )._value.get()

    # Record success
    record_request_success(provider='groq', agent='analyst')

    # Verify increments
    final_total = llm_requests_total.labels(
        provider='groq',
        agent='analyst',
        status='success'
    )._value.get()

    final_success = llm_requests_success.labels(
        provider='groq',
        agent='analyst'
    )._value.get()

    assert final_total == initial_total + 1
    assert final_success == initial_success + 1


def test_record_request_failure():
    """Test failed request increments failure metrics."""
    initial_total = llm_requests_total.labels(
        provider='cerebras',
        agent='pm',
        status='failure'
    )._value.get()

    initial_failure = llm_requests_failure.labels(
        provider='cerebras',
        agent='pm',
        error_type='timeout'
    )._value.get()

    # Record failure
    record_request_failure(
        provider='cerebras',
        agent='pm',
        error_type='timeout'
    )

    final_total = llm_requests_total.labels(
        provider='cerebras',
        agent='pm',
        status='failure'
    )._value.get()

    final_failure = llm_requests_failure.labels(
        provider='cerebras',
        agent='pm',
        error_type='timeout'
    )._value.get()

    assert final_total == initial_total + 1
    assert final_failure == initial_failure + 1


def test_record_429_error():
    """Test 429 error increments rate limit counter."""
    initial = llm_requests_429_total.labels(provider='groq')._value.get()

    record_429_error(provider='groq')

    final = llm_requests_429_total.labels(provider='groq')._value.get()

    assert final == initial + 1


def test_classify_error_rate_limit():
    """Test error classification for rate limits."""
    # 429 in message
    error = Exception("429 Too Many Requests")
    assert classify_error(error) == 'rate_limit'

    # Rate limit in message
    error = Exception("Rate limit exceeded")
    assert classify_error(error) == 'rate_limit'


def test_classify_error_timeout():
    """Test error classification for timeouts."""
    import asyncio

    error = asyncio.TimeoutError("Request timeout")
    assert classify_error(error) == 'timeout'


def test_classify_error_network():
    """Test error classification for network errors."""
    error = ConnectionError("Connection failed")
    assert classify_error(error) == 'network'


def test_classify_error_unknown():
    """Test error classification for unknown errors."""
    error = ValueError("Some random error")
    assert classify_error(error) == 'unknown'
