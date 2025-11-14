"""
Custom Exception Handlers
Story 1.12: Error Handling - Agent Not Found
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class AgentNotFoundException(Exception):
    """Raised when requested agent is not found"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        super().__init__(f"Agent not found: {agent_id}")


async def agent_not_found_handler(request: Request, exc: AgentNotFoundException):
    """Handle AgentNotFoundException"""
    logger.warning(f"Agent not found: {exc.agent_id}")
    
    # Get list of available agents (from orchestrator if available)
    available_agents = []
    
    return JSONResponse(
        status_code=404,
        content={
            "error": "agent_not_found",
            "message": f"Agent '{exc.agent_id}' not found",
            "agent_id": exc.agent_id,
            "available_agents": ["analyst", "pm", "architect", "dev", "sm", "tea", "tech-writer", "ux-designer"],
            "suggestion": f"Try one of the available agents. Use GET /api/v1/agents/available to see full list."
        }
    )


class AllProvidersFailed(Exception):
    """Raised when all providers in fallback chain fail"""
    
    def __init__(self, agent_id: str, details: dict):
        self.agent_id = agent_id
        self.details = details
        super().__init__(f"All providers failed for agent '{agent_id}'")

