"""Unit tests for Settings (environment variables validation)

Tests settings loading, validation, and error handling.
"""

import pytest
from pydantic import ValidationError

from src.config.settings import Settings, get_settings


@pytest.fixture
def clean_env(monkeypatch):
    """Remove all API key env vars before test"""
    keys_to_remove = [
        'GROQ_API_KEY', 'CEREBRAS_API_KEY', 'GEMINI_API_KEY',
        'OPENROUTER_API_KEY', 'TOGETHER_API_KEY',
        'SLACK_WEBHOOK_URL', 'SLACK_ALERTS_ENABLED', 'LOG_LEVEL'
    ]
    for key in keys_to_remove:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def valid_env(monkeypatch):
    """Set all required env vars"""
    monkeypatch.setenv('GROQ_API_KEY', 'gsk_test_groq_key_12345')
    monkeypatch.setenv('CEREBRAS_API_KEY', 'csk_test_cerebras_key_12345')
    monkeypatch.setenv('GEMINI_API_KEY', 'AIzaSy_test_gemini_key_12345')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'sk-or-v1-test_openrouter_key_12345')


# ============================================================================
# Settings Loading Tests
# ============================================================================

def test_settings_all_required_present(valid_env):
    """Test Settings loads successfully with all required vars"""
    settings = Settings()

    assert settings.groq_api_key == 'gsk_test_groq_key_12345'
    assert settings.cerebras_api_key == 'csk_test_cerebras_key_12345'
    assert settings.gemini_api_key == 'AIzaSy_test_gemini_key_12345'
    assert settings.openrouter_api_key == 'sk-or-v1-test_openrouter_key_12345'


def test_settings_missing_required_api_key(clean_env, monkeypatch):
    """Test Settings fails when required API key missing"""
    # Only set some keys, leave others missing
    monkeypatch.setenv('GROQ_API_KEY', 'gsk_test_key')
    monkeypatch.setenv('CEREBRAS_API_KEY', 'csk_test_key')
    # Missing: GEMINI_API_KEY, OPENROUTER_API_KEY

    # Disable .env loading for this test
    monkeypatch.setenv('ENV_FILE', '')

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)  # Disable .env file

    # Check error mentions missing fields
    error_str = str(exc_info.value).lower()
    assert 'gemini_api_key' in error_str or 'field required' in error_str


def test_settings_empty_api_key(clean_env, monkeypatch):
    """Test Settings fails with empty API key"""
    monkeypatch.setenv('GROQ_API_KEY', '')  # Empty string
    monkeypatch.setenv('CEREBRAS_API_KEY', 'csk_test_key')
    monkeypatch.setenv('GEMINI_API_KEY', 'AIza_test_key')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'sk-or-test_key')

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    # Should fail min_length=1 validation
    assert 'groq_api_key' in str(exc_info.value).lower()


# ============================================================================
# Optional Variables Tests
# ============================================================================

def test_settings_optional_defaults(valid_env):
    """Test Settings applies defaults for optional variables"""
    settings = Settings()

    # Optional API keys
    assert settings.together_api_key is None
    assert settings.slack_webhook_url is None

    # Defaults
    assert settings.slack_alerts_enabled is False
    assert settings.log_level == 'INFO'
    assert settings.redis_url == 'redis://localhost:6379'
    assert 'postgresql://' in settings.postgres_url


def test_settings_optional_together_key(valid_env, monkeypatch):
    """Test Settings loads optional Together AI key"""
    monkeypatch.setenv('TOGETHER_API_KEY', 'together_test_key_12345')

    settings = Settings()
    assert settings.together_api_key == 'together_test_key_12345'


# ============================================================================
# Slack Validation Tests
# ============================================================================

def test_settings_slack_webhook_validation(valid_env, monkeypatch):
    """Test Settings validates Slack webhook URL format"""
    # Valid Slack webhook
    monkeypatch.setenv('SLACK_WEBHOOK_URL', 'https://hooks.slack.com/services/T00/B00/XXX')
    settings = Settings()
    assert settings.slack_webhook_url == 'https://hooks.slack.com/services/T00/B00/XXX'


def test_settings_invalid_slack_webhook(valid_env, monkeypatch):
    """Test Settings rejects invalid Slack webhook URL"""
    # Invalid webhook (not Slack format)
    monkeypatch.setenv('SLACK_WEBHOOK_URL', 'https://example.com/webhook')

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    error_str = str(exc_info.value)
    assert 'slack' in error_str.lower() or 'webhook' in error_str.lower()


def test_settings_slack_alerts_enabled(valid_env, monkeypatch):
    """Test Settings parses slack_alerts_enabled bool"""
    monkeypatch.setenv('SLACK_ALERTS_ENABLED', 'true')
    settings = Settings()
    assert settings.slack_alerts_enabled is True

    monkeypatch.setenv('SLACK_ALERTS_ENABLED', 'false')
    settings = Settings()
    assert settings.slack_alerts_enabled is False


# ============================================================================
# Log Level Validation Tests
# ============================================================================

def test_settings_log_level_validation(valid_env, monkeypatch):
    """Test Settings validates and normalizes log level"""
    # Valid log levels (case-insensitive)
    for level in ['DEBUG', 'debug', 'Info', 'WARNING', 'error', 'CRITICAL']:
        monkeypatch.setenv('LOG_LEVEL', level)
        settings = Settings()
        assert settings.log_level == level.upper()


def test_settings_invalid_log_level(valid_env, monkeypatch):
    """Test Settings rejects invalid log level"""
    monkeypatch.setenv('LOG_LEVEL', 'INVALID_LEVEL')

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    error_str = str(exc_info.value)
    assert 'log_level' in error_str.lower()


# ============================================================================
# Helper Methods Tests
# ============================================================================

def test_get_api_key_summary(valid_env, monkeypatch):
    """Test get_api_key_summary returns safe summary"""
    monkeypatch.setenv('TOGETHER_API_KEY', 'together_key')
    monkeypatch.setenv('SLACK_WEBHOOK_URL', 'https://hooks.slack.com/services/T/B/X')
    monkeypatch.setenv('SLACK_ALERTS_ENABLED', 'true')

    settings = Settings()
    summary = settings.get_api_key_summary()

    # Check structure
    assert isinstance(summary, dict)

    # Check required keys
    assert summary['groq'] is True
    assert summary['cerebras'] is True
    assert summary['gemini'] is True
    assert summary['openrouter'] is True

    # Check optional keys
    assert summary['together'] is True
    assert summary['slack_enabled'] is True

    # Ensure no actual key values in summary
    for value in summary.values():
        assert isinstance(value, bool)


def test_get_api_key_summary_missing_optional(valid_env):
    """Test get_api_key_summary with missing optional keys"""
    settings = Settings()
    summary = settings.get_api_key_summary()

    # Optional keys should be False
    assert summary['together'] is False
    assert summary['slack_enabled'] is False


# ============================================================================
# Singleton Tests
# ============================================================================

def test_get_settings_singleton(valid_env):
    """Test get_settings returns singleton instance"""
    # Reset singleton
    import src.config.settings
    src.config.settings._settings = None

    settings1 = get_settings()
    settings2 = get_settings()

    # Same instance
    assert settings1 is settings2


# ============================================================================
# Case Insensitivity Tests
# ============================================================================

def test_settings_case_insensitive(clean_env, monkeypatch):
    """Test Settings accepts lowercase env var names"""
    # Pydantic-settings should handle case-insensitive matching
    monkeypatch.setenv('groq_api_key', 'gsk_lowercase_test')
    monkeypatch.setenv('cerebras_api_key', 'csk_lowercase_test')
    monkeypatch.setenv('gemini_api_key', 'AIza_lowercase_test')
    monkeypatch.setenv('openrouter_api_key', 'sk-or-lowercase_test')

    settings = Settings()
    assert settings.groq_api_key == 'gsk_lowercase_test'
