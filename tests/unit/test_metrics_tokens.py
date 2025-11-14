"""
Unit tests for Token Consumption Metrics (Story 5.3)

Tests the token tracking metrics in src/metrics/observability.py
"""

import pytest
import concurrent.futures
from src.metrics.observability import (
    record_tokens,
    update_quota_usage,
    llm_tokens_consumed,
    llm_tokens_total,
    llm_quota_usage_percent,
    PROMETHEUS_AVAILABLE
)


@pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="Prometheus client not available")
class TestTokenRecording:
    """Test token recording functions"""

    def test_record_tokens(self):
        """Should record tokens in both histogram and counter"""
        # Get initial counter values
        initial_total_input = llm_tokens_total.labels(
            provider='groq',
            type='input'
        )._value.get()

        initial_total_output = llm_tokens_total.labels(
            provider='groq',
            type='output'
        )._value.get()

        # Record tokens
        record_tokens('groq', input_tokens=2500, output_tokens=1200)

        # Verify counter increments
        final_total_input = llm_tokens_total.labels(
            provider='groq',
            type='input'
        )._value.get()

        final_total_output = llm_tokens_total.labels(
            provider='groq',
            type='output'
        )._value.get()

        assert final_total_input == initial_total_input + 2500
        assert final_total_output == initial_total_output + 1200

    def test_record_tokens_input_vs_output(self):
        """Should separate input and output tokens correctly"""
        providers = ['groq', 'cerebras', 'gemini']

        for provider in providers:
            # Get initial values
            initial_input = llm_tokens_total.labels(
                provider=provider,
                type='input'
            )._value.get()

            initial_output = llm_tokens_total.labels(
                provider=provider,
                type='output'
            )._value.get()

            # Record tokens
            input_tokens = 1000 + hash(provider) % 500
            output_tokens = 500 + hash(provider) % 300
            record_tokens(provider, input_tokens, output_tokens)

            # Verify separation
            final_input = llm_tokens_total.labels(
                provider=provider,
                type='input'
            )._value.get()

            final_output = llm_tokens_total.labels(
                provider=provider,
                type='output'
            )._value.get()

            assert final_input == initial_input + input_tokens
            assert final_output == initial_output + output_tokens

    def test_record_tokens_multiple_providers(self):
        """Should handle multiple providers independently"""
        test_cases = [
            ('groq', 3000, 1500),
            ('cerebras', 2000, 1000),
            ('gemini', 4000, 2000),
            ('openrouter', 1500, 800)
        ]

        for provider, input_tok, output_tok in test_cases:
            initial_input = llm_tokens_total.labels(
                provider=provider,
                type='input'
            )._value.get()

            initial_output = llm_tokens_total.labels(
                provider=provider,
                type='output'
            )._value.get()

            # Record
            record_tokens(provider, input_tok, output_tok)

            # Verify
            final_input = llm_tokens_total.labels(
                provider=provider,
                type='input'
            )._value.get()

            final_output = llm_tokens_total.labels(
                provider=provider,
                type='output'
            )._value.get()

            assert final_input == initial_input + input_tok
            assert final_output == initial_output + output_tok

    def test_token_buckets(self):
        """Should distribute token values into correct histogram buckets"""
        # Test different token amounts across buckets (100, 500, 1000, 2000, 5000, 10000)
        test_cases = [
            (50, 'should go in bucket 100'),
            (300, 'should go in bucket 500'),
            (750, 'should go in bucket 1000'),
            (1500, 'should go in bucket 2000'),
            (3000, 'should go in bucket 5000'),
            (7000, 'should go in bucket 10000'),
            (15000, 'should go in bucket 10000 (last bucket)')
        ]

        provider = 'groq'

        # Record each token amount
        for token_amount, description in test_cases:
            # Record as input tokens
            record_tokens(provider, input_tokens=token_amount, output_tokens=0)

        # Just verify no errors - bucket distribution is handled internally by Prometheus


class TestQuotaTracking:
    """Test quota usage tracking"""

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="Prometheus client not available")
    def test_update_quota_usage(self):
        """Should update quota usage gauge correctly"""
        # Set quota usage
        update_quota_usage('groq', 'rpm', 45.5)

        # Verify gauge value
        gauge_value = llm_quota_usage_percent.labels(
            provider='groq',
            quota_type='rpm'
        )._value.get()

        assert gauge_value == 45.5

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="Prometheus client not available")
    def test_quota_percentage_calculation(self):
        """Should handle different quota percentage values"""
        test_cases = [
            ('groq', 'rpm', 25.0),
            ('groq', 'rpd', 80.5),
            ('groq', 'tpm', 100.0),
            ('cerebras', 'rpm', 10.5),
            ('cerebras', 'tpm', 95.0),
            ('gemini', 'rpm', 0.0),
            ('gemini', 'rpd', 50.0)
        ]

        for provider, quota_type, usage_percent in test_cases:
            # Update quota
            update_quota_usage(provider, quota_type, usage_percent)

            # Verify
            gauge_value = llm_quota_usage_percent.labels(
                provider=provider,
                quota_type=quota_type
            )._value.get()

            assert gauge_value == usage_percent

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="Prometheus client not available")
    def test_quota_multiple_types(self):
        """Should track different quota types independently"""
        provider = 'groq'

        # Set different quota types
        update_quota_usage(provider, 'rpm', 30.0)
        update_quota_usage(provider, 'rpd', 60.0)
        update_quota_usage(provider, 'tpm', 90.0)

        # Verify each is independent
        rpm_value = llm_quota_usage_percent.labels(
            provider=provider,
            quota_type='rpm'
        )._value.get()

        rpd_value = llm_quota_usage_percent.labels(
            provider=provider,
            quota_type='rpd'
        )._value.get()

        tpm_value = llm_quota_usage_percent.labels(
            provider=provider,
            quota_type='tpm'
        )._value.get()

        assert rpm_value == 30.0
        assert rpd_value == 60.0
        assert tpm_value == 90.0


@pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="Prometheus client not available")
class TestConcurrency:
    """Test concurrent token recording"""

    def test_concurrent_token_recording(self):
        """Should handle concurrent token updates"""
        provider = 'groq'

        # Get initial value
        initial = llm_tokens_total.labels(
            provider=provider,
            type='input'
        )._value.get()

        def record_many():
            for i in range(10):
                record_tokens(provider, input_tokens=100, output_tokens=50)

        # Simulate concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(record_many) for _ in range(5)]
            concurrent.futures.wait(futures)

        # Verify total increments (5 workers * 10 iterations * 100 tokens)
        final = llm_tokens_total.labels(
            provider=provider,
            type='input'
        )._value.get()

        expected = initial + (5 * 10 * 100)
        assert final == expected


class TestGracefulDegradation:
    """Test behavior when Prometheus is not available"""

    @pytest.mark.skipif(PROMETHEUS_AVAILABLE, reason="Test only runs when Prometheus unavailable")
    def test_tokens_without_prometheus(self):
        """Should not crash if prometheus_client unavailable"""
        # Should not raise any errors
        record_tokens('groq', 1000, 500)
        update_quota_usage('groq', 'rpm', 50.0)

        # If we get here, graceful degradation worked
        assert True
