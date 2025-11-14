"""
Cerebras Provider Implementation

Wrapper for Cerebras API using aiohttp (REST API).
Cerebras provides ultra-fast inference with free tier access.
"""

import time
import logging
import os
import json
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


logger = logging.getLogger(__name__)


class CerebrasProvider(LLMProvider):
    """
    Cerebras API provider wrapper
    
    Features:
    - REST API via aiohttp
    - Llama-3-8B support (ultra-fast inference)
    - Free tier: 30 RPM
    - OpenAI-compatible API format
    
    Environment:
        CEREBRAS_API_KEY: Required API key
    
    Usage:
        config = ProviderConfig(name="cerebras", type="cerebras", model="llama3.1-8b", ...)
        provider = CerebrasProvider(config)
        response = await provider.call("system", "user")
    """
    
    def __init__(self, config: ProviderConfig):
        """Initialize Cerebras provider"""
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp not installed. Install: pip install aiohttp")
        
        super().__init__(config)
        
        # Get API key from environment using api_key_env
        api_key = os.getenv(config.api_key_env)
        if not api_key:
            raise ValueError(f"{config.api_key_env} not found in environment variables")
        
        self.api_key = api_key
        self.base_url = config.base_url or "https://api.cerebras.ai/v1"
        
        logger.info(f"Cerebras provider initialized: model={self.model}")
    
    async def call(
        self,
        system_prompt: str = None,
        user_prompt: str = None,
        messages: Optional[list] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """Call Cerebras API"""
        start_time = time.time()
        
        # Handle different calling conventions
        if messages is None:
            messages = [
                {"role": "system", "content": system_prompt or "You are helpful."},
                {"role": "user", "content": user_prompt or ""}
            ]
        
        # Build payload
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.get_max_tokens(max_tokens),
            "temperature": self.get_temperature(temperature),
            **kwargs
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
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
            
            logger.info(f"Cerebras response: {len(content)} chars, latency={latency_ms}ms")
            
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
            logger.error(f"Cerebras network error: {e}")
            raise ProviderTimeoutError(provider=self.name, message=str(e))
        
        except (ProviderRateLimitError, ProviderTimeoutError, ProviderAPIError):
            raise
        
        except Exception as e:
            logger.error(f"Cerebras unexpected error: {e}")
            raise ProviderAPIError(provider=self.name, message=str(e))
    
    async def health_check(self) -> bool:
        """Check if Cerebras API is reachable"""
        try:
            response = await self.call(
                system_prompt="Test",
                user_prompt="ping",
                max_tokens=5
            )
            return response is not None
        except Exception as e:
            logger.warning(f"Cerebras health check failed: {e}")
            return False

