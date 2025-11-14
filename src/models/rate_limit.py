"""
Rate Limiting Configuration Models

Pydantic models for rate limiting configuration and responses.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class ProviderRateLimitConfig(BaseModel):
    """Rate limit configuration for a single provider"""
    
    rpm: int = Field(..., description="Requests per minute")
    rpd: Optional[int] = Field(None, description="Requests per day (optional)")
    tpm: int = Field(..., description="Tokens per minute")
    burst: int = Field(..., description="Burst capacity (initial tokens)")
    window_size: int = Field(60, description="Sliding window size in seconds")
    
    model_config = ConfigDict(frozen=True)


class GlobalRateLimitConfig(BaseModel):
    """Global rate limiting settings"""
    
    max_concurrent: int = Field(12, description="Max concurrent requests")
    default_timeout: int = Field(30, description="Default timeout in seconds")
    
    model_config = ConfigDict(frozen=True)


class RetryConfig(BaseModel):
    """Retry configuration"""
    
    max_attempts: int = Field(5, description="Maximum retry attempts")
    base_delay: float = Field(1.0, description="Base delay in seconds")
    max_delay: float = Field(30.0, description="Maximum delay in seconds")
    exponential_base: int = Field(2, description="Exponential backoff base")
    jitter: float = Field(0.2, description="Jitter factor (%)")
    retryable_status_codes: List[int] = Field(
        default=[429, 500, 502, 503, 504],
        description="HTTP status codes that should trigger retry"
    )
    
    model_config = ConfigDict(frozen=True)


class RateLimitConfig(BaseModel):
    """Complete rate limiting configuration"""
    
    global_settings: GlobalRateLimitConfig = Field(alias="global")
    providers: dict[str, ProviderRateLimitConfig]
    retry: RetryConfig
    
    model_config = ConfigDict(populate_by_name=True)


class RateLimitState(BaseModel):
    """Current state of rate limiting for a provider"""
    
    provider: str
    tokens_available: int
    window_count: int  # Number of requests in current window
    window_limit: int  # Max requests allowed in window
    is_limited: bool = Field(
        default=False,
        description="Whether requests are currently being rate limited"
    )


class RateLimitError(Exception):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, provider: str, message: str, retry_after: Optional[int] = None):
        self.provider = provider
        self.message = message
        self.retry_after = retry_after
        super().__init__(f"{provider}: {message}")


