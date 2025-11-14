"""Configuration validation on startup

Cross-validates ConfigLoader (YAML) and Settings (environment variables).
Ensures all configuration is valid before application starts.

Validates:
- Rate limits have positive values (rpm > 0, burst >= rpm, tokens > 0)
- Agent chains reference existing providers
- Enabled providers have API keys set

Raises:
- ConfigurationError: If any validation fails
"""

from dataclasses import dataclass
from typing import Optional
import logging
from pydantic import ValidationError

from src.config.loader import ConfigLoader
from src.config.settings import Settings, get_settings
from src.config.models import RateLimitsConfig, AgentChainsConfig, ProvidersConfig, ProviderRateLimits

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration validation fails"""
    pass


@dataclass
class ConfigBundle:
    """Validated configuration bundle

    Contains all validated configuration from YAML files and environment.
    Safe to use throughout application after validate_config() succeeds.

    Attributes:
        settings: Environment variables (API keys, Slack, etc.)
        rate_limits: Provider rate limit configurations
        agent_chains: Agent fallback chain configurations
        providers: Provider configurations (model, timeout, etc.)
    """
    settings: Settings
    rate_limits: RateLimitsConfig
    agent_chains: AgentChainsConfig
    providers: ProvidersConfig


# Provider name to Settings field name mapping
PROVIDER_API_KEY_MAP = {
    'groq': 'groq_api_key',
    'cerebras': 'cerebras_api_key',
    'gemini': 'gemini_api_key',
    'openrouter': 'openrouter_api_key',
    'together': 'together_api_key',
}

# API key documentation URLs
API_KEY_DOCS = {
    'groq': 'https://console.groq.com/keys',
    'cerebras': 'https://cloud.cerebras.ai/',
    'gemini': 'https://aistudio.google.com/app/apikey',
    'openrouter': 'https://openrouter.ai/keys',
    'together': 'https://api.together.xyz/settings/api-keys',
}


def validate_rate_limits(rate_limits: RateLimitsConfig) -> None:
    """Validate rate limit values

    Checks that all rate limits have:
    - rpm > 0 (requests per minute must be positive)
    - burst >= rpm (burst must be at least equal to rpm)
    - tokens_per_minute > 0 (token limit must be positive)

    Args:
        rate_limits: Rate limits configuration to validate

    Raises:
        ConfigurationError: If any rate limit is invalid

    Example:
        >>> rate_limits = loader.load_rate_limits()
        >>> validate_rate_limits(rate_limits)  # Raises if invalid
    """
    providers = {
        'groq': rate_limits.groq,
        'cerebras': rate_limits.cerebras,
        'gemini': rate_limits.gemini,
        'openrouter': rate_limits.openrouter,
    }

    # Add optional together if present
    if rate_limits.together:
        providers['together'] = rate_limits.together

    for provider_name, limits in providers.items():
        # Check rpm > 0
        if limits.rpm <= 0:
            raise ConfigurationError(
                f"Invalid rate limit configuration for provider '{provider_name}':\n"
                f"  - rpm must be > 0 (got {limits.rpm})\n\n"
                f"Fix: Edit config/rate_limits.yaml and set {provider_name}.rpm to a positive value (e.g., 30)"
            )

        # Check burst >= rpm
        if limits.burst < limits.rpm:
            raise ConfigurationError(
                f"Invalid rate limit configuration for provider '{provider_name}':\n"
                f"  - burst must be >= rpm (got burst={limits.burst}, rpm={limits.rpm})\n\n"
                f"Fix: Edit config/rate_limits.yaml and set {provider_name}.burst >= {limits.rpm}"
            )

        # Check tokens_per_minute > 0
        if limits.tokens_per_minute <= 0:
            raise ConfigurationError(
                f"Invalid rate limit configuration for provider '{provider_name}':\n"
                f"  - tokens_per_minute must be > 0 (got {limits.tokens_per_minute})\n\n"
                f"Fix: Edit config/rate_limits.yaml and set {provider_name}.tokens_per_minute to a positive value"
            )


def validate_agent_chains(
    agent_chains: AgentChainsConfig,
    providers: ProvidersConfig
) -> None:
    """Validate agent chains reference valid providers

    Checks that:
    - Primary provider exists in providers config
    - All fallback providers exist in providers config
    - No duplicates in chain (primary not in fallbacks, no duplicate fallbacks)
    - At least 1 provider in chain (primary)

    Args:
        agent_chains: Agent chains configuration to validate
        providers: Providers configuration (for checking existence)

    Raises:
        ConfigurationError: If any agent chain is invalid

    Example:
        >>> agent_chains = loader.load_agent_chains()
        >>> providers = loader.load_providers()
        >>> validate_agent_chains(agent_chains, providers)
    """
    # Get all valid provider names from providers config
    valid_providers = {
        'groq', 'cerebras', 'gemini', 'openrouter'
    }
    if hasattr(providers, 'together') and providers.together:
        valid_providers.add('together')

    # Check all agent chains
    agents = {
        'mary': agent_chains.mary,
        'john': agent_chains.john,
        'alex': agent_chains.alex,
    }

    # Add optional agents if present
    if agent_chains.amelia:
        agents['amelia'] = agent_chains.amelia
    if agent_chains.bob:
        agents['bob'] = agent_chains.bob

    for agent_name, chain in agents.items():
        # Check primary provider exists
        if chain.primary not in valid_providers:
            raise ConfigurationError(
                f"Agent chain '{agent_name}' references unknown provider '{chain.primary}'\n\n"
                f"Available providers in config/providers.yaml:\n" +
                '\n'.join(f"  - {p}" for p in sorted(valid_providers)) + "\n\n"
                f"Fix: Edit config/agent_chains.yaml and use a valid provider name for {agent_name}.primary"
            )

        # Check fallback providers exist
        for fallback in chain.fallbacks:
            if fallback not in valid_providers:
                raise ConfigurationError(
                    f"Agent chain '{agent_name}' references unknown provider '{fallback}' in fallbacks\n\n"
                    f"Available providers in config/providers.yaml:\n" +
                    '\n'.join(f"  - {p}" for p in sorted(valid_providers)) + "\n\n"
                    f"Fix: Edit config/agent_chains.yaml and use valid provider names in {agent_name}.fallbacks"
                )


def validate_provider_api_keys(
    providers: ProvidersConfig,
    settings: Settings
) -> None:
    """Validate enabled providers have API keys

    Checks that each enabled provider has a corresponding non-empty API key
    in Settings (environment variables).

    Provider to API key mapping:
    - groq  GROQ_API_KEY
    - cerebras  CEREBRAS_API_KEY
    - gemini  GEMINI_API_KEY
    - openrouter  OPENROUTER_API_KEY
    - together  TOGETHER_API_KEY (optional)

    Args:
        providers: Providers configuration
        settings: Settings with API keys

    Raises:
        ConfigurationError: If enabled provider missing API key

    Example:
        >>> providers = loader.load_providers()
        >>> settings = get_settings()
        >>> validate_provider_api_keys(providers, settings)
    """
    # Check all providers
    provider_configs = {
        'groq': providers.groq,
        'cerebras': providers.cerebras,
        'gemini': providers.gemini,
        'openrouter': providers.openrouter,
    }

    # Add optional together if present
    if hasattr(providers, 'together') and providers.together:
        provider_configs['together'] = providers.together

    for provider_name, provider_config in provider_configs.items():
        # Skip if provider not enabled
        if not provider_config.enabled:
            continue

        # Get API key field name
        field_name = PROVIDER_API_KEY_MAP.get(provider_name)
        if not field_name:
            continue

        # Get API key from settings
        api_key = getattr(settings, field_name, None)

        # Check API key exists and not empty
        if not api_key:
            docs_url = API_KEY_DOCS.get(provider_name, '')
            raise ConfigurationError(
                f"Provider '{provider_name}' is enabled in config/providers.yaml but API key is missing\n\n"
                f"Required environment variable: {provider_config.api_key_env or field_name.upper()}\n"
                f"Get your API key at: {docs_url}\n\n"
                f"Fix: Add {field_name.upper()} to your .env file (see .env.example for template)"
            )


def _wrap_load(operation: str, loader_fn):
    """Execute a loader function and wrap errors in ConfigurationError."""
    try:
        return loader_fn()
    except FileNotFoundError as exc:
        raise ConfigurationError(
            f"Missing required configuration file for {operation}: {exc.filename}"
        ) from exc
    except ValidationError as exc:
        raise ConfigurationError(
            f"Invalid data in {operation}: {exc}"
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        raise ConfigurationError(
            f"Failed to load {operation}: {exc}"
        ) from exc


def validate_config(config_dir: str = "config") -> ConfigBundle:
    """Load and strictly validate all configuration before use."""
    logger.info("[CONFIG] Loading configuration...")

    loader = ConfigLoader(config_dir)
    settings = get_settings()

    rate_limits = _wrap_load("rate_limits.yaml", loader.load_rate_limits)
    agent_chains = _wrap_load("agent_chains.yaml", loader.load_agent_chains)
    providers = _wrap_load("providers.yaml", loader.load_providers)

    # Cross-validate loaded configs
    validate_rate_limits(rate_limits)
    validate_agent_chains(agent_chains, providers)
    validate_provider_api_keys(providers, settings)

    logger.info("[CONFIG] Configuration validated successfully")
    return ConfigBundle(
        settings=settings,
        rate_limits=rate_limits,
        agent_chains=agent_chains,
        providers=providers,
    )

