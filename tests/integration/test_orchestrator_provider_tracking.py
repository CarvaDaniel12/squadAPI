"""Integration tests for Orchestrator + Provider Status Tracking (Story 9.5)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from src.agents.orchestrator import AgentOrchestrator
from src.agents.loader import AgentLoader
from src.agents.prompt_builder import SystemPromptBuilder
from src.agents.conversation import ConversationManager
from src.agents.router import AgentRouter
from src.metrics.provider_status import ProviderStatusTracker, ProviderStatusEnum
from src.models.request import AgentExecutionRequest
from src.models.provider import LLMResponse


@pytest.fixture
def provider_tracker():
    """Create a provider status tracker."""
    return ProviderStatusTracker()


@pytest.fixture
async def mock_orchestrator(provider_tracker):
    """Create orchestrator with mocked dependencies."""
    loader = AsyncMock(spec=AgentLoader)
    prompt_builder = AsyncMock(spec=SystemPromptBuilder)
    conversation_manager = AsyncMock(spec=ConversationManager)
    router = AsyncMock(spec=AgentRouter)

    orchestrator = AgentOrchestrator(
        agent_loader=loader,
        prompt_builder=prompt_builder,
        conversation_manager=conversation_manager,
        agent_router=router,
        provider_status_tracker=provider_tracker,
    )

    return orchestrator, {
        "loader": loader,
        "prompt_builder": prompt_builder,
        "conversation_manager": conversation_manager,
        "router": router,
    }


class TestOrchestratorProviderTracking:
    """Tests for orchestrator integration with provider tracking."""

    @pytest.mark.asyncio
    async def test_orchestrator_records_success_metrics(self, mock_orchestrator):
        """Test that orchestrator records successful request metrics."""
        orchestrator, mocks = mock_orchestrator
        tracker = orchestrator.provider_status_tracker

        # Setup mocks
        from src.models.agent import Agent
        agent = Agent(
            name="test_agent",
            title="Test Agent",
            role="test",
            instructions="test",
            available_tools=[],
        )
        mocks["loader"].get_agent.return_value = agent
        mocks["router"].get_provider_for_agent.return_value = "groq"

        # Mock provider response
        provider_response = LLMResponse(
            provider="groq",
            model="llama-3.3-70b-versatile",
            content="Test response",
            tokens_input=10,
            tokens_output=5,
        )

        # Create mock provider
        mock_provider = AsyncMock()
        mock_provider.call.return_value = provider_response
        orchestrator.providers = {"groq": mock_provider}

        # Execute request
        request = AgentExecutionRequest(
            agent="test_agent",
            user_id="user1",
            conversation_id="conv1",
            task="What is 2+2?"
        )

        # Patch conversation methods
        with patch.object(mocks["conversation_manager"], "add_message", new_callable=AsyncMock):
            response = await orchestrator.execute(request)

        # Verify metrics were recorded
        assert tracker.providers["groq"].total_requests == 1
        assert tracker.providers["groq"].total_failures == 0
        assert len(tracker.providers["groq"].latencies) == 1
        assert tracker.providers["groq"].latencies[0] >= 0

    @pytest.mark.asyncio
    async def test_orchestrator_records_failure_metrics(self, mock_orchestrator):
        """Test that orchestrator records failed request metrics."""
        orchestrator, mocks = mock_orchestrator
        tracker = orchestrator.provider_status_tracker

        # Setup mocks
        from src.models.agent import Agent
        agent = Agent(
            name="test_agent",
            title="Test Agent",
            role="test",
            instructions="test",
            available_tools=[],
        )
        mocks["loader"].get_agent.return_value = agent
        mocks["router"].get_provider_for_agent.return_value = "groq"

        # Create mock provider that raises error
        mock_provider = AsyncMock()
        mock_provider.call.side_effect = Exception("Connection timeout")
        orchestrator.providers = {"groq": mock_provider}

        # Execute request
        request = AgentExecutionRequest(
            agent="test_agent",
            user_id="user1",
            conversation_id="conv1",
            task="What is 2+2?"
        )

        # Patch conversation methods
        with patch.object(mocks["conversation_manager"], "add_message", new_callable=AsyncMock):
            with pytest.raises(Exception):
                await orchestrator.execute(request)

        # Verify failure metrics were recorded
        assert tracker.providers["groq"].total_requests == 1
        assert tracker.providers["groq"].total_failures == 1
        assert tracker.providers["groq"].last_error == "Connection timeout"
        assert tracker.providers["groq"].last_error_time is not None

    @pytest.mark.asyncio
    async def test_orchestrator_records_rate_limit_metrics(self, mock_orchestrator):
        """Test that orchestrator records rate limit (429) errors."""
        orchestrator, mocks = mock_orchestrator
        tracker = orchestrator.provider_status_tracker

        # Setup mocks
        from src.models.agent import Agent
        agent = Agent(
            name="test_agent",
            title="Test Agent",
            role="test",
            instructions="test",
            available_tools=[],
        )
        mocks["loader"].get_agent.return_value = agent
        mocks["router"].get_provider_for_agent.return_value = "groq"

        # Create mock provider that raises 429 error
        mock_provider = AsyncMock()
        mock_provider.call.side_effect = Exception("HTTP 429: Too Many Requests")
        orchestrator.providers = {"groq": mock_provider}

        # Execute request
        request = AgentExecutionRequest(
            agent="test_agent",
            user_id="user1",
            conversation_id="conv1",
            task="What is 2+2?"
        )

        # Patch conversation methods
        with patch.object(mocks["conversation_manager"], "add_message", new_callable=AsyncMock):
            with pytest.raises(Exception):
                await orchestrator.execute(request)

        # Verify rate limit was recorded
        assert tracker.providers["groq"].last_429_time is not None

    def test_provider_status_after_orchestrator_execution(self, provider_tracker):
        """Test that provider status is calculated correctly after execution."""
        # Simulate successful requests
        for i in range(5):
            provider_tracker.record_request("groq", latency_ms=100 + i*10, success=True)

        # Simulate one failure
        provider_tracker.record_request("groq", latency_ms=5000, success=False, error="Timeout")

        # Simulate rate limit
        provider_tracker.record_rate_limit("groq")

        # Set RPM
        provider_tracker.set_rpm_current("groq", 15)

        # Get status with mock config
        config = {"rpm_limit": 30, "enabled": True, "model": "llama-3.3-70b"}
        status = provider_tracker.get_status("groq", config)

        # Verify status calculation
        assert status.total_requests == 6
        assert status.total_failures == 1
        assert status.failure_rate == pytest.approx(1/6, rel=0.01)
        assert status.rpm_available == 15
        assert status.last_error == "Timeout"
        assert status.last_429_time is not None

        # Verify status is degraded (high failure rate)
        assert status.status == ProviderStatusEnum.DEGRADED
