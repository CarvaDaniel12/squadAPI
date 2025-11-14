"""
Provider Configuration and Response Models

Pydantic models for LLM provider configuration and responses.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ProviderConfig(BaseModel):
    """Configuration for an LLM provider"""
    
    name: str = Field(..., description="Provider name (e.g., 'groq', 'cerebras')")
    type: str = Field(..., description="Provider type/class (e.g., 'groq', 'gemini')")
    model: str = Field(..., description="Model identifier (e.g., 'llama-3-70b-8192')")
    api_key: Optional[str] = Field(None, description="API key (if required)")
    base_url: Optional[str] = Field(None, description="Base URL for API (if custom)")
    rpm_limit: int = Field(..., description="Requests per minute limit")
    tpm_limit: int = Field(..., description="Tokens per minute limit")
    max_tokens: int = Field(2000, description="Default max tokens for responses")
    temperature: float = Field(0.7, description="Default temperature")
    timeout: int = Field(30, description="Request timeout in seconds")
    enabled: bool = Field(True, description="Whether provider is enabled")
    
    model_config = ConfigDict(frozen=False)


class LLMResponse(BaseModel):
    """Response from an LLM provider"""
    
    content: str = Field(..., description="Generated text content")
    tokens_input: int = Field(..., description="Number of input tokens")
    tokens_output: int = Field(..., description="Number of output tokens")
    latency_ms: int = Field(..., description="Latency in milliseconds")
    model: str = Field(..., description="Model used for generation")
    finish_reason: str = Field(..., description="Why generation stopped")
    provider: str = Field(..., description="Provider name")
    
    model_config = ConfigDict(frozen=True)


class LLMError(Exception):
    """Base exception for LLM provider errors"""
    
    def __init__(self, provider: str, message: str, status_code: Optional[int] = None):
        self.provider = provider
        self.message = message
        self.status_code = status_code
        super().__init__(f"{provider}: {message}")


class ProviderRateLimitError(LLMError):
    """Raised when provider rate limit is exceeded"""
    
    def __init__(self, provider: str, message: str, retry_after: Optional[int] = None):
        super().__init__(provider, message, status_code=429)
        self.retry_after = retry_after


class ProviderTimeoutError(LLMError):
    """Raised when provider request times out"""
    
    def __init__(self, provider: str, message: str):
        super().__init__(provider, message, status_code=504)


class ProviderAPIError(LLMError):
    """Raised when provider API returns an error"""
    pass

