"""
Rate Limit Configuration Loader

Loads and parses rate_limits.yaml configuration file.
"""

import yaml
from pathlib import Path
from typing import Optional
from ..models.rate_limit import RateLimitConfig, ProviderRateLimitConfig, GlobalRateLimitConfig, RetryConfig


class RateLimitConfigLoader:
    """Loads rate limit configuration from YAML file"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration loader
        
        Args:
            config_path: Path to rate_limits.yaml (defaults to config/rate_limits.yaml)
        """
        if config_path is None:
            # Default to config/rate_limits.yaml relative to project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "rate_limits.yaml"
        
        self.config_path = config_path
        self._config: Optional[RateLimitConfig] = None
    
    def load(self) -> RateLimitConfig:
        """
        Load configuration from YAML file
        
        Returns:
            Parsed RateLimitConfig object
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Rate limit config not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)
        
        # Parse global settings
        global_settings = GlobalRateLimitConfig(**raw_config.get('global', {}))
        
        # Parse provider configs
        providers = {}
        for provider_name, provider_config in raw_config.get('providers', {}).items():
            providers[provider_name] = ProviderRateLimitConfig(**provider_config)
        
        # Parse retry config
        retry = RetryConfig(**raw_config.get('retry', {}))
        
        # Build complete config
        self._config = RateLimitConfig(
            global_settings=global_settings,
            providers=providers,
            retry=retry
        )
        
        return self._config
    
    def get_provider_config(self, provider: str) -> Optional[ProviderRateLimitConfig]:
        """
        Get configuration for a specific provider
        
        Args:
            provider: Provider name (e.g., 'groq', 'cerebras')
            
        Returns:
            Provider configuration or None if not found
        """
        if self._config is None:
            self.load()
        
        return self._config.providers.get(provider)
    
    def get_global_config(self) -> GlobalRateLimitConfig:
        """Get global rate limiting settings"""
        if self._config is None:
            self.load()
        
        return self._config.global_settings
    
    def get_retry_config(self) -> RetryConfig:
        """Get retry configuration"""
        if self._config is None:
            self.load()
        
        return self._config.retry


# Global singleton instance
_config_loader: Optional[RateLimitConfigLoader] = None


def get_rate_limit_config() -> RateLimitConfigLoader:
    """Get global rate limit config loader instance"""
    global _config_loader
    if _config_loader is None:
        _config_loader = RateLimitConfigLoader()
    return _config_loader

