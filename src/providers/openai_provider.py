"""
OpenAI Provider Implementation

Wrapper for OpenAI API using official openai Python SDK.
Supports GPT-4o, GPT-4o-mini, and other models.
"""

import time
import logging
import os
from typing import Optional

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    AsyncOpenAI = None
    OPENAI_AVAILABLE = False

from .base import LLMProvider
from ..models.provider import (
    ProviderConfig,
    LLMResponse,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderAPIError
)

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """
    OpenAI API provider wrapper

    Features:
    - Official OpenAI Python SDK
    - GPT-4o, GPT-4o-mini support
    - Automatic error handling
    - Cost tracking

    Environment:
        OPENAI_API_KEY: Required API key

    Models:
        - gpt-4o: $2.50/$10.00 per 1M tokens (premium)
        - gpt-4o-mini: $0.15/$0.60 per 1M tokens (cheap)
    """

    def __init__(self, config: ProviderConfig):
        """
        Initialize OpenAI provider

        Args:
            config: Provider configuration

        Raises:
            ImportError: If openai SDK not installed
            ValueError: If OPENAI_API_KEY not found
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai package not installed. Install: pip install openai"
            )

        super().__init__(config)

        # Get API key from environment using api_key_env
        api_key = os.getenv(config.api_key_env)
        if not api_key:
            raise ValueError(
                f"{config.api_key_env} not found in environment variables"
            )

        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=api_key)

        # Store config parameters
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.timeout = config.timeout

        logger.info(f"OpenAI provider initialized: model={self.model}")

    async def call(
        self,
        system_prompt: str = None,
        user_prompt: str = None,
        messages: Optional[list] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        Call OpenAI API

        Args:
            system_prompt: System message
            user_prompt: User message
            messages: Full message list (overrides system/user)
            temperature: Sampling temperature
            max_tokens: Max response tokens

        Returns:
            LLMResponse with content and metadata

        Raises:
            ProviderRateLimitError: Rate limit exceeded
            ProviderTimeoutError: Request timeout
            ProviderAPIError: Other API errors
        """
        start_time = time.time()

        # Build messages
        if messages is None:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            if user_prompt:
                messages.append({"role": "user", "content": user_prompt})

        if not messages:
            raise ValueError("No messages provided")

        # Use config defaults if not specified
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens or self.max_tokens

        try:
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.timeout
            )

            # Extract response
            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason

            # Get token usage
            usage = response.usage
            tokens_input = usage.prompt_tokens
            tokens_output = usage.completion_tokens

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"OpenAI call successful: {tokens_input} in / {tokens_output} out tokens, "
                f"{latency_ms}ms latency"
            )

            return LLMResponse(
                content=content,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                latency_ms=latency_ms,
                model=self.model,
                finish_reason=finish_reason,
                provider=self.name
            )

        except Exception as e:
            error_msg = str(e)

            # Handle rate limits
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                logger.warning(f"OpenAI rate limit: {error_msg}")
                raise ProviderRateLimitError(
                    provider=self.name,
                    message=error_msg,
                    retry_after=60
                )

            # Handle timeouts
            elif "timeout" in error_msg.lower():
                logger.error(f"OpenAI timeout: {error_msg}")
                raise ProviderTimeoutError(
                    provider=self.name,
                    message=error_msg
                )

            # Other errors
            else:
                logger.error(f"OpenAI API error: {error_msg}")
                raise ProviderAPIError(
                    provider=self.name,
                    message=error_msg
                )

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible"""
        try:
            # Simple test call
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return False
