"""
Anthropic Provider Implementation

Wrapper for Anthropic API using official anthropic Python SDK.
Supports Claude 3.5 Sonnet and other models.
"""

import time
import logging
import os
from typing import Optional

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    AsyncAnthropic = None
    ANTHROPIC_AVAILABLE = False

from .base import LLMProvider
from ..models.provider import (
    ProviderConfig,
    LLMResponse,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderAPIError
)

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """
    Anthropic API provider wrapper

    Features:
    - Official Anthropic Python SDK
    - Claude 3.5 Sonnet support
    - Automatic error handling
    - Cost tracking

    Environment:
        ANTHROPIC_API_KEY: Required API key

    Models:
        - claude-3-5-sonnet-20241022: $3.00/$15.00 per 1M tokens
    """

    def __init__(self, config: ProviderConfig):
        """
        Initialize Anthropic provider

        Args:
            config: Provider configuration

        Raises:
            ImportError: If anthropic SDK not installed
            ValueError: If ANTHROPIC_API_KEY not found
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package not installed. Install: pip install anthropic"
            )

        super().__init__(config)

        # Get API key from environment using api_key_env
        api_key = os.getenv(config.api_key_env)
        if not api_key:
            raise ValueError(
                f"{config.api_key_env} not found in environment variables"
            )

        # Initialize Anthropic client
        self.client = AsyncAnthropic(api_key=api_key)

        # Store config parameters
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.timeout = config.timeout

        logger.info(f"Anthropic provider initialized: model={self.model}")

    async def call(
        self,
        system_prompt: str = None,
        user_prompt: str = None,
        messages: Optional[list] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        Call Anthropic API

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

        # Build messages (Anthropic format - no system in messages)
        if messages is None:
            messages = []
            if user_prompt:
                messages.append({"role": "user", "content": user_prompt})
        else:
            # Filter out system messages if present
            messages = [m for m in messages if m.get("role") != "system"]

        if not messages:
            raise ValueError("No messages provided")

        # Use config defaults if not specified
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens or self.max_tokens

        try:
            # Call Anthropic API
            response = await self.client.messages.create(
                model=self.model,
                messages=messages,
                system=system_prompt or "",  # System is separate parameter
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.timeout
            )

            # Extract response
            content = response.content[0].text
            finish_reason = response.stop_reason

            # Get token usage
            tokens_input = response.usage.input_tokens
            tokens_output = response.usage.output_tokens

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"Anthropic call successful: {tokens_input} in / {tokens_output} out tokens, "
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
                logger.warning(f"Anthropic rate limit: {error_msg}")
                raise ProviderRateLimitError(
                    provider=self.name,
                    message=error_msg,
                    retry_after=60
                )

            # Handle timeouts
            elif "timeout" in error_msg.lower():
                logger.error(f"Anthropic timeout: {error_msg}")
                raise ProviderTimeoutError(
                    provider=self.name,
                    message=error_msg
                )

            # Other errors
            else:
                logger.error(f"Anthropic API error: {error_msg}")
                raise ProviderAPIError(
                    provider=self.name,
                    message=error_msg
                )

    async def health_check(self) -> bool:
        """Check if Anthropic API is accessible"""
        try:
            # Simple test call
            response = await self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"Anthropic health check failed: {e}")
            return False
