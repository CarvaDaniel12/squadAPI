"""
Unit tests for BMad Agent Parser
Story 1.1: BMad Agent File Parser - Tests
"""

import pytest
from pathlib import Path
from src.agents.parser import AgentParser, parse_agent_file
from src.models.agent import AgentDefinition, Persona, MenuItem


class TestAgentParser:
    """Test suite for AgentParser"""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance"""
        return AgentParser()
    
    @pytest.fixture
    def analyst_file(self):
        """Path to analyst agent file"""
        return Path(".bmad/bmm/agents/analyst.md")
    
    def test_parse_analyst_agent(self, parser, analyst_file):
        """Test parsing real analyst.md agent file"""
        # Arrange & Act
        agent = parser.parse(analyst_file)
        
        # Assert
        assert isinstance(agent, AgentDefinition)
        assert agent.id == "analyst"
        assert agent.name == "Mary"
        assert agent.title == "Business Analyst"
        assert agent.icon == ""
    
    def test_parse_persona(self, parser, analyst_file):
        """Test persona extraction"""
        # Act
        agent = parser.parse(analyst_file)
        
        # Assert
        assert isinstance(agent.persona, Persona)
        assert agent.persona.role is not None
        assert agent.persona.identity is not None
        assert len(agent.persona.role) > 0
    
    def test_parse_menu(self, parser, analyst_file):
        """Test menu items extraction"""
        # Act
        agent = parser.parse(analyst_file)
        
        # Assert
        assert isinstance(agent.menu, list)
        assert len(agent.menu) > 0
        
        # Check for common menu items
        menu_cmds = [item.cmd for item in agent.menu]
        assert "*help" in menu_cmds or "*exit" in menu_cmds
    
    def test_extract_workflows(self, parser, analyst_file):
        """Test workflow extraction from menu"""
        # Act
        agent = parser.parse(analyst_file)
        
        # Assert
        assert isinstance(agent.workflows, list)
        # Analyst should have research workflow at minimum
        assert any('research' in w or 'workflow' in w for w in agent.workflows)
    
    def test_parse_nonexistent_file(self, parser):
        """Test error handling for missing file"""
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            parser.parse("nonexistent_agent.md")
    
    def test_convenience_function(self, analyst_file):
        """Test parse_agent_file convenience function"""
        # Act
        agent = parse_agent_file(analyst_file)
        
        # Assert
        assert isinstance(agent, AgentDefinition)
        assert agent.id == "analyst"
    
    def test_multiple_agents(self, parser):
        """Test parsing multiple different agents"""
        agent_files = [
            ".bmad/bmm/agents/analyst.md",
            ".bmad/bmm/agents/pm.md",
            ".bmad/bmm/agents/architect.md",
            ".bmad/bmm/agents/dev.md",
        ]
        
        agents = []
        for file_path in agent_files:
            path = Path(file_path)
            if path.exists():
                agent = parser.parse(path)
                agents.append(agent)
        
        # Assert we can parse multiple agents
        assert len(agents) >= 1
        
        # Each agent has unique ID
        ids = [a.id for a in agents]
        assert len(ids) == len(set(ids)), "Agent IDs must be unique"


