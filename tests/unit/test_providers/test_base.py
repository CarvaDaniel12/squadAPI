"""
Unit Tests for LLM Provider Base Class

Tests the abstract interface and base implementation.
"""

import pytest
from src.providers.base import LLMProvider
from src.models.provider import ProviderConfig, LLMResponse


# Concrete implementation for testing
class MockProvider(LLMProvider):
    """Mock provider for testing base class"""
    
    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens=None,
        temperature=None,
        **kwargs
    ) -> LLMResponse:
        """Mock implementation"""
        return LLMResponse(
            content="Mock response",
            tokens_input=100,
            tokens_output=50,
            latency_ms=100,
            model=self.model,
            finish_reason="stop",
            provider=self.name
        )
    
    async def health_check(self) -> bool:
        """Mock implementation"""
        return True


@pytest.mark.unit
class TestLLMProviderBase:
    """Test LLMProvider base class"""
    
    def test_initialization(self):
        """Should initialize with config"""
        config = ProviderConfig(
            name="test-provider",
            type="mock",
            model="test-model",
            rpm_limit=30,
            tpm_limit=20000
        )
        
        provider = MockProvider(config)
        
        assert provider.name == "test-provider"
        assert provider.model == "test-model"
        assert provider.rpm_limit == 30
        assert provider.tpm_limit == 20000
    
    def test_get_max_tokens_default(self):
        """Should use config default when not specified"""
        config = ProviderConfig(
            name="test",
            type="mock",
            model="test",
            rpm_limit=30,
            tpm_limit=20000,
            max_tokens=1500
        )
        
        provider = MockProvider(config)
        
        assert provider.get_max_tokens() == 1500
    
    def test_get_max_tokens_override(self):
        """Should use parameter when specified"""
        config = ProviderConfig(
            name="test",
            type="mock",
            model="test",
            rpm_limit=30,
            tpm_limit=20000,
            max_tokens=1500
        )
        
        provider = MockProvider(config)
        
        assert provider.get_max_tokens(max_tokens=3000) == 3000
    
    def test_get_temperature_default(self):
        """Should use config default when not specified"""
        config = ProviderConfig(
            name="test",
            type="mock",
            model="test",
            rpm_limit=30,
            tpm_limit=20000,
            temperature=0.5
        )
        
        provider = MockProvider(config)
        
        assert provider.get_temperature() == 0.5
    
    def test_get_temperature_override(self):
        """Should use parameter when specified"""
        config = ProviderConfig(
            name="test",
            type="mock",
            model="test",
            rpm_limit=30,
            tpm_limit=20000,
            temperature=0.5
        )
        
        provider = MockProvider(config)
        
        assert provider.get_temperature(temperature=0.9) == 0.9
    
    def test_count_tokens_heuristic(self):
        """Should estimate tokens using heuristic"""
        config = ProviderConfig(
            name="test",
            type="mock",
            model="test",
            rpm_limit=30,
            tpm_limit=20000
        )
        
        provider = MockProvider(config)
        
        # ~4 characters per token
        text = "Hello, world!"  # 13 characters
        tokens = provider.count_tokens(text)
        
        assert tokens >= 1  # At least 1 token
        assert tokens <= 10  # Rough estimate
    
    def test_count_tokens_empty(self):
        """Should return at least 1 token for empty text"""
        config = ProviderConfig(
            name="test",
            type="mock",
            model="test",
            rpm_limit=30,
            tpm_limit=20000
        )
        
        provider = MockProvider(config)
        
        assert provider.count_tokens("") == 1
    
    def test_repr(self):
        """Should have readable repr"""
        config = ProviderConfig(
            name="test-provider",
            type="mock",
            model="test-model",
            rpm_limit=30,
            tpm_limit=20000
        )
        
        provider = MockProvider(config)
        repr_str = repr(provider)
        
        assert "MockProvider" in repr_str
        assert "test-provider" in repr_str
        assert "test-model" in repr_str
        assert "30" in repr_str


@pytest.mark.unit
@pytest.mark.asyncio
class TestLLMProviderAsync:
    """Test async methods of LLMProvider"""
    
    async def test_call_returns_response(self):
        """Should return LLMResponse"""
        config = ProviderConfig(
            name="test",
            type="mock",
            model="test-model",
            rpm_limit=30,
            tpm_limit=20000
        )
        
        provider = MockProvider(config)
        
        response = await provider.call(
            system_prompt="You are a helpful assistant",
            user_prompt="Hello!"
        )
        
        assert isinstance(response, LLMResponse)
        assert response.content == "Mock response"
        assert response.provider == "test"
        assert response.model == "test-model"
    
    async def test_health_check_returns_bool(self):
        """Should return boolean"""
        config = ProviderConfig(
            name="test",
            type="mock",
            model="test-model",
            rpm_limit=30,
            tpm_limit=20000
        )
        
        provider = MockProvider(config)
        
        result = await provider.health_check()
        
        assert isinstance(result, bool)
        assert result is True

