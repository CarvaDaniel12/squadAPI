"""
Agent Router
Story 1.6: Agent Router Core Logic

Routes requests to appropriate agent and provider based on configuration.
Supports agent-to-provider mapping for optimal load distribution.
"""

import logging
import yaml
from typing import Optional, List
from pathlib import Path

from src.agents.loader import AgentLoader
from src.models.agent import AgentDefinition

logger = logging.getLogger(__name__)


class AgentRouter:
    """
    Routes requests to appropriate BMad agent and provider
    
    Features:
    - Agent routing (by ID)
    - Provider routing (agent-specific optimal provider)
    - Fallback chain support
    - Load balancing configuration
    """
    
    def __init__(
        self, 
        agent_loader: AgentLoader,
        routing_config_path: Optional[Path] = None
    ):
        """
        Initialize Agent Router
        
        Args:
            agent_loader: Agent loader instance
            routing_config_path: Path to agent_routing.yaml (optional)
        """
        self.loader = agent_loader
        
        # Load routing configuration
        if routing_config_path is None:
            routing_config_path = Path("config/agent_routing.yaml")
        
        self.routing_config = {}
        self.default_routing = {'primary': 'groq', 'fallback': ['cerebras', 'gemini', 'openrouter']}
        
        if routing_config_path.exists():
            try:
                with open(routing_config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    self.routing_config = config or {}
                logger.info(f"Loaded agent routing config: {len(self.routing_config)} agent mappings")
            except Exception as e:
                logger.warning(f"Failed to load routing config: {e}, using defaults")
        else:
            logger.info("No routing config found, using defaults")
    
    async def route(self, agent_id: str) -> Optional[AgentDefinition]:
        """
        Route request to agent by ID
        
        Args:
            agent_id: Agent identifier (e.g., 'analyst', 'pm', 'architect')
            
        Returns:
            AgentDefinition if found, None if not found
        """
        agent = await self.loader.get_agent(agent_id)
        
        if agent is None:
            logger.warning(f"Agent not found: {agent_id}")
            return None
        
        logger.info(f"Routed to agent: {agent_id} ({agent.name} - {agent.title})")
        return agent
    
    def get_provider_for_agent(self, agent_id: str) -> str:
        """
        Get optimal provider for an agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Provider name (e.g., 'groq', 'cerebras')
        """
        # Get agent-specific routing
        agent_routing = self.routing_config.get(agent_id)
        
        if agent_routing and isinstance(agent_routing, dict):
            primary = agent_routing.get('primary')
            if primary:
                logger.debug(f"Routing {agent_id}  {primary} (configured)")
                return primary
        
        # Use default routing
        default = self.routing_config.get('default', self.default_routing)
        primary = default.get('primary', 'groq')
        
        logger.debug(f"Routing {agent_id}  {primary} (default)")
        return primary
    
    def get_fallback_chain(self, agent_id: str) -> List[str]:
        """
        Get fallback chain for an agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of provider names in fallback order
        """
        # Get agent-specific routing
        agent_routing = self.routing_config.get(agent_id)
        
        if agent_routing and isinstance(agent_routing, dict):
            primary = agent_routing.get('primary', 'groq')
            fallback = agent_routing.get('fallback', [])
            
            # Build complete chain: [primary] + fallback
            chain = [primary] + fallback
            logger.debug(f"Fallback chain for {agent_id}: {chain}")
            return chain
        
        # Use default
        default = self.routing_config.get('default', self.default_routing)
        primary = default.get('primary', 'groq')
        fallback = default.get('fallback', ['cerebras', 'gemini', 'openrouter'])
        
        chain = [primary] + fallback
        logger.debug(f"Fallback chain for {agent_id}: {chain} (default)")
        return chain
    
    def list_available_agents(self) -> list[dict]:
        """
        List all available agents
        
        Returns:
            List of agent summaries (id, name, title, icon)
        """
        agents = self.loader.list_agents()
        
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "title": agent.title,
                "icon": agent.icon,
                "workflows": agent.workflows
            }
            for agent in agents.values()
        ]


