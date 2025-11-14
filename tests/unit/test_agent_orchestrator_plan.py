"""Tests for AgentOrchestrator prompt plan execution path."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock

from src.agents.orchestrator import AgentOrchestrator
from src.models.agent import AgentDefinition, Persona
from src.models.provider import LLMResponse
from src.models.request import AgentExecutionRequest
from src.models.prompt_plan import AgileMetadata, PromptPlan, SpecialistTask


def _agent() -> AgentDefinition:
    return AgentDefinition(
        id="analyst",
        name="Mary",
        title="Senior Analyst",
        icon="",
        persona=Persona(
            role="Analyst",
            identity="Delivers insights",
            communication_style="Direct",
            principles="Data first",
        ),
        menu=[],
    )


def _agile_metadata() -> AgileMetadata:
    return AgileMetadata(
        sprint_goal="Deliver executive summary",
        backlog_item_id="BK-42",
        priority="P0",
        acceptance_criteria=["Summary references plan"],
        ceremonies=["Planning", "Daily"],
        bmad_phase="Blueprint",
        compliance_checklist=["Peer review"],
        requires_approval=True,
    )


def _prompt_plan() -> PromptPlan:
    analysis = SpecialistTask(
        id="analysis",
        role="analyst",
        provider="groq",
        expertise_context="You analyze data",
        task_prompt="Analyze the backlog",
        blocking=False,
        inputs=[],
        expected_outputs=["analysis"],
        definition_of_done=["Insights listed"],
    )
    review = SpecialistTask(
        id="review",
        role="reviewer",
        provider="groq",
        expertise_context="You review results",
        task_prompt="Review the analysis",
        blocking=False,
        inputs=["analysis"],
        expected_outputs=["review"],
        definition_of_done=["Risks noted"],
    )
    return PromptPlan(
        user_request="Summarize",
        normalized_problem="Normalized",
        agile=_agile_metadata(),
        tasks=[analysis, review],
        post_processing_prompt="Combine specialist outputs",
    )


def _sample_request() -> AgentExecutionRequest:
    return AgentExecutionRequest(
        agent="analyst",
        task="Summarize the release",
        user_id="user-1",
        conversation_id="conv-plan",
        metadata={},
    )


class _StubPromptOptimizer:
    def __init__(self, plan: PromptPlan, synthesized: str | None = None, *, raise_in_synthesize: bool = False):
        self.enabled = True
        self.optimize = AsyncMock(return_value=plan)
        if raise_in_synthesize:
            self.synthesize = AsyncMock(side_effect=NotImplementedError("not implemented"))
        else:
            self.synthesize = AsyncMock(return_value=synthesized)


@pytest.fixture
def orchestrator_dependencies():
    loader = Mock()
    loader.get_agent = AsyncMock(return_value=_agent())

    prompt_builder = Mock()
    prompt_builder.build.return_value = "System prompt"
    prompt_builder.estimate_tokens.return_value = 100

    conv_manager = Mock()
    conv_manager.get_messages = AsyncMock(return_value=[])
    conv_manager.add_message = AsyncMock()

    router = Mock()
    router.get_provider_for_agent.return_value = "groq"

    provider = Mock()
    provider.call = AsyncMock(
        side_effect=[
            LLMResponse(
                provider="groq",
                model="llama-3",
                content="analysis result",
                tokens_input=40,
                tokens_output=20,
                latency_ms=100,
                finish_reason="stop",
            ),
            LLMResponse(
                provider="groq",
                model="llama-3",
                content="review result",
                tokens_input=30,
                tokens_output=15,
                latency_ms=80,
                finish_reason="stop",
            ),
        ]
    )

    return {
        "loader": loader,
        "prompt_builder": prompt_builder,
        "conv_manager": conv_manager,
        "router": router,
        "providers": {"groq": provider},
        "provider": provider,
    }


@pytest.mark.asyncio
async def test_orchestrator_uses_prompt_optimizer_synthesis(orchestrator_dependencies):
    plan = _prompt_plan()
    optimizer = _StubPromptOptimizer(plan, synthesized="Synthesized summary")

    orchestrator = AgentOrchestrator(
        agent_loader=orchestrator_dependencies["loader"],
        prompt_builder=orchestrator_dependencies["prompt_builder"],
        conversation_manager=orchestrator_dependencies["conv_manager"],
        agent_router=orchestrator_dependencies["router"],
        providers=orchestrator_dependencies["providers"],
        prompt_optimizer=optimizer,
    )

    response = await orchestrator.execute(_sample_request())

    optimizer.optimize.assert_awaited_once()
    optimizer.synthesize.assert_awaited_once()
    assert response.response == "Synthesized summary"
    assert response.provider == "groq"
    assert response.metadata.tokens_input == 70
    assert response.metadata.tokens_output == 35

    # Provider should have been invoked for every task in the plan
    assert orchestrator_dependencies["provider"].call.await_count == 2


@pytest.mark.asyncio
async def test_orchestrator_falls_back_when_synthesis_unavailable(orchestrator_dependencies):
    plan = _prompt_plan()
    optimizer = _StubPromptOptimizer(plan, synthesized=None, raise_in_synthesize=True)

    orchestrator = AgentOrchestrator(
        agent_loader=orchestrator_dependencies["loader"],
        prompt_builder=orchestrator_dependencies["prompt_builder"],
        conversation_manager=orchestrator_dependencies["conv_manager"],
        agent_router=orchestrator_dependencies["router"],
        providers=orchestrator_dependencies["providers"],
        prompt_optimizer=optimizer,
    )

    response = await orchestrator.execute(_sample_request())

    optimizer.optimize.assert_awaited_once()
    optimizer.synthesize.assert_awaited_once()
    assert "Task analysis (groq)" in response.response
    assert "Task review (groq)" in response.response
