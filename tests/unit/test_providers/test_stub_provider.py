"""
Unit Tests for Stub LLM Provider

Tests the fake provider used for unit testing.
"""

import pytest
import time
from src.providers.stub_provider import StubLLMProvider
from src.models.provider import ProviderConfig, LLMResponse


@pytest.mark.unit
@pytest.mark.asyncio
class TestStubLLMProvider:
    """Test stub provider functionality"""
    
    async def test_initialization_default(self):
        """Should initialize with default config"""
        stub = StubLLMProvider()
        
        assert stub.name == "stub"
        assert stub.model == "stub-model-v1"
        assert stub.call_count == 0
        assert len(stub.call_history) == 0
    
    async def test_initialization_with_config(self):
        """Should initialize with custom config"""
        config = ProviderConfig(
            name="custom-stub",
            type="stub",
            model="custom-model",
            rpm_limit=100,
            tpm_limit=10000
        )
        
        stub = StubLLMProvider(config=config)
        
        assert stub.name == "custom-stub"
        assert stub.model == "custom-model"
    
    async def test_call_echo_mode(self):
        """Should echo user prompt when no fixed response"""
        stub = StubLLMProvider(simulate_latency=False)
        
        response = await stub.call(
            system_prompt="You are helpful",
            user_prompt="Hello!"
        )
        
        assert isinstance(response, LLMResponse)
        assert "[STUB]" in response.content
        assert "Hello!" in response.content
        assert response.provider == "stub"
        assert response.finish_reason == "stop"
    
    async def test_call_fixed_response(self):
        """Should return fixed response when set"""
        stub = StubLLMProvider(
            fixed_response="This is a fixed response",
            simulate_latency=False
        )
        
        response = await stub.call(
            system_prompt="System",
            user_prompt="User"
        )
        
        assert response.content == "This is a fixed response"
    
    async def test_call_tracking(self):
        """Should track call count and history"""
        stub = StubLLMProvider(simulate_latency=False)
        
        assert stub.call_count == 0
        
        await stub.call("system1", "user1")
        assert stub.call_count == 1
        
        await stub.call("system2", "user2")
        assert stub.call_count == 2
        
        assert len(stub.call_history) == 2
        assert stub.call_history[0]['user_prompt'] == "user1"
        assert stub.call_history[1]['user_prompt'] == "user2"
    
    async def test_call_simulates_latency(self):
        """Should simulate realistic latency"""
        stub = StubLLMProvider(
            simulate_latency=True,
            latency_range=(50, 150)
        )
        
        start = time.time()
        response = await stub.call("system", "user")
        elapsed_ms = (time.time() - start) * 1000
        
        # Should have some latency
        assert elapsed_ms >= 40  # At least 40ms (with tolerance)
        assert response.latency_ms >= 40
    
    async def test_call_no_latency(self):
        """Should be fast when latency disabled"""
        stub = StubLLMProvider(simulate_latency=False)
        
        start = time.time()
        await stub.call("system", "user")
        elapsed_ms = (time.time() - start) * 1000
        
        # Should be very fast
        assert elapsed_ms < 50  # Less than 50ms
    
    async def test_health_check_healthy(self):
        """Should return True when healthy"""
        stub = StubLLMProvider()
        
        result = await stub.health_check()
        
        assert result is True
    
    async def test_health_check_unhealthy(self):
        """Should return False when set unhealthy"""
        stub = StubLLMProvider()
        
        stub.set_healthy(False)
        result = await stub.health_check()
        
        assert result is False
    
    async def test_set_fixed_response(self):
        """Should update fixed response"""
        stub = StubLLMProvider(
            fixed_response="Initial",
            simulate_latency=False
        )
        
        response1 = await stub.call("s", "u")
        assert response1.content == "Initial"
        
        stub.set_fixed_response("Updated")
        response2 = await stub.call("s", "u")
        assert response2.content == "Updated"
    
    async def test_reset(self):
        """Should reset call tracking"""
        stub = StubLLMProvider(simulate_latency=False)
        
        await stub.call("s", "u")
        await stub.call("s", "u")
        assert stub.call_count == 2
        
        stub.reset()
        
        assert stub.call_count == 0
        assert len(stub.call_history) == 0
    
    async def test_get_last_call(self):
        """Should return last call details"""
        stub = StubLLMProvider(simulate_latency=False)
        
        assert stub.get_last_call() is None
        
        await stub.call("system", "user1")
        await stub.call("system", "user2")
        
        last_call = stub.get_last_call()
        assert last_call is not None
        assert last_call['user_prompt'] == "user2"
    
    async def test_assert_called_once(self):
        """Should assert single call"""
        stub = StubLLMProvider(simulate_latency=False)
        
        await stub.call("s", "u")
        
        # Should not raise
        stub.assert_called_once()
    
    async def test_assert_called_once_fails(self):
        """Should raise when not called once"""
        stub = StubLLMProvider(simulate_latency=False)
        
        # Not called yet
        with pytest.raises(AssertionError, match="Expected 1 call"):
            stub.assert_called_once()
        
        # Called twice
        await stub.call("s", "u")
        await stub.call("s", "u")
        
        with pytest.raises(AssertionError, match="Expected 1 call"):
            stub.assert_called_once()
    
    async def test_assert_called_with(self):
        """Should assert call with specific prompt"""
        stub = StubLLMProvider(simulate_latency=False)
        
        await stub.call("system", "Hello!")
        
        # Should not raise
        stub.assert_called_with("Hello!")
    
    async def test_assert_called_with_fails(self):
        """Should raise when prompt doesn't match"""
        stub = StubLLMProvider(simulate_latency=False)
        
        await stub.call("system", "Hello!")
        
        with pytest.raises(AssertionError, match="Expected user_prompt"):
            stub.assert_called_with("Goodbye!")
    
    async def test_token_counting(self):
        """Should estimate tokens"""
        stub = StubLLMProvider(simulate_latency=False)
        
        response = await stub.call(
            system_prompt="System prompt here",
            user_prompt="User prompt here"
        )
        
        # Should have reasonable token counts
        assert response.tokens_input > 0
        assert response.tokens_output > 0
    
    async def test_custom_parameters(self):
        """Should accept and track custom parameters"""
        stub = StubLLMProvider(simulate_latency=False)
        
        response = await stub.call(
            system_prompt="System",
            user_prompt="User",
            max_tokens=1000,
            temperature=0.5
        )
        
        last_call = stub.get_last_call()
        assert last_call['max_tokens'] == 1000
        assert last_call['temperature'] == 0.5

