"""
Provider Factory

Dynamically creates and manages LLM provider instances based on configuration.
Supports registration, validation, and provider discovery.
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Optional, List, Type
from pydantic import ValidationError

from .base import LLMProvider
from .groq_provider import GroqProvider
from ..config.models import ProviderConfig


logger = logging.getLogger(__name__)


# Import providers with fallback
try:
    from .anthropic_provider import AnthropicProvider
except ImportError:
    AnthropicProvider = None
    logger.warning("Anthropic provider not available (anthropic package not installed)")

try:
    from .openai_provider import OpenAIProvider
except ImportError:
    OpenAIProvider = None
    logger.warning("OpenAI provider not available (openai package not installed)")

try:
    from .cerebras_provider import CerebrasProvider
except ImportError:
    CerebrasProvider = None
    logger.warning("Cerebras provider not available (aiohttp not installed)")

try:
    from .gemini_provider import GeminiProvider
except ImportError:
    GeminiProvider = None
    logger.warning("Gemini provider not available (google-genai not installed)")

try:
    from .openrouter_provider import OpenRouterProvider
except ImportError:
    OpenRouterProvider = None
    logger.warning("OpenRouter provider not available (aiohttp not installed)")


class ProviderFactory:
    """
    Factory for creating LLM provider instances

    Features:
    - Dynamic provider creation from YAML config
    - Provider registry (type -> class mapping)
    - API key validation
    - No fallback to stub provider - fail fast on missing API keys
    - Extensible (easy to add new providers)

    Usage:
        factory = ProviderFactory()
        providers = factory.create_all("config/providers.yaml")
        groq = providers['groq']
        response = await groq.call("system", "user")
    """

    def __init__(self):
        """Initialize provider factory"""
        # Provider type -> Class mapping
        self.PROVIDER_CLASSES: Dict[str, Type[LLMProvider]] = {
            'groq': GroqProvider,
        }

        # Add optional providers if available
        if AnthropicProvider is not None:
            self.PROVIDER_CLASSES['anthropic'] = AnthropicProvider
            logger.info("Anthropic provider registered")
        else:
            logger.warning("Anthropic provider not registered - package not available")

        if OpenAIProvider is not None:
            self.PROVIDER_CLASSES['openai'] = OpenAIProvider
            logger.info("OpenAI provider registered")
        else:
            logger.warning("OpenAI provider not registered - package not available")

        if CerebrasProvider is not None:
            self.PROVIDER_CLASSES['cerebras'] = CerebrasProvider
            logger.info("Cerebras provider registered")
        else:
            logger.warning("Cerebras provider not registered - package not available")

        if GeminiProvider is not None:
            self.PROVIDER_CLASSES['gemini'] = GeminiProvider
            logger.info("Gemini provider registered")
        else:
            logger.warning("Gemini provider not registered - package not available")

        if OpenRouterProvider is not None:
            self.PROVIDER_CLASSES['openrouter'] = OpenRouterProvider
            logger.info("OpenRouter provider registered")
        else:
            logger.warning("OpenRouter provider not registered - package not available")

        self.providers: Dict[str, LLMProvider] = {}
        logger.info(f"Provider factory initialized with {len(self.PROVIDER_CLASSES)} provider types")

    def register_provider_class(self, provider_type: str, provider_class: Type[LLMProvider]):
        """
        Register a new provider class

        Args:
            provider_type: Provider type identifier (e.g., 'myprovider')
            provider_class: Provider class (must inherit from LLMProvider)
        """
        if not issubclass(provider_class, LLMProvider):
            raise TypeError(f"{provider_class} must inherit from LLMProvider")

        self.PROVIDER_CLASSES[provider_type] = provider_class
        logger.info(f"Registered provider type: {provider_type}")

    def create_provider(self, name: str, config_dict: dict) -> Optional[LLMProvider]:
        """
        Create a single provider instance with API key validation

        Args:
            name: Provider instance name
            config_dict: Provider configuration dict

        Returns:
            Provider instance or raises RuntimeError if API key is missing

        Raises:
            RuntimeError: If required API key is missing
            ImportError: If provider SDK is not installed
        """
        try:
            # Build config (keep 'name' as it's required by ProviderConfig)
            config = ProviderConfig(**config_dict)

            # Check if provider is enabled
            if not config.enabled:
                logger.info(f"Provider '{name}' is disabled, skipping")
                return None

            # Get provider class
            provider_type = config.type
            provider_class = self.PROVIDER_CLASSES.get(provider_type)

            if not provider_class:
                raise RuntimeError(f"Unknown provider type '{provider_type}' for '{name}'. Available providers: {list(self.PROVIDER_CLASSES.keys())}")

            # Validate API key before creating provider
            self._validate_api_key(provider_type, config.api_key_env, name)

            # Create provider instance
            provider = provider_class(config)

            logger.info(f"Created provider: {name} ({provider_type}, model={config.model})")
            return provider

        except (ImportError, ValueError) as e:
            # These are configuration errors - fail fast
            logger.error(f"Failed to create provider '{name}': {e}")
            raise RuntimeError(f"Provider '{name}' configuration error: {e}") from e
        except ValidationError as e:
            # Pydantic validation errors - show detailed error
            logger.error(f"Failed to create provider '{name}' - validation error: {e}")
            raise RuntimeError(f"Provider '{name}' configuration error: {e}") from e
        except Exception as e:
            logger.error(f"Failed to create provider '{name}': {e}")
            return None

    def _validate_api_key(self, provider_type: str, api_key_env: str, provider_name: str):
        """
        Validate that required API key is present

        Args:
            provider_type: Provider type identifier
            api_key_env: Environment variable name for API key
            provider_name: Provider instance name

        Raises:
            RuntimeError: If API key is missing
        """
        import os

        # For stub provider, no API key needed
        if provider_type == "stub":
            return

        if not api_key_env:
            raise RuntimeError(f"Provider '{provider_name}' missing api_key_env configuration")

        api_key = os.getenv(api_key_env)
        if not api_key:
            raise RuntimeError(
                f"API key for provider '{provider_name}' not found. "
                f"Please set {api_key_env} environment variable or provide api_key in config. "
                f"See docs/API-KEYS-SETUP.md for setup instructions."
            )

        logger.debug(f"API key validation passed for {provider_name} ({api_key_env})")

    def create_all(self, config_path: str) -> Dict[str, LLMProvider]:
        """
        Create all providers from YAML configuration

        Args:
            config_path: Path to providers.yaml

        Returns:
            Dict mapping provider name -> provider instance
        """
        config_file = Path(config_path)

        if not config_file.exists():
            logger.error(f"Provider config not found: {config_path}")
            return {}

        # Load YAML config
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        providers_config = config_data.get('providers', {})

        logger.info(f"Loading providers from {config_path}: {len(providers_config)} providers found")

        # Create providers
        providers = {}
        for name, provider_config in providers_config.items():
            provider = self.create_provider(name, provider_config)
            if provider:
                providers[name] = provider

        self.providers = providers

        logger.info(f"Provider factory created {len(providers)} providers: {list(providers.keys())}")

        # Validate that we have at least one working provider
        if not providers:
            logger.error("No providers could be initialized. Check your API keys and configuration.")

        return providers

    def get_provider(self, name: str) -> Optional[LLMProvider]:
        """
        Get provider by name

        Args:
            name: Provider name

        Returns:
            Provider instance or None
        """
        return self.providers.get(name)

    def list_providers(self) -> List[str]:
        """List all available provider names"""
        return list(self.providers.keys())

    def list_enabled_providers(self) -> List[str]:
        """List enabled provider names"""
        return [name for name, p in self.providers.items() if p.config.enabled]

    async def health_check_all(self) -> Dict[str, bool]:
        """
        Run health check on all providers

        Returns:
            Dict mapping provider name -> health status
        """
        results = {}

        for name, provider in self.providers.items():
            try:
                is_healthy = await provider.health_check()
                results[name] = is_healthy
                logger.info(f"Health check {name}: {'healthy' if is_healthy else 'unhealthy'}")
            except Exception as e:
                logger.error(f"Health check {name} failed: {e}")
                results[name] = False

        return results


# Global singleton instance
_factory: Optional[ProviderFactory] = None


def get_provider_factory() -> ProviderFactory:
    """Get global provider factory instance"""
    global _factory
    if _factory is None:
        _factory = ProviderFactory()
    return _factory
