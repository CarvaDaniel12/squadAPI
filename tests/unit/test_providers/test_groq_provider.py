"""
Unit Tests for Groq Provider

Tests Groq API wrapper (with mocked API calls).
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.models.provider import ProviderConfig, LLMResponse
from src.models.provider import ProviderRateLimitError, ProviderTimeoutError, ProviderAPIError


# Mock groq SDK
mock_groq_response = MagicMock()
mock_groq_response.choices = [MagicMock()]
mock_groq_response.choices[0].message.content = "Test response"
mock_groq_response.choices[0].finish_reason = "stop"
mock_groq_response.usage = MagicMock()
mock_groq_response.usage.prompt_tokens = 100
mock_groq_response.usage.completion_tokens = 50


@pytest.mark.unit
@pytest.mark.asyncio
@patch('src.providers.groq_provider.GROQ_AVAILABLE', True)
@patch('src.providers.groq_provider.AsyncGroq')
class TestGroqProvider:
    """Test Groq provider (mocked)"""

    async def test_initialization(self, mock_async_groq):
        """Should initialize with API key"""
        from src.providers.groq_provider import GroqProvider

        config = ProviderConfig(
            name="groq",
            type="groq",
            model="llama-3.1-70b-versatile",
            api_key="test-key",
            rpm_limit=30,
            tpm_limit=20000
        )

        provider = GroqProvider(config)

        assert provider.name == "groq"
        assert provider.model == "llama-3.1-70b-versatile"
        assert mock_async_groq.called

    async def test_initialization_no_api_key(self, mock_async_groq):
        """Should raise error if no API key"""
        from src.providers.groq_provider import GroqProvider

        config = ProviderConfig(
            name="groq",
            type="groq",
            model="llama-3.1-70b-versatile",
            rpm_limit=30,
            tpm_limit=20000
        )

        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GROQ_API_KEY"):
                GroqProvider(config)

    async def test_call_success(self, mock_async_groq):
        """Should make successful API call"""
        from src.providers.groq_provider import GroqProvider

        # Setup mock
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_groq_response)
        mock_async_groq.return_value = mock_client

        config = ProviderConfig(
            name="groq",
            type="groq",
            model="llama-3.1-70b-versatile",
            api_key="test-key",
            rpm_limit=30,
            tpm_limit=20000
        )

        provider = GroqProvider(config)

        response = await provider.call(
            system_prompt="You are helpful",
            user_prompt="Hello!"
        )

        assert isinstance(response, LLMResponse)
        assert response.content == "Test response"
        assert response.tokens_input == 100
        assert response.tokens_output == 50
        assert response.provider == "groq"
        assert mock_client.chat.completions.create.called

    async def test_call_with_custom_parameters(self, mock_async_groq):
        """Should pass custom parameters to API"""
        from src.providers.groq_provider import GroqProvider

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_groq_response)
        mock_async_groq.return_value = mock_client

        config = ProviderConfig(
            name="groq",
            type="groq",
            model="llama-3.1-70b-versatile",
            api_key="test-key",
            rpm_limit=30,
            tpm_limit=20000
        )

        provider = GroqProvider(config)

        await provider.call(
            system_prompt="System",
            user_prompt="User",
            max_tokens=1000,
            temperature=0.5
        )

        # Verify API was called with correct parameters
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs['max_tokens'] == 1000
        assert call_kwargs['temperature'] == 0.5

    async def test_call_rate_limit_error(self, mock_async_groq):
        """Should handle rate limit error"""
        from src.providers.groq_provider import GroqProvider

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=ProviderRateLimitError("groq", "Rate limit exceeded")
        )
        mock_async_groq.return_value = mock_client

        config = ProviderConfig(
            name="groq",
            type="groq",
            model="llama-3.1-70b-versatile",
            api_key="test-key",
            rpm_limit=30,
            tpm_limit=20000
        )

        provider = GroqProvider(config)

        with pytest.raises(ProviderRateLimitError):
            await provider.call("system", "user")

    async def test_call_timeout_error(self, mock_async_groq):
        """Should handle timeout error"""
        from src.providers.groq_provider import GroqProvider

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=ProviderTimeoutError("groq", "Timeout")
        )
        mock_async_groq.return_value = mock_client

        config = ProviderConfig(
            name="groq",
            type="groq",
            model="llama-3.1-70b-versatile",
            api_key="test-key",
            rpm_limit=30,
            tpm_limit=20000
        )

        provider = GroqProvider(config)

        with pytest.raises(ProviderTimeoutError):
            await provider.call("system", "user")

    async def test_health_check_healthy(self, mock_async_groq):
        """Should return True when healthy"""
        from src.providers.groq_provider import GroqProvider

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_groq_response)
        mock_async_groq.return_value = mock_client

        config = ProviderConfig(
            name="groq",
            type="groq",
            model="llama-3.1-70b-versatile",
            api_key="test-key",
            rpm_limit=30,
            tpm_limit=20000
        )

        provider = GroqProvider(config)

        result = await provider.health_check()

        assert result is True

    async def test_health_check_unhealthy(self, mock_async_groq):
        """Should return False when unhealthy"""
        from src.providers.groq_provider import GroqProvider

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("Error"))
        mock_async_groq.return_value = mock_client

        config = ProviderConfig(
            name="groq",
            type="groq",
            model="llama-3.1-70b-versatile",
            api_key="test-key",
            rpm_limit=30,
            tpm_limit=20000
        )

        provider = GroqProvider(config)

        result = await provider.health_check()

        assert result is False

