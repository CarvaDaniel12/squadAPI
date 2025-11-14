"""
Agent Loader Service
Story 1.3: Agent Loader Service

Loads all BMad agents on startup and caches in Redis
"""

from pathlib import Path
from typing import Dict, Optional
import logging

import redis.asyncio as redis

from src.agents.parser import AgentParser
from src.models.agent import AgentDefinition

logger = logging.getLogger(__name__)


class AgentLoader:
    """Loads and caches BMad agent definitions"""
    
    def __init__(self, bmad_path: str | Path, redis_client: Optional[redis.Redis] = None):
        """
        Initialize Agent Loader
        
        Args:
            bmad_path: Path to .bmad directory
            redis_client: Redis client for caching (optional for testing)
        """
        self.bmad_path = Path(bmad_path)
        self.redis = redis_client
        self.parser = AgentParser()
        self._agents: Dict[str, AgentDefinition] = {}
    
    async def load_all(self) -> Dict[str, AgentDefinition]:
        """
        Load all BMad agents from filesystem
        
        Scans .bmad/bmm/agents/*.md and parses each agent
        Caches in Redis with 1 hour TTL
        
        Returns:
            Dict[agent_id, AgentDefinition]: All loaded agents
        """
        agents_dir = self.bmad_path / "bmm" / "agents"
        
        if not agents_dir.exists():
            raise FileNotFoundError(f"Agents directory not found: {agents_dir}")
        
        agents = {}
        loaded_count = 0
        
        for file in agents_dir.glob("*.md"):
            # Skip meta files
            if file.stem in ['README', 'index']:
                continue
            
            try:
                agent = self.parser.parse(file)
                agents[agent.id] = agent
                loaded_count += 1
                
                # Cache in Redis (if available)
                if self.redis:
                    await self._cache_agent(agent)
                
                logger.info(f"Loaded agent: {agent.id} ({agent.name} - {agent.title})")
            
            except Exception as e:
                logger.error(f"Failed to parse agent file {file}: {e}")
                continue
        
        self._agents = agents
        logger.info(f"Loaded {loaded_count} BMad agents")
        
        return agents
    
    async def _cache_agent(self, agent: AgentDefinition):
        """Cache agent definition in Redis with 1 hour TTL"""
        try:
            key = f"agent:{agent.id}"
            value = agent.model_dump_json()
            await self.redis.setex(key, 3600, value)  # 1 hour TTL
        except Exception as e:
            logger.warning(f"Failed to cache agent {agent.id} in Redis: {e}")
    
    async def get_agent(self, agent_id: str) -> Optional[AgentDefinition]:
        """
        Get agent by ID (from cache or filesystem)
        
        Args:
            agent_id: Agent ID (e.g., 'analyst')
            
        Returns:
            AgentDefinition if found, None otherwise
        """
        # Try Redis cache first
        if self.redis:
            try:
                cached = await self.redis.get(f"agent:{agent_id}")
                if cached:
                    return AgentDefinition.model_validate_json(cached)
            except Exception as e:
                logger.warning(f"Redis cache miss for agent {agent_id}: {e}")
        
        # Fallback to in-memory cache
        if agent_id in self._agents:
            return self._agents[agent_id]
        
        # Try loading from filesystem
        agent_file = self.bmad_path / "bmm" / "agents" / f"{agent_id}.md"
        if agent_file.exists():
            try:
                agent = self.parser.parse(agent_file)
                self._agents[agent_id] = agent
                
                if self.redis:
                    await self._cache_agent(agent)
                
                return agent
            except Exception as e:
                logger.error(f"Failed to load agent {agent_id}: {e}")
        
        return None
    
    def list_agents(self) -> Dict[str, AgentDefinition]:
        """List all loaded agents"""
        return self._agents.copy()

