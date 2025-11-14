"""
LLM Provider Abstract Base Class

Defines the interface that all LLM providers must implement.
This ensures consistency across Groq, Cerebras, Gemini, OpenRouter, etc.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import logging

from ..models.provider import ProviderConfig, LLMResponse


logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """
    Abstract base class for all LLM providers
    
    All providers (Groq, Cerebras, Gemini, OpenRouter) must implement this interface.
    This allows the orchestrator to work with any provider transparently.
    """
    
    def __init__(self, config: ProviderConfig):
        """
        Initialize provider with configuration
        
        Args:
            config: Provider configuration (API key, model, limits, etc.)
        """
        self.config = config
        self.name = config.name
        self.model = config.model
        self.rpm_limit = config.rpm_limit
        self.tpm_limit = config.tpm_limit
        
        logger.info(
            f"Initialized {self.__class__.__name__}: "
            f"name={self.name}, model={self.model}, rpm={self.rpm_limit}"
        )
    
    @abstractmethod
    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Make an LLM API call
        
        Args:
            system_prompt: System prompt (agent persona, rules, etc.)
            user_prompt: User's message/task
            max_tokens: Maximum tokens to generate (uses config default if None)
            temperature: Sampling temperature (uses config default if None)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse with content, tokens, latency, etc.
            
        Raises:
            ProviderRateLimitError: If rate limit exceeded (429)
            ProviderTimeoutError: If request times out
            ProviderAPIError: If API returns an error
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if provider is healthy and reachable
        
        Returns:
            True if provider is healthy, False otherwise
        """
        pass
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        
        Uses simple heuristic: ~4 characters per token (English text).
        Providers can override this with more accurate methods.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Estimated token count
        """
        # Simple heuristic: ~4 chars per token
        return max(1, len(text) // 4)
    
    def get_max_tokens(self, max_tokens: Optional[int] = None) -> int:
        """Get max_tokens value (use parameter or config default)"""
        return max_tokens if max_tokens is not None else self.config.max_tokens
    
    def get_temperature(self, temperature: Optional[float] = None) -> float:
        """Get temperature value (use parameter or config default)"""
        return temperature if temperature is not None else self.config.temperature
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"model='{self.model}', "
            f"rpm={self.rpm_limit})"
        )

