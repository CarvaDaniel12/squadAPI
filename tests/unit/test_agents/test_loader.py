"""
Unit tests for Agent Loader
Story 1.3: Agent Loader Service - Tests
"""

import pytest
from pathlib import Path
from src.agents.loader import AgentLoader
from src.models.agent import AgentDefinition


class TestAgentLoader:
    """Test suite for AgentLoader"""
    
    @pytest.fixture
    def loader(self):
        """Create loader instance (no Redis)"""
        return AgentLoader(bmad_path=".bmad", redis_client=None)
    
    @pytest.mark.asyncio
    async def test_load_all_agents(self, loader):
        """Test loading all BMad agents"""
        # Act
        agents = await loader.load_all()
        
        # Assert
        assert isinstance(agents, dict)
        assert len(agents) >= 1  # At least one agent should exist
        
        # Check expected agents
        expected_agents = ['analyst', 'pm', 'architect', 'dev', 'sm']
        for agent_id in expected_agents:
            assert agent_id in agents, f"Agent {agent_id} should be loaded"
            assert isinstance(agents[agent_id], AgentDefinition)
    
    @pytest.mark.asyncio
    async def test_get_agent_by_id(self, loader):
        """Test getting specific agent by ID"""
        # Arrange
        await loader.load_all()
        
        # Act
        analyst = await loader.get_agent('analyst')
        
        # Assert
        assert analyst is not None
        assert analyst.id == 'analyst'
        assert analyst.name == 'Mary'
        assert analyst.title == 'Business Analyst'
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_agent(self, loader):
        """Test getting agent that doesn't exist"""
        # Arrange
        await loader.load_all()
        
        # Act
        agent = await loader.get_agent('nonexistent_agent_xyz')
        
        # Assert
        assert agent is None
    
    def test_list_agents(self, loader):
        """Test listing all agents"""
        # Act
        agents_list = loader.list_agents()
        
        # Assert
        assert isinstance(agents_list, dict)
        # Before load_all(), should be empty
        assert len(agents_list) == 0
    
    @pytest.mark.asyncio
    async def test_agent_caching(self, loader):
        """Test in-memory caching"""
        # Arrange
        await loader.load_all()
        
        # Act - Get agent twice
        agent1 = await loader.get_agent('analyst')
        agent2 = await loader.get_agent('analyst')
        
        # Assert - Should return same instance from cache
        assert agent1 is not None
        assert agent2 is not None
        assert agent1.id == agent2.id

