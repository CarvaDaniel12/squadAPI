"""
Unit Tests for Fallback Chain Executor

Tests fallback logic with mocked providers.
"""

import pytest
from unittest.mock import AsyncMock

from src.agents.fallback import FallbackExecutor, AllProvidersFailed
from src.providers.stub_provider import StubLLMProvider
from src.models.provider import ProviderConfig, ProviderRateLimitError


@pytest.mark.unit
@pytest.mark.asyncio
class TestFallbackExecutor:
    """Test fallback executor"""
    
    async def test_get_fallback_chain_custom(self):
        """Should return custom chain for agent"""
        provider1 = StubLLMProvider()
        provider2 = StubLLMProvider()
        
        providers = {"p1": provider1, "p2": provider2}
        chains = {"agent1": ["p2", "p1"]}  # Custom order
        
        executor = FallbackExecutor(providers, chains)
        
        chain = executor.get_fallback_chain("agent1")
        
        assert chain == ["p2", "p1"]
    
    async def test_get_fallback_chain_default(self):
        """Should return default chain if not specified"""
        provider1 = StubLLMProvider()
        provider2 = StubLLMProvider()
        
        providers = {"p1": provider1, "p2": provider2}
        
        executor = FallbackExecutor(providers, {})
        
        chain = executor.get_fallback_chain("unknown_agent")
        
        assert set(chain) == {"p1", "p2"}
    
    async def test_execute_success_first_provider(self):
        """Should succeed on first provider (no fallback)"""
        provider = StubLLMProvider(fixed_response="Success")
        
        providers = {"p1": provider}
        executor = FallbackExecutor(providers, {})
        
        response = await executor.execute_with_fallback(
            agent_id="test",
            system_prompt="System",
            user_prompt="User"
        )
        
        assert response.content == "Success"
        
        stats = executor.get_stats()
        assert stats['fallback_triggered'] == 0
    
    async def test_fallback_statistics(self):
        """Should track fallback statistics"""
        executor = FallbackExecutor({}, {})
        
        stats = executor.get_stats()
        
        assert 'total_calls' in stats
        assert 'fallback_triggered' in stats
        assert 'fallback_success' in stats
        assert 'all_failed' in stats
    
    async def test_reset_stats(self):
        """Should reset statistics"""
        provider = StubLLMProvider()
        executor = FallbackExecutor({"p1": provider}, {})
        
        # Make a call
        await executor.execute_with_fallback("agent", "sys", "user")
        
        assert executor.get_stats()['total_calls'] == 1
        
        # Reset
        executor.reset_stats()
        
        assert executor.get_stats()['total_calls'] == 0

