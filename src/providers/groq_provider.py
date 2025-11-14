"""
Groq Provider Implementation

Wrapper for Groq API using official groq Python SDK.
Supports Llama-3-70B and other models via Groq's fast inference.
"""

import time
import logging
import os
from typing import Optional

try:
    from groq import AsyncGroq, RateLimitError, APIError, APITimeoutError
    GROQ_AVAILABLE = True
except ImportError:
    AsyncGroq = None
    RateLimitError = Exception
    APIError = Exception
    APITimeoutError = Exception
    GROQ_AVAILABLE = False

from .base import LLMProvider
from ..models.provider import (
    ProviderConfig,
    LLMResponse,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderAPIError
)


logger = logging.getLogger(__name__)


class GroqProvider(LLMProvider):
    """
    Groq API provider wrapper

    Features:
    - Official Groq Python SDK (AsyncGroq)
    - Llama-3-70B-8192 support
    - Fast inference (Groq's LPU acceleration)
    - Rate limit: 30 RPM (free tier)
    - Automatic error handling (429, timeouts, etc.)

    Environment:
        GROQ_API_KEY: Required API key

    Usage:
        config = ProviderConfig(name="groq", type="groq", model="llama-3.1-70b-versatile", ...)
        provider = GroqProvider(config)
        response = await provider.call("system", "user")
    """

    def __init__(self, config: ProviderConfig):
        """
        Initialize Groq provider

        Args:
            config: Provider configuration

        Raises:
            ImportError: If groq SDK not installed
            ValueError: If GROQ_API_KEY not found
        """
        if not GROQ_AVAILABLE:
            raise ImportError(
                "groq package not installed. Install: pip install groq"
            )

        super().__init__(config)

        # Get API key from environment using api_key_env
        api_key = os.getenv(config.api_key_env)
        if not api_key:
            raise ValueError(
                f"{config.api_key_env} not found in environment variables"
            )

        # Initialize Groq client
        # Note: AsyncGroq doesn't accept 'proxies' argument - only 'http_client'
        # We create it explicitly to avoid any proxy-related issues
        try:
            self.client = AsyncGroq(api_key=api_key)
        except TypeError as e:
            if 'proxies' in str(e) or 'unexpected keyword' in str(e):
                # Fallback: try with explicit http_client to avoid proxy issues
                import httpx
                http_client = httpx.AsyncClient(
                    timeout=httpx.Timeout(30.0),
                    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
                )
                self.client = AsyncGroq(api_key=api_key, http_client=http_client)
            else:
                raise

        logger.info(f"Groq provider initialized: model={self.model}")

    async def call(
        self,
        system_prompt: str = None,
        user_prompt: str = None,
        messages: Optional[list] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Call Groq API

        Args:
            system_prompt: System prompt (agent persona, rules)
            user_prompt: User's message/task
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional Groq-specific parameters

        Returns:
            LLMResponse with content, tokens, latency

        Raises:
            ProviderRateLimitError: If 429 rate limit exceeded
            ProviderTimeoutError: If request times out
            ProviderAPIError: If API returns an error
        """
        start_time = time.time()

        # Handle different calling conventions
        if messages is None:
            # Direct call with system_prompt and user_prompt
            messages = [
                {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                {"role": "user", "content": user_prompt or ""}
            ]
        else:
            # Messages provided - normalize to proper format
            normalized_messages = []
            for msg in messages:
                content = msg.get("content")

                # Handle nested messages (flatten)
                if isinstance(content, list):
                    # Content is an array of messages - flatten it
                    for nested_msg in content:
                        if isinstance(nested_msg, dict) and nested_msg.get("content"):
                            normalized_messages.append({
                                "role": nested_msg.get("role", "user"),
                                "content": str(nested_msg.get("content", ""))
                            })
                elif isinstance(content, str) and content.strip():
                    # Content is a string - use it
                    normalized_messages.append({
                        "role": msg.get("role", "user"),
                        "content": content
                    })

            messages = normalized_messages

        # Ensure we have at least one message
        if not messages:
            messages = [{"role": "user", "content": "ping"}]

        # Debug: log messages structure
        logger.debug(f"Groq messages count: {len(messages)}")
        for i, msg in enumerate(messages):
            logger.debug(f"  Message {i}: role={msg.get('role')}, content_type={type(msg.get('content'))}, content_len={len(str(msg.get('content')))}")

        # Get parameters
        max_tokens_value = self.get_max_tokens(max_tokens)
        temperature_value = self.get_temperature(temperature)

        try:
            logger.debug(
                f"Groq call: model={self.model}, "
                f"max_tokens={max_tokens_value}, temp={temperature_value}, "
                f"messages_count={len(messages)}"
            )

            # Call Groq API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens_value,
                temperature=temperature_value,
                **kwargs
            )

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Extract response data
            content = response.choices[0].message.content or ""
            tokens_input = response.usage.prompt_tokens
            tokens_output = response.usage.completion_tokens
            finish_reason = response.choices[0].finish_reason

            logger.info(
                f"Groq response: {len(content)} chars, "
                f"in={tokens_input}, out={tokens_output}, "
                f"latency={latency_ms}ms"
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

        # Re-raise our own exceptions (for testing and internal propagation)
        except (ProviderRateLimitError, ProviderTimeoutError, ProviderAPIError):
            raise

        except RateLimitError as e:
            logger.warning(f"Groq rate limit exceeded: {e}")
            # Try to extract Retry-After from error
            retry_after = getattr(e, 'retry_after', None)
            raise ProviderRateLimitError(
                provider=self.name,
                message=str(e),
                retry_after=retry_after
            )

        except APITimeoutError as e:
            logger.error(f"Groq timeout: {e}")
            raise ProviderTimeoutError(
                provider=self.name,
                message=str(e)
            )

        except APIError as e:
            logger.error(f"Groq API error: {e}")
            raise ProviderAPIError(
                provider=self.name,
                message=str(e),
                status_code=getattr(e, 'status_code', None)
            )

        except Exception as e:
            logger.error(f"Groq unexpected error: {e}")
            raise ProviderAPIError(
                provider=self.name,
                message=f"Unexpected error: {str(e)}"
            )

    async def health_check(self) -> bool:
        """
        Check if Groq API is reachable

        Makes a minimal API call to verify connectivity.

        Returns:
            True if healthy, False otherwise
        """
        try:
            logger.debug("Groq health check starting")

            # Make minimal API call
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5
            )

            is_healthy = response is not None
            logger.info(f"Groq health check: {'healthy' if is_healthy else 'unhealthy'}")

            return is_healthy

        except Exception as e:
            logger.warning(f"Groq health check failed: {e}")
            return False

