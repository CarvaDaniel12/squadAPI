"""Unit tests for ConfigLoader

Tests config loading, validation, and error handling for all config types.
"""

import pytest
import yaml
from pathlib import Path
from pydantic import ValidationError

from src.config.loader import ConfigLoader
from src.config.models import (
    RateLimitsConfig,
    AgentChainsConfig,
    ProvidersConfig
)


# Fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "config"


@pytest.fixture
def valid_config_dir():
    """Path to valid config fixtures"""
    return str(FIXTURES_DIR)


@pytest.fixture
def loader(valid_config_dir):
    """ConfigLoader with valid fixtures directory"""
    return ConfigLoader(config_dir=valid_config_dir)


# ============================================================================
# ConfigLoader Initialization Tests
# ============================================================================

def test_config_loader_init_success(valid_config_dir):
    """Test ConfigLoader initialization with valid directory"""
    loader = ConfigLoader(config_dir=valid_config_dir)
    assert loader.config_dir == Path(valid_config_dir)


def test_config_loader_init_directory_not_found():
    """Test ConfigLoader fails with non-existent directory"""
    with pytest.raises(FileNotFoundError) as exc_info:
        ConfigLoader(config_dir="./nonexistent_dir")

    assert "Config directory not found" in str(exc_info.value)


# ============================================================================
# Rate Limits Config Tests
# ============================================================================

def test_load_rate_limits_success(loader):
    """Test successful rate_limits.yaml load"""
    config = loader.load_rate_limits()

    # Check type
    assert isinstance(config, RateLimitsConfig)

    # Check Groq config
    assert config.groq.rpm == 12
    assert config.groq.burst == 15
    assert config.groq.tokens_per_minute == 14400

    # Check Cerebras config
    assert config.cerebras.rpm == 20
    assert config.cerebras.burst == 25

    # Check Gemini config
    assert config.gemini.rpm == 15

    # Check OpenRouter config
    assert config.openrouter.rpm == 10


def test_load_rate_limits_file_not_found():
    """Test rate_limits.yaml load fails when file missing"""
    loader = ConfigLoader(config_dir="./config")  # Real config dir

    # Temporarily create loader with nonexistent file
    loader.config_dir = Path("./nonexistent")

    with pytest.raises(FileNotFoundError) as exc_info:
        loader.load_rate_limits()

    assert "Config file not found" in str(exc_info.value)
    assert "rate_limits.yaml" in str(exc_info.value)


def test_load_rate_limits_invalid_yaml(tmp_path):
    """Test rate_limits.yaml load fails with invalid YAML syntax"""
    # Create temp config dir with invalid YAML
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    invalid_file = config_dir / "rate_limits.yaml"
    # This YAML will fail to parse (unclosed bracket in list)
    invalid_file.write_text("groq:\n  rpm: [1, 2,\n  burst: 15")

    loader = ConfigLoader(config_dir=str(config_dir))

    with pytest.raises((yaml.YAMLError, ValidationError)):
        # Accept either YAML parse error or validation error
        loader.load_rate_limits()


def test_load_rate_limits_validation_error(tmp_path):
    """Test rate_limits.yaml load fails with invalid values"""
    # Create temp config dir with invalid data (rpm = 0)
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    invalid_file = config_dir / "rate_limits.yaml"
    invalid_file.write_text("""
groq:
  rpm: 0
  burst: 15
  tokens_per_minute: 14400

cerebras:
  rpm: 20
  burst: 25
  tokens_per_minute: 1000000

gemini:
  rpm: 15
  burst: 20
  tokens_per_minute: 1500000

openrouter:
  rpm: 10
  burst: 12
  tokens_per_minute: 100000
""")

    loader = ConfigLoader(config_dir=str(config_dir))

    with pytest.raises(ValidationError) as exc_info:
        loader.load_rate_limits()

    # Check error mentions rpm validation
    assert "rpm" in str(exc_info.value).lower()


# ============================================================================
# Agent Chains Config Tests
# ============================================================================

def test_load_agent_chains_success(loader):
    """Test successful agent_chains.yaml load"""
    config = loader.load_agent_chains()

    # Check type
    assert isinstance(config, AgentChainsConfig)

    # Check Mary config
    assert config.mary.primary == "groq"
    assert config.mary.fallbacks == ["cerebras", "gemini"]

    # Check John config
    assert config.john.primary == "cerebras"
    assert config.john.fallbacks == ["groq"]

    # Check Alex config
    assert config.alex.primary == "gemini"
    assert config.alex.fallbacks == ["openrouter"]


def test_load_agent_chains_file_not_found():
    """Test agent_chains.yaml load fails when file missing"""
    loader = ConfigLoader(config_dir="./config")
    loader.config_dir = Path("./nonexistent")

    with pytest.raises(FileNotFoundError) as exc_info:
        loader.load_agent_chains()

    assert "Config file not found" in str(exc_info.value)
    assert "agent_chains.yaml" in str(exc_info.value)


def test_load_agent_chains_invalid_yaml(tmp_path):
    """Test agent_chains.yaml load fails with invalid YAML syntax"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    invalid_file = config_dir / "agent_chains.yaml"
    invalid_file.write_text("mary:\n  primary: [ invalid")

    loader = ConfigLoader(config_dir=str(config_dir))

    with pytest.raises(yaml.YAMLError):
        loader.load_agent_chains()


def test_load_agent_chains_validation_error(tmp_path):
    """Test agent_chains.yaml load fails with duplicate providers"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Primary in fallbacks (invalid)
    invalid_file = config_dir / "agent_chains.yaml"
    invalid_file.write_text("""
mary:
  primary: groq
  fallbacks:
    - groq
    - cerebras

john:
  primary: cerebras
  fallbacks: []

alex:
  primary: gemini
  fallbacks: []
""")

    loader = ConfigLoader(config_dir=str(config_dir))

    with pytest.raises(ValidationError) as exc_info:
        loader.load_agent_chains()

    # Check error mentions duplicate or primary
    error_msg = str(exc_info.value).lower()
    assert "primary" in error_msg or "fallback" in error_msg


# ============================================================================
# Providers Config Tests
# ============================================================================

def test_load_providers_success(loader):
    """Test successful providers.yaml load"""
    config = loader.load_providers()

    # Check type
    assert isinstance(config, ProvidersConfig)

    # Check Groq config
    assert config.groq.enabled is True
    assert config.groq.model == "llama-3.3-70b-versatile"
    assert config.groq.api_key_env == "GROQ_API_KEY"
    assert config.groq.timeout == 30

    # Check Cerebras config
    assert config.cerebras.model == "llama3.1-70b"

    # Check OpenRouter has base_url
    assert config.openrouter.base_url == "https://openrouter.ai/api/v1"


def test_load_providers_file_not_found():
    """Test providers.yaml load fails when file missing"""
    loader = ConfigLoader(config_dir="./config")
    loader.config_dir = Path("./nonexistent")

    with pytest.raises(FileNotFoundError) as exc_info:
        loader.load_providers()

    assert "Config file not found" in str(exc_info.value)
    assert "providers.yaml" in str(exc_info.value)


def test_load_providers_invalid_yaml(tmp_path):
    """Test providers.yaml load fails with invalid YAML syntax"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    invalid_file = config_dir / "providers.yaml"
    invalid_file.write_text("groq: {invalid")

    loader = ConfigLoader(config_dir=str(config_dir))

    with pytest.raises(yaml.YAMLError):
        loader.load_providers()


def test_load_providers_validation_error(tmp_path):
    """Test providers.yaml load fails with missing required fields"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Missing 'model' field (required)
    invalid_file = config_dir / "providers.yaml"
    invalid_file.write_text("""
groq:
  enabled: true
  api_key_env: GROQ_API_KEY
  timeout: 30

cerebras:
  enabled: true
  model: llama3.1-70b
  api_key_env: CEREBRAS_API_KEY

gemini:
  enabled: true
  model: gemini-1.5-flash
  api_key_env: GEMINI_API_KEY

openrouter:
  enabled: true
  model: meta-llama/llama-3.3-70b-instruct
  api_key_env: OPENROUTER_API_KEY
""")

    loader = ConfigLoader(config_dir=str(config_dir))

    with pytest.raises(ValidationError) as exc_info:
        loader.load_providers()

    # Check error mentions missing field
    assert "model" in str(exc_info.value).lower() or "field required" in str(exc_info.value).lower()


# ============================================================================
# Edge Cases
# ============================================================================

def test_load_empty_file(tmp_path):
    """Test config load fails with empty YAML file"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    empty_file = config_dir / "rate_limits.yaml"
    empty_file.write_text("")

    loader = ConfigLoader(config_dir=str(config_dir))

    with pytest.raises(ValueError) as exc_info:
        loader.load_rate_limits()

    assert "Empty config file" in str(exc_info.value)
