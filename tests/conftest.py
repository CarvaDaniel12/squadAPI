"""
Pytest Configuration and Fixtures
Shared fixtures for all tests
"""

import pytest
import asyncio
from src.api.agents import set_orchestrator
from src.agents.loader import AgentLoader
from src.agents.prompt_builder import SystemPromptBuilder
from src.agents.conversation import ConversationManager
from src.agents.router import AgentRouter
from src.agents.orchestrator import AgentOrchestrator


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def initialize_orchestrator():
    """
    Initialize orchestrator once for all API integration tests
    
    Note: Rate limiting disabled for tests (would slow down test suite).
    Rate limiting tests should create their own orchestrator instances.
    """
    loader = AgentLoader(bmad_path=".bmad", redis_client=None)
    await loader.load_all()
    
    orchestrator = AgentOrchestrator(
        agent_loader=loader,
        prompt_builder=SystemPromptBuilder(),
        conversation_manager=ConversationManager(redis_client=None),
        agent_router=AgentRouter(loader),
        rate_limiter=None,  # Disabled for tests (Epic 2)
        global_semaphore=None,  # Disabled for tests (Epic 2)
        provider_stub=None
    )
    
    set_orchestrator(orchestrator)
    
    yield orchestrator

