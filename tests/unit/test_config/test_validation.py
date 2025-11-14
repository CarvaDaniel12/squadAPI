"""Unit tests for config validation

Tests cross-validation of YAML configs and environment variables.
"""

import pytest
from pydantic import ValidationError

from src.config.validation import (
    validate_rate_limits,
    validate_agent_chains,
    validate_provider_api_keys,
    validate_config,
    ConfigurationError,
    ConfigBundle,
)
from src.config.models import (
    RateLimitsConfig,
    AgentChainsConfig,
    ProvidersConfig,
    ProviderRateLimits,
    AgentChain,
    ProviderConfig,
)
from src.config.settings import Settings


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def valid_rate_limits():
    """Valid rate limits config"""
    return RateLimitsConfig(
        groq=ProviderRateLimits(rpm=30, burst=40, tokens_per_minute=100000),
        cerebras=ProviderRateLimits(rpm=20, burst=30, tokens_per_minute=80000),
        gemini=ProviderRateLimits(rpm=15, burst=20, tokens_per_minute=60000),
        openrouter=ProviderRateLimits(rpm=10, burst=15, tokens_per_minute=50000),
    )


@pytest.fixture
def valid_providers():
    """Valid providers config"""
    return ProvidersConfig(
        groq=ProviderConfig(
            enabled=True,
            model="llama-3.1-70b-versatile",
            api_key_env="GROQ_API_KEY",
            base_url="https://api.groq.com/openai/v1",
            timeout=30
        ),
        cerebras=ProviderConfig(
            enabled=True,
            model="llama3.1-8b",
            api_key_env="CEREBRAS_API_KEY",
            base_url="https://api.cerebras.ai/v1",
            timeout=30
        ),
        gemini=ProviderConfig(
            enabled=True,
            model="gemini-1.5-flash",
            api_key_env="GEMINI_API_KEY",
            timeout=30
        ),
        openrouter=ProviderConfig(
            enabled=True,
            model="meta-llama/llama-3.1-8b-instruct:free",
            api_key_env="OPENROUTER_API_KEY",
            base_url="https://openrouter.ai/api/v1",
            timeout=30
        ),
    )


@pytest.fixture
def valid_agent_chains():
    """Valid agent chains config"""
    return AgentChainsConfig(
        mary=AgentChain(primary="groq", fallbacks=["cerebras", "gemini"]),
        john=AgentChain(primary="cerebras", fallbacks=["groq"]),
        alex=AgentChain(primary="gemini", fallbacks=["openrouter"]),
    )


@pytest.fixture
def valid_settings(monkeypatch):
    """Valid settings with all API keys"""
    monkeypatch.setenv('GROQ_API_KEY', 'gsk_test_key')
    monkeypatch.setenv('CEREBRAS_API_KEY', 'csk_test_key')
    monkeypatch.setenv('GEMINI_API_KEY', 'AIzaSy_test_key')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'sk-or-v1-test_key')
    return Settings(_env_file=None)


# ============================================================================
# Rate Limits Validation Tests
# ============================================================================

def test_validate_rate_limits_success(valid_rate_limits):
    """Test rate limits validation with valid config"""
    # Should not raise
    validate_rate_limits(valid_rate_limits)


def test_validate_rate_limits_rpm_zero():
    """Test rate limits validation fails when rpm = 0"""
    # Pydantic validates rpm > 0 in ProviderRateLimits model
    # Creating invalid model should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        rate_limits = RateLimitsConfig(
            groq=ProviderRateLimits(rpm=0, burst=40, tokens_per_minute=100000),  # Invalid: rpm = 0
            cerebras=ProviderRateLimits(rpm=20, burst=30, tokens_per_minute=80000),
            gemini=ProviderRateLimits(rpm=15, burst=20, tokens_per_minute=60000),
            openrouter=ProviderRateLimits(rpm=10, burst=15, tokens_per_minute=50000),
        )

    error_msg = str(exc_info.value).lower()
    assert 'rpm' in error_msg or 'greater than 0' in error_msg
def test_validate_rate_limits_burst_less_than_rpm():
    """Test rate limits validation fails when burst < rpm"""
    # Pydantic validates burst >= rpm in ProviderRateLimits model
    with pytest.raises(ValidationError) as exc_info:
        rate_limits = RateLimitsConfig(
            groq=ProviderRateLimits(rpm=30, burst=20, tokens_per_minute=100000),  # Invalid: burst < rpm
            cerebras=ProviderRateLimits(rpm=20, burst=30, tokens_per_minute=80000),
            gemini=ProviderRateLimits(rpm=15, burst=20, tokens_per_minute=60000),
            openrouter=ProviderRateLimits(rpm=10, burst=15, tokens_per_minute=50000),
        )

    error_msg = str(exc_info.value).lower()
    assert 'burst' in error_msg
def test_validate_rate_limits_tokens_zero():
    """Test rate limits validation fails when tokens_per_minute = 0"""
    # Pydantic validates tokens_per_minute > 0 in ProviderRateLimits model
    with pytest.raises(ValidationError) as exc_info:
        rate_limits = RateLimitsConfig(
            groq=ProviderRateLimits(rpm=30, burst=40, tokens_per_minute=0),  # Invalid
            cerebras=ProviderRateLimits(rpm=20, burst=30, tokens_per_minute=80000),
            gemini=ProviderRateLimits(rpm=15, burst=20, tokens_per_minute=60000),
            openrouter=ProviderRateLimits(rpm=10, burst=15, tokens_per_minute=50000),
        )

    error_msg = str(exc_info.value).lower()
    assert 'tokens_per_minute' in error_msg or 'greater than 0' in error_msg
# ============================================================================
# Agent Chains Validation Tests
# ============================================================================

def test_validate_agent_chains_success(valid_agent_chains, valid_providers):
    """Test agent chains validation with valid config"""
    # Should not raise
    validate_agent_chains(valid_agent_chains, valid_providers)


def test_validate_agent_chains_unknown_primary(valid_providers):
    """Test agent chains validation fails with unknown primary"""
    agent_chains = AgentChainsConfig(
        mary=AgentChain(primary="invalid_provider", fallbacks=["cerebras"]),  # Invalid primary
        john=AgentChain(primary="cerebras", fallbacks=["groq"]),
        alex=AgentChain(primary="gemini", fallbacks=["openrouter"]),
    )

    with pytest.raises(ConfigurationError) as exc_info:
        validate_agent_chains(agent_chains, valid_providers)

    error_msg = str(exc_info.value).lower()
    assert 'invalid_provider' in error_msg
    assert 'mary' in error_msg
    assert 'available providers' in error_msg


def test_validate_agent_chains_unknown_fallback(valid_providers):
    """Test agent chains validation fails with unknown fallback"""
    agent_chains = AgentChainsConfig(
        mary=AgentChain(primary="groq", fallbacks=["cerebras", "invalid_provider"]),  # Invalid fallback
        john=AgentChain(primary="cerebras", fallbacks=["groq"]),
        alex=AgentChain(primary="gemini", fallbacks=["openrouter"]),
    )

    with pytest.raises(ConfigurationError) as exc_info:
        validate_agent_chains(agent_chains, valid_providers)

    error_msg = str(exc_info.value).lower()
    assert 'invalid_provider' in error_msg
    assert 'mary' in error_msg
    assert 'fallbacks' in error_msg


# Note: Duplicate validation is already handled by Pydantic validator in AgentChain model
# So we don't need a separate test here - Pydantic will raise ValidationError before our function runs


# ============================================================================
# Provider API Keys Validation Tests
# ============================================================================

def test_validate_provider_api_keys_success(valid_providers, valid_settings):
    """Test provider API keys validation with all keys"""
    # Should not raise
    validate_provider_api_keys(valid_providers, valid_settings)


def test_validate_provider_api_keys_missing(valid_providers, monkeypatch):
    """Test provider API keys validation fails when key missing"""
    # Clean environment first
    for key in ['GROQ_API_KEY', 'CEREBRAS_API_KEY', 'GEMINI_API_KEY', 'OPENROUTER_API_KEY']:
        monkeypatch.delenv(key, raising=False)

    # Only set some keys
    monkeypatch.setenv('GROQ_API_KEY', 'gsk_test_key')
    monkeypatch.setenv('CEREBRAS_API_KEY', 'csk_test_key')
    # Missing: GEMINI_API_KEY, OPENROUTER_API_KEY

    # Settings creation will fail because gemini and openrouter are required
    # But we can test the validation function with a partial Settings mock
    # Create Settings with all keys to bypass initial validation
    monkeypatch.setenv('GEMINI_API_KEY', 'temp_key')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'temp_key')
    settings = Settings(_env_file=None)

    # Now manually clear the keys we want to test as missing
    settings.gemini_api_key = None  # type: ignore

    # Gemini is enabled but API key now missing
    with pytest.raises(ConfigurationError) as exc_info:
        validate_provider_api_keys(valid_providers, settings)

    error_msg = str(exc_info.value).lower()
    assert 'api key is missing' in error_msg
    assert 'gemini' in error_msg
def test_validate_provider_api_keys_disabled_provider_ok(valid_settings):
    """Test disabled provider without API key is OK"""
    providers = ProvidersConfig(
        groq=ProviderConfig(
            enabled=True,
            model="llama-3.1-70b-versatile",
            api_key_env="GROQ_API_KEY",
            timeout=30
        ),
        cerebras=ProviderConfig(
            enabled=False,  # Disabled
            model="llama3.1-8b",
            api_key_env="CEREBRAS_API_KEY",
            timeout=30
        ),
        gemini=ProviderConfig(
            enabled=True,
            model="gemini-1.5-flash",
            api_key_env="GEMINI_API_KEY",
            timeout=30
        ),
        openrouter=ProviderConfig(
            enabled=True,
            model="meta-llama/llama-3.1-8b-instruct:free",
            api_key_env="OPENROUTER_API_KEY",
            timeout=30
        ),
    )

    # Should not raise even though cerebras is disabled
    validate_provider_api_keys(providers, valid_settings)


# ============================================================================
# Full Config Validation Tests
# ============================================================================

def test_validate_config_success(tmp_path, valid_settings, monkeypatch):
    """Test full config validation with valid configs"""
    # Create test config directory
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Create valid YAML files
    (config_dir / "rate_limits.yaml").write_text("""
groq:
  rpm: 30
  burst: 40
  tokens_per_minute: 100000

cerebras:
  rpm: 20
  burst: 30
  tokens_per_minute: 80000

gemini:
  rpm: 15
  burst: 20
  tokens_per_minute: 60000

openrouter:
  rpm: 10
  burst: 15
  tokens_per_minute: 50000
""")

    (config_dir / "agent_chains.yaml").write_text("""
mary:
  primary: groq
  fallbacks:
    - cerebras
    - gemini

john:
  primary: cerebras
  fallbacks:
    - groq

alex:
  primary: gemini
  fallbacks:
    - openrouter
""")

    (config_dir / "providers.yaml").write_text("""
groq:
  enabled: true
  model: llama-3.1-70b-versatile
  api_key_env: GROQ_API_KEY
  base_url: https://api.groq.com/openai/v1
  timeout: 30

cerebras:
  enabled: true
  model: llama3.1-8b
  api_key_env: CEREBRAS_API_KEY
  base_url: https://api.cerebras.ai/v1
  timeout: 30

gemini:
  enabled: true
  model: gemini-1.5-flash
  api_key_env: GEMINI_API_KEY
  timeout: 30

openrouter:
  enabled: true
  model: meta-llama/llama-3.1-8b-instruct:free
  api_key_env: OPENROUTER_API_KEY
  base_url: https://openrouter.ai/api/v1
  timeout: 30
""")

    # Run validation
    config = validate_config(str(config_dir))

    # Verify ConfigBundle structure
    assert isinstance(config, ConfigBundle)
    assert config.settings is not None
    assert config.rate_limits is not None
    assert config.agent_chains is not None
    assert config.providers is not None


def test_validate_config_invalid_rate_limits(tmp_path, valid_settings, monkeypatch):
    """Test validate_config fails when rate limits invalid"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Invalid rate limits (rpm = 0)
    (config_dir / "rate_limits.yaml").write_text("""
groq:
  rpm: 0
  burst: 40
  tokens_per_minute: 100000

cerebras:
  rpm: 20
  burst: 30
  tokens_per_minute: 80000

gemini:
  rpm: 15
  burst: 20
  tokens_per_minute: 60000

openrouter:
  rpm: 10
  burst: 15
  tokens_per_minute: 50000
""")

    (config_dir / "agent_chains.yaml").write_text("""
mary:
  primary: groq
  fallbacks: [cerebras]

john:
  primary: cerebras
  fallbacks: []

alex:
  primary: gemini
  fallbacks: []
""")

    (config_dir / "providers.yaml").write_text("""
groq:
  enabled: true
  model: llama-3.1-70b-versatile
  api_key_env: GROQ_API_KEY
  timeout: 30

cerebras:
  enabled: true
  model: llama3.1-8b
  api_key_env: CEREBRAS_API_KEY
  timeout: 30

gemini:
  enabled: true
  model: gemini-1.5-flash
  api_key_env: GEMINI_API_KEY
  timeout: 30

openrouter:
  enabled: true
  model: meta-llama/llama-3.1-8b-instruct:free
  api_key_env: OPENROUTER_API_KEY
  timeout: 30
""")

    with pytest.raises(ConfigurationError) as exc_info:
        validate_config(str(config_dir))

    error_msg = str(exc_info.value).lower()
    assert ('rpm' in error_msg and 'greater than 0' in error_msg) or 'configuration validation failed' in error_msg
def test_validate_config_invalid_agent_chains(tmp_path, valid_settings, monkeypatch):
    """Test validate_config fails when agent chains invalid"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    (config_dir / "rate_limits.yaml").write_text("""
groq:
  rpm: 30
  burst: 40
  tokens_per_minute: 100000

cerebras:
  rpm: 20
  burst: 30
  tokens_per_minute: 80000

gemini:
  rpm: 15
  burst: 20
  tokens_per_minute: 60000

openrouter:
  rpm: 10
  burst: 15
  tokens_per_minute: 50000
""")

    # Invalid agent chain (unknown provider)
    (config_dir / "agent_chains.yaml").write_text("""
mary:
  primary: invalid_provider
  fallbacks: [cerebras]

john:
  primary: cerebras
  fallbacks: []

alex:
  primary: gemini
  fallbacks: []
""")

    (config_dir / "providers.yaml").write_text("""
groq:
  enabled: true
  model: llama-3.1-70b-versatile
  api_key_env: GROQ_API_KEY
  timeout: 30

cerebras:
  enabled: true
  model: llama3.1-8b
  api_key_env: CEREBRAS_API_KEY
  timeout: 30

gemini:
  enabled: true
  model: gemini-1.5-flash
  api_key_env: GEMINI_API_KEY
  timeout: 30

openrouter:
  enabled: true
  model: meta-llama/llama-3.1-8b-instruct:free
  api_key_env: OPENROUTER_API_KEY
  timeout: 30
""")

    with pytest.raises(ConfigurationError) as exc_info:
        validate_config(str(config_dir))

    error_msg = str(exc_info.value).lower()
    # Check for validation error mentioning the invalid provider or validation failure
    assert 'invalid_provider' in error_msg or 'validation' in error_msg
def test_config_bundle_structure(valid_settings, valid_rate_limits, valid_agent_chains, valid_providers):
    """Test ConfigBundle contains all required configs"""
    bundle = ConfigBundle(
        settings=valid_settings,
        rate_limits=valid_rate_limits,
        agent_chains=valid_agent_chains,
        providers=valid_providers
    )

    assert bundle.settings == valid_settings
    assert bundle.rate_limits == valid_rate_limits
    assert bundle.agent_chains == valid_agent_chains
    assert bundle.providers == valid_providers
