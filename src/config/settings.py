"""Application settings from environment variables

Validates and loads all required environment variables on startup.
Uses Pydantic Settings for type-safe configuration.

Required:
- API keys for all providers (Groq, Cerebras, Gemini, OpenRouter)

Optional:
- Slack webhook URL and alerts toggle
- Together AI API key (future)
- Log level, Redis URL, PostgreSQL URL
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings from environment variables

    Loads from .env file and validates all required variables.
    Fails fast on startup if required keys missing.

    Usage:
        settings = Settings()  # Raises ValidationError if invalid
        groq_key = settings.groq_api_key

    Example:
        # With .env file
        settings = Settings()

        # Override with environment
        import os
        os.environ['GROQ_API_KEY'] = 'gsk_override'
        settings = Settings()
    """

    # API Keys (Optional - at least one is recommended)
    groq_api_key: Optional[str] = Field(
        None,
        description="Groq API key (get at https://console.groq.com/keys)"
    )
    cerebras_api_key: Optional[str] = Field(
        None,
        description="Cerebras API key (get at https://cloud.cerebras.ai/)"
    )
    gemini_api_key: Optional[str] = Field(
        None,
        description="Google Gemini API key (get at https://aistudio.google.com/app/apikey)"
    )
    openrouter_api_key: Optional[str] = Field(
        None,
        description="OpenRouter API key (get at https://openrouter.ai/keys)"
    )
    anthropic_api_key: Optional[str] = Field(
        None,
        description="Anthropic API key (get at https://console.anthropic.com/)"
    )
    openai_api_key: Optional[str] = Field(
        None,
        description="OpenAI API key (get at https://platform.openai.com/)"
    )

    # Optional API Keys
    together_api_key: Optional[str] = Field(
        None,
        description="Together AI API key (optional - for future use)"
    )

    # Slack Configuration
    slack_webhook_url: Optional[str] = Field(
        None,
        description="Slack webhook URL for alerts"
    )
    slack_alerts_enabled: bool = Field(
        False,
        description="Enable Slack alerts (requires webhook URL)"
    )

    # Application Configuration
    log_level: str = Field(
        "INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    redis_url: str = Field(
        "redis://localhost:6379",
        description="Redis connection URL"
    )
    postgres_url: str = Field(
        "postgresql://squad:squad@localhost:5432/squad_api",
        description="PostgreSQL connection URL"
    )

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
        env_ignore_empty=True  # Ignore empty env vars
    )

    @field_validator('slack_webhook_url')
    @classmethod
    def validate_slack_webhook(cls, v):
        """Validate Slack webhook URL format

        Args:
            v: Webhook URL value

        Returns:
            Validated URL

        Raises:
            ValueError: If URL doesn't match expected format
        """
        if v is not None and v and not v.startswith('https://hooks.slack.com/'):
            raise ValueError(
                'Slack webhook must start with https://hooks.slack.com/ '
                '(create at https://api.slack.com/messaging/webhooks)'
            )
        return v

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level against standard logging levels

        Args:
            v: Log level string

        Returns:
            Uppercase log level

        Raises:
            ValueError: If log level not recognized
        """
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f'log_level must be one of {valid_levels}, got: {v}'
            )
        return v_upper

    def get_api_key_summary(self) -> dict:
        """Get summary of loaded API keys (without exposing values)

        Safe for logging - shows which keys are configured without
        revealing actual key values.

        Returns:
            Dict with key names and whether they're loaded

        Example:
            summary = settings.get_api_key_summary()
            # {'groq': True, 'cerebras': True, 'gemini': False, ...}
            logger.info(f"API keys loaded: {summary}")
        """
        return {
            'groq': bool(self.groq_api_key),
            'cerebras': bool(self.cerebras_api_key),
            'gemini': bool(self.gemini_api_key),
            'openrouter': bool(self.openrouter_api_key),
            'anthropic': bool(self.anthropic_api_key),
            'openai': bool(self.openai_api_key),
            'together': bool(self.together_api_key),
            'slack_enabled': self.slack_alerts_enabled and bool(self.slack_webhook_url)
        }

    def log_startup_summary(self):
        """Log startup configuration summary

        Logs API key availability and configuration without
        exposing sensitive values.
        """
        summary = self.get_api_key_summary()
        all_keys = ['groq', 'cerebras', 'gemini', 'openrouter', 'anthropic', 'openai']
        loaded_keys = sum(1 for k in all_keys if summary[k])

        logger.info(
            f"Settings loaded: {loaded_keys}/{len(all_keys)} API keys configured, "
            f"log_level={self.log_level}, "
            f"slack_alerts={summary['slack_enabled']}"
        )
        
        if loaded_keys == 0:
            logger.warning(
                "No API keys configured! Please set at least one API key in .env file. "
                "See docs/API-KEYS-SETUP.md for setup instructions."
            )


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get singleton Settings instance

    Loads settings from environment on first call, then caches.
    Subsequent calls return cached instance.

    Returns:
        Settings instance (cached after first call)

    Raises:
        ValidationError: If required environment variables missing

    Example:
        settings = get_settings()
        api_key = settings.groq_api_key
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.log_startup_summary()
    return _settings
