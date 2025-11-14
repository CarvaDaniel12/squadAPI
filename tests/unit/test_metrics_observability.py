"""
Unit tests for Story 5.2 - Prometheus Latency Tracking

Tests the latency metrics implementation in src/metrics/observability.py
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock

from src.metrics.observability import (
    record_latency,
    record_provider_latency,
    LatencyTracker,
    AsyncLatencyTracker,
    PROMETHEUS_AVAILABLE,
    get_observability_stats
)


@pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="Prometheus client not available")
class TestLatencyRecording:
    """Test latency recording functions"""

    def test_record_latency(self):
        """Should record latency in histogram"""
        # Mock the histogram labels to track observe calls
        mock_histogram = Mock()
        mock_labels = Mock()
        mock_labels.observe = Mock()
        mock_histogram.labels.return_value = mock_labels

        # Patch the histogram to use our mock
        with patch('src.metrics.observability.llm_request_duration_seconds', mock_histogram):
            # Record latency
            record_latency('groq', 'analyst', 2.5)

            # Verify the histogram labels method was called with correct parameters
            mock_histogram.labels.assert_called_once_with(provider='groq', agent='analyst')

            # Verify observe was called with the latency value
            mock_labels.observe.assert_called_once_with(2.5)

    def test_record_provider_latency(self):
        """Should record provider-specific latency"""
        # Mock the histogram labels to track observe calls
        mock_histogram = Mock()
        mock_labels = Mock()
        mock_labels.observe = Mock()
        mock_histogram.labels.return_value = mock_labels

        # Patch the histogram to use our mock
        with patch('src.metrics.observability.llm_provider_latency_seconds', mock_histogram):
            # Record provider latency
            record_provider_latency('groq', 1.8)

            # Verify the histogram labels method was called with correct parameters
            mock_histogram.labels.assert_called_once_with(provider='groq')

            # Verify observe was called with the latency value
            mock_labels.observe.assert_called_once_with(1.8)

    def test_latency_with_multiple_providers(self):
        """Should handle multiple provider/agent combinations"""
        providers = ['groq', 'gemini', 'openai']
        agents = ['analyst', 'writer', 'researcher']

        # Mock the histograms to track calls
        mock_request_histogram = Mock()
        mock_provider_histogram = Mock()

        with patch('src.metrics.observability.llm_request_duration_seconds', mock_request_histogram):
            with patch('src.metrics.observability.llm_provider_latency_seconds', mock_provider_histogram):

                # Record latencies for all combinations
                for provider in providers:
                    for agent in agents:
                        record_latency(provider, agent, 1.0 + hash(f"{provider}{agent}") % 10)

                # Verify that labels was called for each combination
                expected_request_calls = len(providers) * len(agents)
                assert mock_request_histogram.labels.call_count == expected_request_calls

                # Now test provider latencies separately
                for provider in providers:
                    record_provider_latency(provider, 0.5 + hash(provider) % 5)

                expected_provider_calls = len(providers)
                assert mock_provider_histogram.labels.call_count == expected_provider_calls

                # Verify all observe calls were made
                assert mock_request_histogram.labels.return_value.observe.call_count == expected_request_calls
                assert mock_provider_histogram.labels.return_value.observe.call_count == expected_provider_calls

    def test_latency_buckets(self):
        """Should distribute latency values into correct buckets"""
        # Test different latency values across buckets
        test_cases = [
            (0.1, 'should go in bucket 0.5'),
            (0.7, 'should go in bucket 1'),
            (1.5, 'should go in bucket 2'),
            (3.0, 'should go in bucket 5'),
            (7.0, 'should go in bucket 10'),
            (15.0, 'should go in bucket 30'),
            (50.0, 'should go in bucket 30 (last bucket)')
        ]

        provider = 'groq'
        agent = 'test'

        # Mock the histograms to track observe calls
        mock_request_histogram = Mock()
        mock_provider_histogram = Mock()
        mock_request_histogram.labels.return_value.observe = Mock()
        mock_provider_histogram.labels.return_value.observe = Mock()

        with patch('src.metrics.observability.llm_request_duration_seconds', mock_request_histogram):
            with patch('src.metrics.observability.llm_provider_latency_seconds', mock_provider_histogram):

                # Record each latency
                for latency_value, description in test_cases:
                    record_latency(provider, agent, latency_value)
                    record_provider_latency(provider, latency_value)

                # Verify that all observe calls were made
                assert mock_request_histogram.labels.return_value.observe.call_count == len(test_cases)
                assert mock_provider_histogram.labels.return_value.observe.call_count == len(test_cases)

                # Verify the correct latency values were recorded
                observed_request_values = [call[0][0] for call in mock_request_histogram.labels.return_value.observe.call_args_list]
                observed_provider_values = [call[0][0] for call in mock_provider_histogram.labels.return_value.observe.call_args_list]

                expected_values = [latency for latency, _ in test_cases]

                assert observed_request_values == expected_values
                assert observed_provider_values == expected_values


class TestContextManagers:
    """Test latency tracker context managers"""

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="Prometheus client not available")
    def test_latency_tracker_context_manager(self):
        """Test synchronous context manager LatencyTracker"""
        provider = 'groq'
        agent = 'analyst'

        # Mock set_agent_active to verify calls
        with patch('src.metrics.observability.set_agent_active') as mock_set_active:
            # Mock the histogram methods
            mock_histogram = Mock()
            mock_labels = Mock()
            mock_labels.observe = Mock()
            mock_histogram.labels.return_value = mock_labels

            with patch('src.metrics.observability.llm_request_duration_seconds', mock_histogram):
                with patch('src.metrics.observability.llm_provider_latency_seconds', mock_histogram):

                    with LatencyTracker(provider, agent) as tracker:
                        assert tracker.provider == provider
                        assert tracker.agent == agent
                        assert tracker.start_time is not None

                        # Verify agent was set active
                        mock_set_active.assert_called_with(agent, True)

                        # Sleep briefly to ensure some latency is recorded
                        time.sleep(0.01)

                    # After exiting context, agent should be set inactive
                    mock_set_active.assert_called_with(agent, False)

                    # Verify latency was recorded (observe should be called)
                    assert mock_histogram.labels.return_value.observe.called

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="Prometheus client not available")
    async def test_async_latency_tracker(self):
        """Test asynchronous context manager AsyncLatencyTracker"""
        provider = 'gemini'
        agent = 'researcher'

        # Mock set_agent_active to verify calls
        with patch('src.metrics.observability.set_agent_active') as mock_set_active:
            # Mock the histogram methods
            mock_histogram = Mock()
            mock_labels = Mock()
            mock_labels.observe = Mock()
            mock_histogram.labels.return_value = mock_labels

            with patch('src.metrics.observability.llm_request_duration_seconds', mock_histogram):
                with patch('src.metrics.observability.llm_provider_latency_seconds', mock_histogram):

                    async with AsyncLatencyTracker(provider, agent) as tracker:
                        assert tracker.provider == provider
                        assert tracker.agent == agent
                        assert tracker.start_time is not None

                        # Verify agent was set active
                        mock_set_active.assert_called_with(agent, True)

                        # Sleep briefly to ensure some latency is recorded
                        await asyncio.sleep(0.01)

                    # After exiting context, agent should be set inactive
                    mock_set_active.assert_called_with(agent, False)

                    # Verify latency was recorded (observe should be called)
                    assert mock_histogram.labels.return_value.observe.called


class TestGracefulDegradation:
    """Test graceful degradation when Prometheus is not available"""

    @pytest.mark.skipif(PROMETHEUS_AVAILABLE, reason="Prometheus is available")
    def test_latency_without_prometheus(self):
        """Should gracefully handle Prometheus unavailability"""
        # This test only runs when Prometheus is not available
        # Import the module (it should have None values for metrics)
        from src.metrics import observability

        # These should not raise exceptions even when metrics are None
        observability.record_latency('groq', 'analyst', 2.5)
        observability.record_provider_latency('groq', 1.8)

        # Context managers should still work (just won't record metrics)
        with observability.LatencyTracker('groq', 'analyst') as tracker:
            time.sleep(0.01)

        # Async context manager should also work
        async def test_async():
            async with observability.AsyncLatencyTracker('gemini', 'researcher'):
                await asyncio.sleep(0.01)

        asyncio.run(test_async())

        # Check stats show Prometheus unavailable
        stats = observability.get_observability_stats()
        assert stats['prometheus_available'] is False
        assert stats['latency_metrics'] is False

    def test_get_observability_stats(self):
        """Should return correct observability status"""
        stats = get_observability_stats()

        assert 'prometheus_available' in stats
        assert 'latency_metrics' in stats
        assert 'token_metrics' in stats
        assert 'agent_metrics' in stats

        # All should be True if Prometheus is available
        if PROMETHEUS_AVAILABLE:
            assert stats['prometheus_available'] is True
            assert stats['latency_metrics'] is True
        else:
            assert stats['prometheus_available'] is False
            assert stats['latency_metrics'] is False


class TestErrorHandling:
    """Test error handling in latency tracking"""

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="Prometheus client not available")
    def test_context_manager_with_exception(self):
        """Should still record latency even if exception occurs"""
        provider = 'groq'
        agent = 'analyst'

        # Mock set_agent_active to verify calls
        with patch('src.metrics.observability.set_agent_active') as mock_set_active:
            # Mock the histogram methods
            mock_histogram = Mock()
            mock_labels = Mock()
            mock_labels.observe = Mock()
            mock_histogram.labels.return_value = mock_labels

            with patch('src.metrics.observability.llm_request_duration_seconds', mock_histogram):
                with patch('src.metrics.observability.llm_provider_latency_seconds', mock_histogram):

                    try:
                        with LatencyTracker(provider, agent):
                            time.sleep(0.01)
                            raise ValueError("Test exception")
                    except ValueError:
                        pass  # Expected exception

                    # Latency should still be recorded despite exception
                    assert mock_histogram.labels.return_value.observe.called

                    # Agent should be set inactive even on exception
                    mock_set_active.assert_called_with(agent, False)

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="Prometheus client not available")
    async def test_async_context_manager_with_exception(self):
        """Should still record latency even if async exception occurs"""
        provider = 'gemini'
        agent = 'researcher'

        # Mock set_agent_active to verify calls
        with patch('src.metrics.observability.set_agent_active') as mock_set_active:
            # Mock the histogram methods
            mock_histogram = Mock()
            mock_labels = Mock()
            mock_labels.observe = Mock()
            mock_histogram.labels.return_value = mock_labels

            with patch('src.metrics.observability.llm_request_duration_seconds', mock_histogram):
                with patch('src.metrics.observability.llm_provider_latency_seconds', mock_histogram):

                    try:
                        async with AsyncLatencyTracker(provider, agent):
                            await asyncio.sleep(0.01)
                            raise ValueError("Test async exception")
                    except ValueError:
                        pass  # Expected exception

                    # Latency should still be recorded despite exception
                    assert mock_histogram.labels.return_value.observe.called

                    # Agent should be set inactive even on exception
                    mock_set_active.assert_called_with(agent, False)
