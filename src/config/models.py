"""Configuration data models

Pydantic models for validating YAML configuration files.
Ensures type safety and provides clear validation errors.

Models:
- RateLimitsConfig: Rate limiting settings per provider
- AgentChainsConfig: Agent fallback chains
- ProvidersConfig: Provider settings and API keys
"""

from pydantic import BaseModel, Field, validator, field_validator
from typing import Dict, List, Literal, Optional


class ProviderRateLimits(BaseModel):
    """Rate limits for a single provider

    Attributes:
        rpm: Requests per minute limit
        burst: Burst capacity (must be >= rpm)
        tokens_per_minute: Token consumption limit per minute
    """
    rpm: int = Field(..., gt=0, description="Requests per minute")
    burst: int = Field(..., gt=0, description="Burst capacity")
    tokens_per_minute: int = Field(..., gt=0, description="Token limit per minute")

    @field_validator('burst')
    @classmethod
    def burst_must_be_gte_rpm(cls, v, info):
        """Validate burst capacity >= RPM"""
        if 'rpm' in info.data and v < info.data['rpm']:
            raise ValueError(f'burst ({v}) must be >= rpm ({info.data["rpm"]})')
        return v


class RateLimitsConfig(BaseModel):
    """Rate limits configuration for all providers

    Loaded from: config/rate_limits.yaml

    Example:
        groq:
          rpm: 12
          burst: 15
          tokens_per_minute: 14400
    """
    groq: ProviderRateLimits
    cerebras: ProviderRateLimits
    gemini: ProviderRateLimits
    openrouter: ProviderRateLimits
    together: Optional[ProviderRateLimits] = None


class AgentChain(BaseModel):
    """Fallback chain for an agent

    Attributes:
        primary: Primary provider (first choice)
        fallbacks: Ordered list of fallback providers
    """
    primary: str = Field(..., description="Primary provider")
    fallbacks: List[str] = Field(default_factory=list, description="Fallback providers")

    @field_validator('fallbacks')
    @classmethod
    def no_duplicate_providers(cls, v, info):
        """Validate no duplicate providers in chain"""
        # Check primary not in fallbacks
        if 'primary' in info.data and info.data['primary'] in v:
            raise ValueError(
                f'Primary provider "{info.data["primary"]}" cannot be in fallbacks'
            )

        # Check no duplicates in fallbacks
        if len(v) != len(set(v)):
            duplicates = [p for p in v if v.count(p) > 1]
            raise ValueError(f'Duplicate providers in fallback chain: {duplicates}')

        return v


class AgentChainsConfig(BaseModel):
    """Agent fallback chains configuration

    Loaded from: config/agent_chains.yaml

    Example:
        mary:
          primary: groq
          fallbacks:
            - cerebras
            - gemini
    """
    mary: AgentChain
    john: AgentChain
    alex: AgentChain
    amelia: Optional[AgentChain] = None
    bob: Optional[AgentChain] = None


class ProviderConfig(BaseModel):
    """Configuration for a single provider

    Attributes:
        name: Provider instance name (for identification)
        type: Provider type (groq, cerebras, gemini, openrouter, etc.)
        enabled: Whether provider is active
        model: Model name/identifier
        api_key_env: Environment variable name for API key
        base_url: Optional base URL (for custom endpoints)
        timeout: Request timeout in seconds
        rpm_limit: Requests per minute limit
        tpm_limit: Tokens per minute limit
        max_tokens: Maximum tokens per request
        temperature: Model temperature setting
    """
    name: str = Field(..., description="Provider instance name")
    type: str = Field(..., description="Provider type")
    enabled: bool = True
    model: str = Field(..., description="Model name")
    api_key_env: str = Field(..., description="Environment variable for API key")
    base_url: Optional[str] = None
    timeout: int = Field(default=30, gt=0, description="Timeout in seconds")
    rpm_limit: Optional[int] = None
    tpm_limit: Optional[int] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class PromptOptimizerConfig(BaseModel):
    """Configuration for the local lightweight optimizer/aggregator."""

    model_config = {"protected_namespaces": ()}

    enabled: bool = False
    model_path: str = Field(..., description="Path to local model weights (e.g., GGUF file) or Ollama model name")
    runtime: Literal["llama-cpp", "gpt4all", "ollama", "custom"] = "llama-cpp"
    endpoint: Optional[str] = Field(default="http://localhost:11434", description="Ollama API endpoint")
    max_context_tokens: int = Field(default=4096, gt=0)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    bmad_config: str = Field(..., description="Path to BMAD method configuration")
    aggregation_prompt: str = Field(..., description="Prompt used to merge specialist outputs")


class ProvidersConfig(BaseModel):
    """Providers configuration

    Loaded from: config/providers.yaml

    Example:
        groq:
          enabled: true
          model: llama-3.3-70b-versatile
          api_key_env: GROQ_API_KEY
          timeout: 30
    """
    groq: ProviderConfig
    cerebras: ProviderConfig
    gemini: ProviderConfig
    openrouter: ProviderConfig
    anthropic: ProviderConfig
    openai: Optional[ProviderConfig] = None
    together: Optional[ProviderConfig] = None
    prompt_optimizer: Optional[PromptOptimizerConfig] = None
