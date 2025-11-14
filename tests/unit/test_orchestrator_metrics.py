"""
Unit tests for Agent Orchestrator metrics integration
Story 5.5: Metrics Integration - Agent Orchestrator

Tests that orchestrator correctly integrates:
- Request tracking (success/failure/429)
- Latency tracking
- Token consumption tracking
- Logging context (request_id, agent_id, provider)
"""

import pytest
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.agents.orchestrator import AgentOrchestrator
from src.models.request import AgentExecutionRequest
from src.models.response import AgentExecutionResponse
from src.models.agent import AgentDefinition
from src.models.provider import LLMResponse


@pytest.fixture
def mock_agent():
    """Mock agent definition"""
    return AgentDefinition(
        id="analyst",
        name="Mary",
        title="Senior Data Analyst",
        icon="",
        persona={
            "role": "Data Analyst",
            "identity": "Senior analyst",
            "communication_style": "Direct",
            "principles": "Data-driven"
        },
        menu=[]
    )


@pytest.fixture
def mock_components(mock_agent):
    """Mock all orchestrator components"""
    loader = Mock()
    loader.get_agent = AsyncMock(return_value=mock_agent)

    prompt_builder = Mock()
    prompt_builder.build.return_value = "System prompt"
    prompt_builder.estimate_tokens.return_value = 100

    conv_manager = Mock()
    conv_manager.get_messages = AsyncMock(return_value=[])
    conv_manager.add_message = AsyncMock()

    router = Mock()
    router.get_provider_for_agent.return_value = "groq"

    # Mock provider
    provider = Mock()
    provider.call = AsyncMock(return_value=LLMResponse(
        provider="groq",
        model="llama-3.1-70b",
        content="Analysis complete",
        tokens_input=150,
        tokens_output=50,
        latency_ms=250,
        finish_reason="stop"
    ))

    providers = {"groq": provider}

    return {
        "loader": loader,
        "prompt_builder": prompt_builder,
        "conv_manager": conv_manager,
        "router": router,
        "providers": providers
    }


@pytest.fixture
def orchestrator(mock_components):
    """Create orchestrator with mocked components"""
    return AgentOrchestrator(
        agent_loader=mock_components["loader"],
        prompt_builder=mock_components["prompt_builder"],
        conversation_manager=mock_components["conv_manager"],
        agent_router=mock_components["router"],
        providers=mock_components["providers"]
    )


@pytest.fixture
def sample_request():
    """Sample agent execution request"""
    return AgentExecutionRequest(
        agent="analyst",
        prompt="Analyze this data",
        user_id="user-123",
        conversation_id="conv-unit-test",
        metadata={"channel": "unit-test"}
    )


class TestMetricsIntegration:
    """Test metrics are correctly tracked"""

    @pytest.mark.asyncio
    async def test_success_metrics_recorded(self, orchestrator, sample_request):
        """Should record success metrics on successful execution"""
        with patch('src.agents.orchestrator.record_request_success') as mock_success, \
             patch('src.agents.orchestrator.record_latency') as mock_latency, \
             patch('src.agents.orchestrator.record_tokens') as mock_tokens:

            response = await orchestrator.execute(sample_request)

            # Verify success metric called
            mock_success.assert_called_once_with(
                provider="groq",
                agent="analyst"
            )

            # Verify latency metric called
            mock_latency.assert_called_once()
            call_args = mock_latency.call_args
            assert call_args[0][0] == "groq"  # provider
            assert call_args[0][1] == "analyst"  # agent
            assert isinstance(call_args[0][2], float)  # duration in seconds

            # Verify tokens metric called
            mock_tokens.assert_called_once_with(
                "groq",
                150,  # tokens_in
                50    # tokens_out
            )

    @pytest.mark.asyncio
    async def test_failure_metrics_recorded(self, orchestrator, sample_request, mock_components):
        """Should record failure metrics on error"""
        # Make provider raise exception
        mock_components["providers"]["groq"].call = AsyncMock(
            side_effect=Exception("API Error")
        )

        with patch('src.agents.orchestrator.record_request_failure') as mock_failure, \
             patch('src.agents.orchestrator.classify_error') as mock_classify:

            mock_classify.return_value = 'api_error'

            with pytest.raises(Exception):
                await orchestrator.execute(sample_request)

            # Verify failure metric called
            mock_failure.assert_called_once_with(
                provider="groq",
                agent="analyst",
                error_type="api_error"
            )

    @pytest.mark.asyncio
    async def test_429_metrics_recorded(self, orchestrator, sample_request, mock_components):
        """Should record 429 metric on rate limit error"""
        # Make provider raise 429 error
        mock_components["providers"]["groq"].call = AsyncMock(
            side_effect=Exception("429 Rate limit exceeded")
        )

        with patch('src.agents.orchestrator.record_request_failure') as mock_failure, \
             patch('src.agents.orchestrator.record_429_error') as mock_429, \
             patch('src.agents.orchestrator.classify_error') as mock_classify:

            mock_classify.return_value = 'rate_limit'

            with pytest.raises(Exception):
                await orchestrator.execute(sample_request)

            # Verify 429 metric called
            mock_429.assert_called_once_with(provider="groq")

            # Verify failure metric also called
            mock_failure.assert_called_once_with(
                provider="groq",
                agent="analyst",
                error_type="rate_limit"
            )

    @pytest.mark.asyncio
    async def test_latency_tracking_accurate(self, orchestrator, sample_request, mock_components):
        """Should track latency accurately"""
        # Make provider take ~200ms
        async def slow_call(*args, **kwargs):
            await asyncio.sleep(0.2)
            return LLMResponse(
                provider="groq",
                model="llama-3.1-70b",
                content="Response",
                tokens_input=100,
                tokens_output=50,
                latency_ms=200,
                finish_reason="stop"
            )

        mock_components["providers"]["groq"].call = slow_call

        with patch('src.agents.orchestrator.record_latency') as mock_latency:
            start = time.time()
            await orchestrator.execute(sample_request)
            duration = time.time() - start

            # Verify latency metric called with correct duration
            mock_latency.assert_called_once()
            recorded_duration = mock_latency.call_args[0][2]

            # Should be approximately 0.2 seconds (within 50ms tolerance)
            assert abs(recorded_duration - 0.2) < 0.05


class TestLoggingContextIntegration:
    """Test logging context is correctly set/cleared"""

    @pytest.mark.asyncio
    async def test_context_set_on_request(self, orchestrator, sample_request):
        """Should set logging context at request start"""
        with patch('src.agents.orchestrator.set_request_context') as mock_set:
            await orchestrator.execute(sample_request)

            # Verify context set (may be called twice: initial + provider update)
            assert mock_set.call_count >= 1

            # Verify first call has correct structure
            first_call_args = mock_set.call_args_list[0][0]

            # request_id should be UUID
            assert len(first_call_args[0]) == 36  # UUID length with hyphens
            assert first_call_args[1] == "analyst"  # agent_id
            assert first_call_args[2] == "groq"     # provider

    @pytest.mark.asyncio
    async def test_context_cleared_on_success(self, orchestrator, sample_request):
        """Should clear logging context after success"""
        with patch('src.agents.orchestrator.clear_request_context') as mock_clear:
            await orchestrator.execute(sample_request)

            # Verify context cleared
            mock_clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_cleared_on_error(self, orchestrator, sample_request, mock_components):
        """Should clear logging context even on error (finally block)"""
        # Make provider raise exception
        mock_components["providers"]["groq"].call = AsyncMock(
            side_effect=Exception("Test error")
        )

        with patch('src.agents.orchestrator.clear_request_context') as mock_clear, \
             patch('src.agents.orchestrator.record_request_failure'), \
             patch('src.agents.orchestrator.classify_error', return_value='unknown'):

            with pytest.raises(Exception):
                await orchestrator.execute(sample_request)

            # Verify context cleared even on error
            mock_clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_id_unique_per_request(self, orchestrator, sample_request):
        """Should generate unique request_id for each request"""
        request_ids = []

        with patch('src.agents.orchestrator.set_request_context') as mock_set:
            # Execute multiple requests
            for _ in range(3):
                await orchestrator.execute(sample_request)
                request_ids.append(mock_set.call_args[0][0])

            # All request IDs should be unique
            assert len(set(request_ids)) == 3

            # All should be valid UUIDs (36 chars with hyphens)
            for req_id in request_ids:
                assert len(req_id) == 36


class TestTokenTracking:
    """Test token consumption tracking"""

    @pytest.mark.asyncio
    async def test_tokens_tracked_from_llm_response(self, orchestrator, sample_request):
        """Should track tokens from LLM response"""
        with patch('src.agents.orchestrator.record_tokens') as mock_tokens:
            await orchestrator.execute(sample_request)

            # Verify tokens tracked
            mock_tokens.assert_called_once_with(
                "groq",
                150,  # tokens_input from LLMResponse
                50    # tokens_output from LLMResponse
            )

    @pytest.mark.asyncio
    async def test_tokens_tracked_on_dict_response(self, orchestrator, sample_request, mock_components):
        """Should handle backward-compatible dict response"""
        # Mock old-style dict response
        mock_components["providers"]["groq"].call = AsyncMock(return_value={
            "content": "Response text",
            "tokens_input": 200,
            "tokens_output": 75
        })

        with patch('src.agents.orchestrator.record_tokens') as mock_tokens:
            await orchestrator.execute(sample_request)

            # Verify tokens tracked from dict
            mock_tokens.assert_called_once_with(
                "stub",  # provider name for dict response
                200,  # tokens_input from dict
                75    # tokens_output from dict
            )
# Fix missing import
import asyncio

