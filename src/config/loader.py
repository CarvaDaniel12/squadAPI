"""Configuration loader

Centralized YAML configuration loader with validation.
Loads and validates all YAML config files using Pydantic models.

Usage:
    loader = ConfigLoader()
    rate_limits = loader.load_rate_limits()
    agent_chains = loader.load_agent_chains()
    providers = loader.load_providers()
"""

from pathlib import Path
import yaml
import logging
from typing import TypeVar, Type

from .models import RateLimitsConfig, AgentChainsConfig, ProvidersConfig

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ConfigLoader:
    """Centralized YAML configuration loader

    Loads and validates all YAML config files using Pydantic models.
    Provides consistent error handling and logging.

    Attributes:
        config_dir: Path to configuration directory

    Example:
        loader = ConfigLoader()
        rate_limits = loader.load_rate_limits()

        # Custom config directory
        loader = ConfigLoader(config_dir="./custom_config")
    """

    def __init__(self, config_dir: str = "./config"):
        """Initialize config loader

        Args:
            config_dir: Directory containing config YAML files

        Raises:
            FileNotFoundError: If config directory doesn't exist
        """
        self.config_dir = Path(config_dir)

        if not self.config_dir.exists():
            raise FileNotFoundError(
                f"Config directory not found: {config_dir}"
            )

        logger.info(f"ConfigLoader initialized: config_dir={self.config_dir}")

    def load_rate_limits(self) -> RateLimitsConfig:
        """Load and validate rate_limits.yaml

        Returns:
            Validated RateLimitsConfig instance

        Raises:
            FileNotFoundError: If rate_limits.yaml not found
            yaml.YAMLError: If YAML syntax invalid
            pydantic.ValidationError: If config schema invalid

        Example:
            config = loader.load_rate_limits()
            groq_rpm = config.groq.rpm  # 12
        """
        return self._load_config("rate_limits.yaml", RateLimitsConfig)

    def load_agent_chains(self) -> AgentChainsConfig:
        """Load and validate agent_chains.yaml

        Returns:
            Validated AgentChainsConfig instance

        Raises:
            FileNotFoundError: If agent_chains.yaml not found
            yaml.YAMLError: If YAML syntax invalid
            pydantic.ValidationError: If config schema invalid

        Example:
            config = loader.load_agent_chains()
            mary_primary = config.mary.primary  # "groq"
        """
        return self._load_config("agent_chains.yaml", AgentChainsConfig)

    def load_providers(self) -> ProvidersConfig:
        """Load and validate providers.yaml

        Returns:
            Validated ProvidersConfig instance

        Raises:
            FileNotFoundError: If providers.yaml not found
            yaml.YAMLError: If YAML syntax invalid
            pydantic.ValidationError: If config schema invalid

        Example:
            config = loader.load_providers()
            groq_model = config.groq.model  # "llama-3.3-70b-versatile"
        """
        return self._load_config("providers.yaml", ProvidersConfig)

    def _load_config(self, filename: str, model_class: Type[T]) -> T:
        """Generic config loader with validation

        Loads YAML file, validates with Pydantic model, and returns instance.

        Args:
            filename: Config file name (e.g., "rate_limits.yaml")
            model_class: Pydantic model class for validation

        Returns:
            Validated config instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML parsing fails
            ValueError: If config file is empty
            pydantic.ValidationError: If validation fails
        """
        path = self.config_dir / filename

        # Check file exists
        if not path.exists():
            error_msg = f"Config file not found: {path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            # Load YAML
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            # Check not empty
            if data is None:
                error_msg = f"Empty config file: {filename}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Validate with Pydantic
            config = model_class(**data)

            logger.info(f"Loaded config: {filename}")
            return config

        except yaml.YAMLError as e:
            logger.error(f"YAML syntax error in {filename}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")
            raise


# Singleton instance (optional - can also use dependency injection)
_loader_instance = None


def get_config_loader(config_dir: str = "./config") -> ConfigLoader:
    """Get singleton ConfigLoader instance

    Args:
        config_dir: Configuration directory path

    Returns:
        ConfigLoader instance (reused across calls)

    Example:
        loader = get_config_loader()
        rate_limits = loader.load_rate_limits()
    """
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = ConfigLoader(config_dir)
    return _loader_instance
