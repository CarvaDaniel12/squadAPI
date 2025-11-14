"""
OpenRouter Provider Implementation

Wrapper for OpenRouter API using aiohttp (REST API).
OpenRouter provides access to multiple free models.

Features:
- Automatic fallback to available FREE models on failure
- Smart model discovery and selection
- Caches model list to avoid API spam
"""

import time
import logging
import os
from typing import Optional

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    aiohttp = None
    AIOHTTP_AVAILABLE = False

from .base import LLMProvider
from ..models.provider import (
    ProviderConfig,
    LLMResponse,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderAPIError
)
from ..utils.openrouter_fallback import OpenRouterSmartFallback


logger = logging.getLogger(__name__)


class OpenRouterProvider(LLMProvider):
    """
    OpenRouter API provider wrapper

    Features:
    - REST API via aiohttp
    - Multiple free models (Gemma, etc.)
    - Free tier: 20 RPM
    - OpenAI-compatible API

    Environment:
        OPENROUTER_API_KEY: Required API key

    Usage:
        config = ProviderConfig(name="openrouter", type="openrouter", model="google/gemma-2-9b-it:free", ...)
        provider = OpenRouterProvider(config)
        response = await provider.call("system", "user")
    """

    def __init__(self, config: ProviderConfig):
        """Initialize OpenRouter provider with smart fallback"""
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp not installed. Install: pip install aiohttp")

        super().__init__(config)

        # Get API key from environment using api_key_env
        api_key = os.getenv(config.api_key_env)
        if not api_key:
            raise ValueError(f"{config.api_key_env} not found in environment variables")

        self.api_key = api_key
        self.base_url = config.base_url or "https://openrouter.ai/api/v1"

        # Store config parameters
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.timeout = config.timeout

        # Initialize smart fallback system
        self.smart_fallback = OpenRouterSmartFallback(
            api_key=api_key,
            cache_duration_minutes=60  # Cache models for 1 hour
        )

        # Enable auto-fallback by default
        self.auto_fallback_enabled = True

        logger.info(f"OpenRouter provider initialized: model={self.model}, auto_fallback=enabled")

    async def call(
        self,
        system_prompt: str = None,
        user_prompt: str = None,
        messages: Optional[list] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        task_type: Optional[str] = None,  # 'code', 'reasoning', 'general'
        enable_fallback: Optional[bool] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Call OpenRouter API with automatic fallback

        Args:
            system_prompt: System message
            user_prompt: User message
            messages: Or full message list
            max_tokens: Max response tokens
            temperature: Temperature
            task_type: Type of task ('code', 'reasoning', 'general') for smart model selection
            enable_fallback: Override auto_fallback_enabled for this call
            **kwargs: Additional params

        Returns:
            LLMResponse
        """
        # Check if fallback should be used for this call
        use_fallback = (
            enable_fallback if enable_fallback is not None
            else self.auto_fallback_enabled
        )

        if use_fallback:
            # Use smart fallback system
            return await self.smart_fallback.call_with_auto_fallback(
                provider=self,
                messages=messages,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                task_type=task_type,
                **kwargs
            )
        else:
            # Direct call without fallback
            return await self._direct_call(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )

    async def _direct_call(
        self,
        system_prompt: str = None,
        user_prompt: str = None,
        messages: Optional[list] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """Direct API call without fallback logic"""
        start_time = time.time()

        # Handle different calling conventions
        if messages is None:
            messages = [
                {"role": "system", "content": system_prompt or "You are helpful."},
                {"role": "user", "content": user_prompt or ""}
            ]

        # Build payload (OpenAI-compatible)
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
            **kwargs
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://squad-api.local",  # Optional: for analytics
            "X-Title": "Squad API"  # Optional: for analytics
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as resp:
                    if resp.status == 429:
                        error_data = await resp.json()
                        retry_after = resp.headers.get("Retry-After")
                        raise ProviderRateLimitError(
                            provider=self.name,
                            message=str(error_data),
                            retry_after=int(retry_after) if retry_after else None
                        )

                    if resp.status >= 400:
                        error_data = await resp.text()
                        raise ProviderAPIError(
                            provider=self.name,
                            message=error_data,
                            status_code=resp.status
                        )

                    data = await resp.json()

            # Parse response
            latency_ms = int((time.time() - start_time) * 1000)

            content = data["choices"][0]["message"]["content"]
            tokens_input = data["usage"]["prompt_tokens"]
            tokens_output = data["usage"]["completion_tokens"]
            finish_reason = data["choices"][0]["finish_reason"]

            logger.info(f"OpenRouter response: {len(content)} chars, latency={latency_ms}ms")

            return LLMResponse(
                content=content,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                latency_ms=latency_ms,
                model=self.model,
                finish_reason=finish_reason,
                provider=self.name
            )

        except aiohttp.ClientError as e:
            logger.error(f"OpenRouter network error: {e}")
            raise ProviderTimeoutError(provider=self.name, message=str(e))

        except (ProviderRateLimitError, ProviderTimeoutError, ProviderAPIError):
            raise

        except Exception as e:
            logger.error(f"OpenRouter unexpected error: {e}")
            raise ProviderAPIError(provider=self.name, message=str(e))

    async def health_check(self) -> bool:
        """Check if OpenRouter API is reachable"""
        try:
            response = await self.call(
                system_prompt="Test",
                user_prompt="ping",
                max_tokens=5
            )
            return response is not None
        except Exception as e:
            logger.warning(f"OpenRouter health check failed: {e}")
            return False

