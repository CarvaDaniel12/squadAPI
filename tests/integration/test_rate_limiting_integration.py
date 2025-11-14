"""
Integration Tests for Rate Limiting in Orchestrator

Tests that rate limiting is properly integrated into agent execution flow.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock

from src.agents.loader import AgentLoader
from src.agents.prompt_builder import SystemPromptBuilder
from src.agents.conversation import ConversationManager
from src.agents.router import AgentRouter
from src.agents.orchestrator import AgentOrchestrator
from src.rate_limit.combined import CombinedRateLimiter
from src.rate_limit.semaphore import GlobalSemaphore
from src.models.request import AgentExecutionRequest
from src.models.rate_limit import ProviderRateLimitConfig


@pytest.mark.integration
@pytest.mark.asyncio
class TestRateLimitingIntegration:
    """Test rate limiting integration with orchestrator"""
    
    async def test_orchestrator_with_rate_limiting(self):
        """Should execute agent with rate limiting enabled"""
        # Setup
        loader = AgentLoader(bmad_path=".bmad", redis_client=None)
        await loader.load_all()
        
        # Create rate limiter and register provider
        rate_limiter = CombinedRateLimiter(redis_client=None)
        config = ProviderRateLimitConfig(rpm=60, tpm=20000, burst=10, window_size=60)
        rate_limiter.register_provider('stub', config)
        
        # Create semaphore
        semaphore = GlobalSemaphore(max_concurrent=5)
        
        # Create stub provider
        stub_provider = AsyncMock()
        stub_provider.call = AsyncMock(return_value={
            "content": "Test response",
            "tokens_input": 100,
            "tokens_output": 50
        })
        
        # Create orchestrator with rate limiting
        orchestrator = AgentOrchestrator(
            agent_loader=loader,
            prompt_builder=SystemPromptBuilder(),
            conversation_manager=ConversationManager(redis_client=None),
            agent_router=AgentRouter(loader),
            rate_limiter=rate_limiter,
            global_semaphore=semaphore,
            provider_stub=stub_provider
        )
        
        # Execute agent
        request = AgentExecutionRequest(
            agent="analyst",
            task="Test task",
            user_id="test-user"
        )
        
        response = await orchestrator.execute(request)
        
        # Verify response
        assert response is not None
        assert response.response == "Test response"
        assert stub_provider.call.called
        
        # Verify rate limiter state
        state = await rate_limiter.get_state('stub')
        assert state['window_count'] == 1  # One request made
        
        # Verify semaphore stats
        stats = semaphore.get_stats()
        assert stats['total_acquired'] == 1
    
    async def test_concurrent_requests_limited_by_semaphore(self):
        """Should limit concurrent requests via semaphore"""
        # Setup
        loader = AgentLoader(bmad_path=".bmad", redis_client=None)
        await loader.load_all()
        
        # Create semaphore with low capacity
        semaphore = GlobalSemaphore(max_concurrent=2)
        
        # Create slow stub provider
        async def slow_call(messages):
            await asyncio.sleep(0.1)  # Simulate slow LLM
            return {"content": "Response", "tokens_input": 10, "tokens_output": 10}
        
        stub_provider = AsyncMock()
        stub_provider.call = slow_call
        
        # Create orchestrator
        orchestrator = AgentOrchestrator(
            agent_loader=loader,
            prompt_builder=SystemPromptBuilder(),
            conversation_manager=ConversationManager(redis_client=None),
            agent_router=AgentRouter(loader),
            rate_limiter=None,  # No rate limiting, just semaphore
            global_semaphore=semaphore,
            provider_stub=stub_provider
        )
        
        # Execute 5 concurrent requests
        async def execute_one(i):
            request = AgentExecutionRequest(
                agent="analyst",
                task=f"Task {i}",
                user_id=f"user-{i}"
            )
            return await orchestrator.execute(request)
        
        start = time.time()
        results = await asyncio.gather(*[execute_one(i) for i in range(5)])
        elapsed = time.time() - start
        
        # Verify all completed
        assert len(results) == 5
        
        # With max_concurrent=2 and 0.1s per request:
        # First 2 run immediately (0.1s)
        # Next 2 run after first 2 complete (0.2s total)
        # Last 1 runs after first 4 complete (0.3s total)
        # So total time should be >= 0.3s (with some tolerance)
        assert elapsed >= 0.25
        
        # Verify semaphore stats
        stats = semaphore.get_stats()
        assert stats['total_acquired'] == 5
    
    async def test_rate_limiter_enforces_window(self):
        """Should enforce rate limit window"""
        # Setup
        loader = AgentLoader(bmad_path=".bmad", redis_client=None)
        await loader.load_all()
        
        # Create rate limiter with strict limits
        rate_limiter = CombinedRateLimiter(redis_client=None)
        config = ProviderRateLimitConfig(
            rpm=3,  # Only 3 requests per minute
            tpm=10000,
            burst=2,  # 2 burst capacity
            window_size=10  # 10 second window
        )
        rate_limiter.register_provider('stub', config)
        
        # Create stub provider
        stub_provider = AsyncMock()
        stub_provider.call = AsyncMock(return_value={
            "content": "Response",
            "tokens_input": 10,
            "tokens_output": 10
        })
        
        # Create orchestrator
        orchestrator = AgentOrchestrator(
            agent_loader=loader,
            prompt_builder=SystemPromptBuilder(),
            conversation_manager=ConversationManager(redis_client=None),
            agent_router=AgentRouter(loader),
            rate_limiter=rate_limiter,
            global_semaphore=None,  # No semaphore limit
            provider_stub=stub_provider
        )
        
        # Execute 3 requests (at limit)
        for i in range(3):
            request = AgentExecutionRequest(
                agent="analyst",
                task=f"Task {i}",
                user_id="test-user"
            )
            await orchestrator.execute(request)
        
        # Verify rate limiter state
        state = await rate_limiter.get_state('stub')
        assert state['window_count'] == 3
        assert state['is_limited'] is True  # At capacity
    
    async def test_orchestrator_without_rate_limiting(self):
        """Should work without rate limiting (fallback mode)"""
        # Setup
        loader = AgentLoader(bmad_path=".bmad", redis_client=None)
        await loader.load_all()
        
        # Create stub provider
        stub_provider = AsyncMock()
        stub_provider.call = AsyncMock(return_value={
            "content": "Response",
            "tokens_input": 10,
            "tokens_output": 10
        })
        
        # Create orchestrator WITHOUT rate limiting
        orchestrator = AgentOrchestrator(
            agent_loader=loader,
            prompt_builder=SystemPromptBuilder(),
            conversation_manager=ConversationManager(redis_client=None),
            agent_router=AgentRouter(loader),
            rate_limiter=None,
            global_semaphore=None,
            provider_stub=stub_provider
        )
        
        # Execute agent
        request = AgentExecutionRequest(
            agent="analyst",
            task="Test task",
            user_id="test-user"
        )
        
        response = await orchestrator.execute(request)
        
        # Should still work (no rate limiting)
        assert response is not None
        assert response.response == "Response"

