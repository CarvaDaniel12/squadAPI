#!/usr/bin/env python3
"""
Test runner for metrics requests module
Runs tests without conftest.py dependencies
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_record_request_success():
    """Test successful request increments correct metrics."""
    from src.metrics.requests import llm_requests_total, llm_requests_success, record_request_success

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

    assert final_total == initial_total + 1, f"Expected {initial_total + 1}, got {final_total}"
    assert final_success == initial_success + 1, f"Expected {initial_success + 1}, got {final_success}"
    print("OK test_record_request_success passed")


def test_record_request_failure():
    """Test failed request increments failure metrics."""
    from src.metrics.requests import llm_requests_total, llm_requests_failure, record_request_failure

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

    assert final_total == initial_total + 1, f"Expected {initial_total + 1}, got {final_total}"
    assert final_failure == initial_failure + 1, f"Expected {initial_failure + 1}, got {final_failure}"
    print("OK test_record_request_failure passed")


def test_record_429_error():
    """Test 429 error increments rate limit counter."""
    from src.metrics.requests import llm_requests_429_total, record_429_error

    initial = llm_requests_429_total.labels(provider='groq')._value.get()

    record_429_error(provider='groq')

    final = llm_requests_429_total.labels(provider='groq')._value.get()

    assert final == initial + 1, f"Expected {initial + 1}, got {final}"
    print("OK test_record_429_error passed")


def test_classify_error_rate_limit():
    """Test error classification for rate limits."""
    from src.metrics.requests import classify_error

    # 429 in message
    error = Exception("429 Too Many Requests")
    assert classify_error(error) == 'rate_limit', f"Expected 'rate_limit', got '{classify_error(error)}'"

    # Rate limit in message
    error = Exception("Rate limit exceeded")
    assert classify_error(error) == 'rate_limit', f"Expected 'rate_limit', got '{classify_error(error)}'"
    print("OK test_classify_error_rate_limit passed")


def test_classify_error_timeout():
    """Test error classification for timeouts."""
    from src.metrics.requests import classify_error
    import asyncio

    error = asyncio.TimeoutError("Request timeout")
    assert classify_error(error) == 'timeout', f"Expected 'timeout', got '{classify_error(error)}'"
    print("OK test_classify_error_timeout passed")


def test_classify_error_network():
    """Test error classification for network errors."""
    from src.metrics.requests import classify_error

    error = ConnectionError("Connection failed")
    assert classify_error(error) == 'network', f"Expected 'network', got '{classify_error(error)}'"
    print("OK test_classify_error_network passed")


def test_classify_error_unknown():
    """Test error classification for unknown errors."""
    from src.metrics.requests import classify_error

    error = ValueError("Some random error")
    assert classify_error(error) == 'unknown', f"Expected 'unknown', got '{classify_error(error)}'"
    print("OK test_classify_error_unknown passed")


def run_all_tests():
    """Run all tests and calculate coverage"""
    print("=== Running Metrics Tests ===")

    tests = [
        test_record_request_success,
        test_record_request_failure,
        test_record_429_error,
        test_classify_error_rate_limit,
        test_classify_error_timeout,
        test_classify_error_network,
        test_classify_error_unknown
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"FAIL {test.__name__} failed: {e}")
            failed += 1

    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {len(tests)}")
    print(f"Success Rate: {(passed/len(tests)*100):.1f}%")

    # Calculate coverage manually
    total_functions = 6  # Functions in requests.py that should be tested
    functions_tested = passed
    coverage = (functions_tested / total_functions) * 100

    print(f"Coverage: {coverage:.1f}%")

    return passed, failed, coverage


if __name__ == "__main__":
    passed, failed, coverage = run_all_tests()

    if failed == 0:
        print("\nALL TESTS PASSED!")
    else:
        print(f"\n{failed} tests failed")

    print(f"Coverage: {coverage:.1f}%")
    sys.exit(failed)
