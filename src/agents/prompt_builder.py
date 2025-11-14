"""
System Prompt Builder
Story 1.4: System Prompt Builder

Builds complete system prompts that transform external LLMs into BMad agents
"""

from typing import Dict, Optional
from src.models.agent import AgentDefinition, MenuItem


class SystemPromptBuilder:
    """Builds system prompts that instruct LLMs to embody BMad agents"""
    
    def build(
        self, 
        agent: AgentDefinition, 
        user_config: Optional[Dict] = None,
        include_menu: bool = True
    ) -> str:
        """
        Build complete system prompt for agent
        
        Args:
            agent: Agent definition
            user_config: User configuration (communication_language, user_name, etc.)
            include_menu: Whether to include full menu (default: True)
            
        Returns:
            Complete system prompt (3-4k tokens)
        """
        config = user_config or {}
        
        sections = [
            self._build_intro(agent),
            self._build_persona(agent),
        ]
        
        if include_menu:
            sections.append(self._build_menu(agent))
        
        sections.extend([
            self._build_rules(config),
            self._build_activation_reminder(agent)
        ])
        
        return "\n\n".join(sections)
    
    def _build_intro(self, agent: AgentDefinition) -> str:
        """Build introduction section"""
        return f"You are {agent.name}, a {agent.title}."
    
    def _build_persona(self, agent: AgentDefinition) -> str:
        """Build persona section"""
        persona = agent.persona
        
        return f"""PERSONA:
- Role: {persona.role}
- Identity: {persona.identity}
- Communication Style: {persona.communication_style}
- Principles: {persona.principles}"""
    
    def _build_menu(self, agent: AgentDefinition) -> str:
        """Build menu section"""
        if not agent.menu:
            return "MENU:\n(No menu items defined)"
        
        menu_lines = ["MENU:"]
        
        for idx, item in enumerate(agent.menu, start=1):
            cmd_part = f" ({item.cmd})" if item.cmd else ""
            desc = item.description or "Menu item"
            menu_lines.append(f"{idx}. {desc}{cmd_part}")
        
        return "\n".join(menu_lines)
    
    def _build_rules(self, user_config: Dict) -> str:
        """Build rules section from user config"""
        comm_lang = user_config.get('communication_language', 'EN')
        user_name = user_config.get('user_name', 'User')
        
        return f"""RULES:
- ALWAYS communicate in {comm_lang}
- User's name is {user_name}
- Stay in character until exit selected
- Menu triggers use asterisk (*) - NOT markdown
- Number all lists, use letters for sub-options
- Load files ONLY when executing menu items or workflows require it"""
    
    def _build_activation_reminder(self, agent: AgentDefinition) -> str:
        """Build activation reminder"""
        return f"""You must fully embody this agent's persona and follow all instructions exactly as specified.
NEVER break character until given an exit command.

Your name is {agent.name}. You are a {agent.title}. {agent.icon}"""
    
    def estimate_tokens(self, prompt: str) -> int:
        """
        Estimate token count (rough approximation)
        
        Rule of thumb: 1 token  4 characters
        
        Args:
            prompt: System prompt text
            
        Returns:
            Estimated token count
        """
        return len(prompt) // 4


# Convenience function
def build_system_prompt(
    agent: AgentDefinition, 
    user_config: Optional[Dict] = None
) -> str:
    """Build system prompt - convenience function"""
    builder = SystemPromptBuilder()
    return builder.build(agent, user_config)


