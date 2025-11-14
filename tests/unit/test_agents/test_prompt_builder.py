"""
Unit tests for System Prompt Builder
Story 1.4: System Prompt Builder - Tests
"""

import pytest
from src.agents.prompt_builder import SystemPromptBuilder, build_system_prompt
from src.agents.parser import parse_agent_file


class TestSystemPromptBuilder:
    """Test suite for SystemPromptBuilder"""
    
    @pytest.fixture
    def builder(self):
        """Create builder instance"""
        return SystemPromptBuilder()
    
    @pytest.fixture
    def analyst_agent(self):
        """Load real analyst agent"""
        return parse_agent_file(".bmad/bmm/agents/analyst.md")
    
    @pytest.fixture
    def user_config(self):
        """Sample user config"""
        return {
            "communication_language": "PT-BR",
            "user_name": "Dani"
        }
    
    def test_build_complete_prompt(self, builder, analyst_agent, user_config):
        """Test building complete system prompt"""
        # Act
        prompt = builder.build(analyst_agent, user_config)
        
        # Assert
        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Should be substantial
        
        # Check key components present
        assert "Mary" in prompt
        assert "Business Analyst" in prompt
        assert "PERSONA:" in prompt
        assert "MENU:" in prompt
        assert "RULES:" in prompt
    
    def test_intro_section(self, builder, analyst_agent):
        """Test introduction includes name and title"""
        # Act
        intro = builder._build_intro(analyst_agent)
        
        # Assert
        assert "Mary" in intro
        assert "Business Analyst" in intro
        assert intro.startswith("You are")
    
    def test_persona_section(self, builder, analyst_agent):
        """Test persona section includes all fields"""
        # Act
        persona_text = builder._build_persona(analyst_agent)
        
        # Assert
        assert "PERSONA:" in persona_text
        assert "Role:" in persona_text
        assert "Identity:" in persona_text
        assert "Communication Style:" in persona_text
        assert "Principles:" in persona_text
    
    def test_menu_section(self, builder, analyst_agent):
        """Test menu section is numbered"""
        # Act
        menu_text = builder._build_menu(analyst_agent)
        
        # Assert
        assert "MENU:" in menu_text
        assert "1." in menu_text  # First item
        # Should have menu items
        assert len(menu_text.split('\n')) > 1
    
    def test_rules_section(self, builder, user_config):
        """Test rules include user config"""
        # Act
        rules = builder._build_rules(user_config)
        
        # Assert
        assert "RULES:" in rules
        assert "PT-BR" in rules
        assert "Dani" in rules
        assert "asterisk" in rules or "*" in rules
    
    def test_activation_reminder(self, builder, analyst_agent):
        """Test activation reminder"""
        # Act
        reminder = builder._build_activation_reminder(analyst_agent)
        
        # Assert
        assert "Mary" in reminder
        assert "NEVER break character" in reminder
        assert "" in reminder  # Icon included
    
    def test_token_estimation(self, builder, analyst_agent, user_config):
        """Test token count estimation"""
        # Act
        prompt = builder.build(analyst_agent, user_config)
        tokens = builder.estimate_tokens(prompt)
        
        # Assert
        assert tokens > 0
        assert tokens < 4000  # AC requirement: < 4000 tokens
        # Rough check: typical prompt is 400-3000 tokens (compact is better!)
        assert 200 < tokens < 4000, f"Token estimate {tokens} out of expected range"
    
    def test_build_without_menu(self, builder, analyst_agent, user_config):
        """Test building prompt without menu (compact mode)"""
        # Act
        prompt = builder.build(analyst_agent, user_config, include_menu=False)
        
        # Assert
        assert "Mary" in prompt
        assert "PERSONA:" in prompt
        # Menu should NOT be included
        assert "MENU:" not in prompt or len(prompt.split("MENU:")[1].split("\n")) < 3
    
    def test_convenience_function(self, analyst_agent, user_config):
        """Test build_system_prompt convenience function"""
        # Act
        prompt = build_system_prompt(analyst_agent, user_config)
        
        # Assert
        assert isinstance(prompt, str)
        assert "Mary" in prompt
        assert "PERSONA:" in prompt
    
    def test_multiple_agents_unique_prompts(self, builder):
        """Test different agents generate different prompts"""
        # Arrange
        analyst = parse_agent_file(".bmad/bmm/agents/analyst.md")
        pm = parse_agent_file(".bmad/bmm/agents/pm.md")
        
        config = {"communication_language": "PT-BR", "user_name": "Dani"}
        
        # Act
        prompt_analyst = builder.build(analyst, config)
        prompt_pm = builder.build(pm, config)
        
        # Assert
        assert prompt_analyst != prompt_pm
        assert "Mary" in prompt_analyst
        assert "John" in prompt_pm
        assert "Business Analyst" in prompt_analyst
        assert "Product Manager" in prompt_pm


