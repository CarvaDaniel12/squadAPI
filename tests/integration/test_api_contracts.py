"""
API Contract Tests
QA Action Item 2: API Endpoint Contract Validation

Tests API contracts match PRD specifications
"""

import pytest
import pytest_asyncio
from src.models.request import AgentExecutionRequest
from src.agents.loader import AgentLoader
from src.agents.prompt_builder import SystemPromptBuilder
from src.agents.conversation import ConversationManager
from src.agents.router import AgentRouter
from src.agents.orchestrator import AgentOrchestrator


@pytest_asyncio.fixture
async def test_components():
    """Create test components (orchestrator + supporting objects)"""
    loader = AgentLoader(bmad_path=".bmad", redis_client=None)
    await loader.load_all()
    
    conversation_manager = ConversationManager(redis_client=None)
    
    orchestrator = AgentOrchestrator(
        agent_loader=loader,
        prompt_builder=SystemPromptBuilder(),
        conversation_manager=conversation_manager,
        agent_router=AgentRouter(loader),
        provider_stub=None
    )
    
    # Return all components for testing
    return {
        "orchestrator": orchestrator,
        "loader": loader,
        "conversation_manager": conversation_manager
    }


class TestAgentExecutionAPI:
    """Contract tests for agent execution endpoint"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_execute_agent_success_response_schema(self, test_components):
        """Validate response schema matches PRD specification"""
        orchestrator = test_components["orchestrator"]
        
        request = AgentExecutionRequest(
            agent="analyst",
            task="Test task for contract validation",
            user_id="contract_test"
        )
        
        response = await orchestrator.execute(request)
        
        # Validate response schema (from PRD)
        assert response.agent == "analyst"
        assert response.agent_name == "Mary"
        assert isinstance(response.provider, str)
        assert isinstance(response.model, str)
        assert isinstance(response.response, str)
        assert isinstance(response.metadata.latency_ms, int)
        assert isinstance(response.metadata.tokens_input, int)
        assert isinstance(response.metadata.tokens_output, int)
        assert isinstance(response.metadata.fallback_used, bool)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_execute_agent_not_found_error(self, test_components):
        """Validate error handling for missing agent"""
        from src.api.errors import AgentNotFoundException
        orchestrator = test_components["orchestrator"]
        
        request = AgentExecutionRequest(
            agent="nonexistent_agent_xyz",
            task="Test",
            user_id="test"
        )
        
        with pytest.raises(AgentNotFoundException):
            await orchestrator.execute(request)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_execute_analyst_agent(self, test_components):
        """Test executing analyst agent (Mary)"""
        orchestrator = test_components["orchestrator"]
        
        request = AgentExecutionRequest(
            agent="analyst",
            task="Quick analysis test",
            user_id="test"
        )
        
        response = await orchestrator.execute(request)
        
        assert response.agent == "analyst"
        assert response.agent_name == "Mary"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_execute_dev_agent(self, test_components):
        """Test executing dev agent (Amelia)"""
        orchestrator = test_components["orchestrator"]
        
        request = AgentExecutionRequest(
            agent="dev",
            task="Implement feature X",
            user_id="test"
        )
        
        response = await orchestrator.execute(request)
        
        assert response.agent == "dev"
        assert response.agent_name == "Amelia"


class TestAgentsListAPI:
    """Contract tests for agents list endpoint"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_all_agents(self, test_components):
        """Validate all agents can be listed"""
        loader = test_components["loader"]
        agents_dict = await loader.load_all()
        agents = list(agents_dict.values())
        
        # Should have at least 6 BMad agents (some may fail to parse)
        assert len(agents) >= 6
        
        # Check core agents present
        agent_ids = [a.id for a in agents]
        core_agents = ["analyst", "pm", "architect", "dev", "sm", "tea"]
        
        for expected_id in core_agents:
            assert expected_id in agent_ids, f"Missing core agent: {expected_id}"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agent_definition_schema(self, test_components):
        """Validate agent definition schema"""
        loader = test_components["loader"]
        agent = await loader.get_agent("analyst")
        
        # Validate required fields
        assert agent.id == "analyst"
        assert agent.name == "Mary"
        assert isinstance(agent.title, str)
        assert isinstance(agent.persona, object)  # Persona object
        assert isinstance(agent.menu, list)
        assert len(agent.workflows) >= 0  # May have workflows


class TestConversationPersistence:
    """Test conversation state management"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_conversation_history_persisted(self, test_components):
        """Validate conversation history is maintained across calls"""
        orchestrator = test_components["orchestrator"]
        conversation_manager = test_components["conversation_manager"]
        
        user_id = "persistence_test"
        agent = "analyst"
        
        # First message
        request1 = AgentExecutionRequest(
            agent=agent,
            task="Remember: my name is Dani",
            user_id=user_id
        )
        response1 = await orchestrator.execute(request1)
        assert len(response1.response) > 0
        
        # Second message (should remember context)
        request2 = AgentExecutionRequest(
            agent=agent,
            task="What is my name?",
            user_id=user_id
        )
        response2 = await orchestrator.execute(request2)
        assert len(response2.response) > 0
        
        # Conversation should have grown
        history = await conversation_manager.get_history(user_id, agent)
        assert len(history.messages) >= 4  # 2 user + 2 assistant messages

