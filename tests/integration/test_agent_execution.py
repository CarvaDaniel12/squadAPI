"""
Integration Test - Agent Execution
Story 1.11: Basic Integration Test - Agent Execution

Tests complete flow: Request  Orchestrator  Agent  Response
"""

import pytest
from src.agents.loader import AgentLoader
from src.agents.prompt_builder import SystemPromptBuilder
from src.agents.conversation import ConversationManager
from src.agents.router import AgentRouter
from src.agents.orchestrator import AgentOrchestrator
from src.models.request import AgentExecutionRequest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_agent_execution_flow():
    """Test complete agent execution flow end-to-end"""
    # Arrange - Create orchestrator with all components
    loader = AgentLoader(bmad_path=".bmad", redis_client=None)
    prompt_builder = SystemPromptBuilder()
    conv_manager = ConversationManager(redis_client=None)
    router = AgentRouter(loader)
    
    # Load agents
    agents = await loader.load_all()
    assert len(agents) >= 1, "Should load at least one agent"
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(
        agent_loader=loader,
        prompt_builder=prompt_builder,
        conversation_manager=conv_manager,
        agent_router=router,
        provider_stub=None
    )
    
    # Act - Execute agent
    request = AgentExecutionRequest(
        agent="analyst",
        task="Test task",
        user_id="test_user"
    )
    
    response = await orchestrator.execute(request)
    
    # Assert
    assert response.agent == "analyst"
    assert response.agent_name == "Mary"
    assert response.response is not None
    assert len(response.response) > 0
    assert response.metadata.latency_ms >= 0  # Can be 0 if execution < 1ms
    assert response.metadata.tokens_input > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_not_found_error():
    """Test error handling when agent doesn't exist"""
    # Arrange
    loader = AgentLoader(bmad_path=".bmad", redis_client=None)
    await loader.load_all()
    
    orchestrator = AgentOrchestrator(
        agent_loader=loader,
        prompt_builder=SystemPromptBuilder(),
        conversation_manager=ConversationManager(redis_client=None),
        agent_router=AgentRouter(loader),
        provider_stub=None
    )
    
    # Act & Assert
    from src.api.errors import AgentNotFoundException
    
    with pytest.raises(AgentNotFoundException) as exc_info:
        request = AgentExecutionRequest(
            agent="nonexistent_agent_xyz",
            task="Test",
            user_id="test"
        )
        await orchestrator.execute(request)
    
    assert exc_info.value.agent_id == "nonexistent_agent_xyz"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_conversation_history_persistence():
    """Test conversation history persists across multiple messages"""
    # Arrange
    loader = AgentLoader(bmad_path=".bmad", redis_client=None)
    await loader.load_all()
    
    conv_manager = ConversationManager(redis_client=None)
    
    orchestrator = AgentOrchestrator(
        agent_loader=loader,
        prompt_builder=SystemPromptBuilder(),
        conversation_manager=conv_manager,
        agent_router=AgentRouter(loader),
        provider_stub=None
    )
    
    # Act - Send multiple messages
    request1 = AgentExecutionRequest(agent="analyst", task="First message", user_id="test")
    request2 = AgentExecutionRequest(agent="analyst", task="Second message", user_id="test")
    
    await orchestrator.execute(request1)
    await orchestrator.execute(request2)
    
    # Get conversation history
    history = await conv_manager.get_messages("test", "analyst")
    
    # Assert - Should have 4 messages (user, assistant, user, assistant)
    assert len(history) == 4
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "First message"
    assert history[1]["role"] == "assistant"
    assert history[2]["content"] == "Second message"


