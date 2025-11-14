"""
Google Gemini Provider Implementation

Wrapper for Google Gemini API using official google-genai SDK.
Supports Gemini 2.0 Flash and other models.
"""

import time
import logging
import os
from typing import Optional

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    types = None
    GENAI_AVAILABLE = False

from .base import LLMProvider
from ..models.provider import (
    ProviderConfig,
    LLMResponse,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderAPIError
)


logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """
    Google Gemini API provider wrapper
    
    Features:
    - Official google-genai SDK
    - Gemini 2.0 Flash support (very fast)
    - Free tier: 15 RPM, 1M TPM
    - Auto-detects GEMINI_API_KEY
    
    Environment:
        GEMINI_API_KEY: Required API key
    
    Usage:
        config = ProviderConfig(name="gemini", type="gemini", model="gemini-2.0-flash-exp", ...)
        provider = GeminiProvider(config)
        response = await provider.call("system", "user")
    """
    
    def __init__(self, config: ProviderConfig):
        """Initialize Gemini provider"""
        if not GENAI_AVAILABLE:
            raise ImportError("google-genai not installed. Install: pip install google-genai")
        
        super().__init__(config)
        
        # Get API key from environment using api_key_env
        api_key = os.getenv(config.api_key_env)
        if not api_key:
            raise ValueError(f"{config.api_key_env} not found in environment variables")
        
        # Initialize Gemini client
        self.client = genai.Client(api_key=api_key)
        
        logger.info(f"Gemini provider initialized: model={self.model}")
    
    async def call(
        self,
        system_prompt: str = None,
        user_prompt: str = None,
        messages: Optional[list] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """Call Gemini API"""
        start_time = time.time()
        
        # Handle different calling conventions
        if messages is not None:
            # Extract from messages array
            system_prompt = ""
            user_prompt = ""
            for msg in messages:
                if msg.get("role") == "system":
                    system_prompt = msg.get("content", "")
                elif msg.get("role") == "user":
                    user_prompt = msg.get("content", "")
        
        # Gemini combines system + user in single prompt
        combined_prompt = f"{system_prompt}\n\nUser: {user_prompt}\nAssistant:"
        
        try:
            # Create config
            gen_config = types.GenerateContentConfig(
                max_output_tokens=self.get_max_tokens(max_tokens),
                temperature=self.get_temperature(temperature),
                **kwargs
            )
            
            # Call Gemini API
            response = self.client.models.generate_content(
                model=self.model,
                contents=combined_prompt,
                config=gen_config
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Extract response
            content = response.text
            tokens_input = response.usage_metadata.prompt_token_count
            tokens_output = response.usage_metadata.candidates_token_count
            finish_reason = str(response.candidates[0].finish_reason)
            
            logger.info(f"Gemini response: {len(content)} chars, latency={latency_ms}ms")
            
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
            error_str = str(e).lower()
            
            if "429" in error_str or "quota" in error_str:
                raise ProviderRateLimitError(
                    provider=self.name,
                    message=str(e)
                )
            
            if "timeout" in error_str:
                raise ProviderTimeoutError(
                    provider=self.name,
                    message=str(e)
                )
            
            logger.error(f"Gemini error: {e}")
            raise ProviderAPIError(provider=self.name, message=str(e))
    
    async def health_check(self) -> bool:
        """Check if Gemini API is reachable"""
        try:
            response = await self.call(
                system_prompt="Test",
                user_prompt="ping",
                max_tokens=5
            )
            return response is not None
        except Exception as e:
            logger.warning(f"Gemini health check failed: {e}")
            return False

