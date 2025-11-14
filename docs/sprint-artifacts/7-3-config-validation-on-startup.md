# Story 7.3: Config Validation on Startup

**Epic:** 7 - Configuration System
**Status:** In Progress
**Priority:** High
**Dependencies:** Story 7.1 (YAML Config Loader), Story 7.2 (Environment Variables Validation)

---

## Story Description

As a **system administrator**, I want **all configuration to be validated on application startup**, so that **I catch misconfigurations early before they cause runtime failures**.

**Context:**
- Story 7.1 created ConfigLoader for YAML files (rate_limits.yaml, agent_chains.yaml, providers.yaml)
- Story 7.2 created Settings for environment variables (API keys, Slack, log level)
- Currently these are validated independently, but there's no cross-validation
- Example issues: agent chain references non-existent provider, provider enabled but API key missing, rate limit RPM = 0

**Value:**
- **Fail-fast principle:** Catch errors at startup, not during first request
- **Clear error messages:** Guide users to fix configuration issues quickly
- **Prevent runtime failures:** Don't start application with invalid config
- **Cross-validation:** Ensure YAML configs and env vars are consistent

---

## Acceptance Criteria

### AC1: Rate Limits Validation
**Given** rate_limits.yaml is loaded
**When** startup validation runs
**Then** verify all rate limits have:
- `rpm > 0` (requests per minute must be positive)
- `burst >= rpm` (burst must be at least equal to rpm)
- `tokens_per_minute > 0` (token limit must be positive)

**Error Example:**
```
ConfigurationError: Invalid rate limit for 'groq': rpm must be > 0 (got 0)
```

### AC2: Agent Chains Validation
**Given** agent_chains.yaml is loaded
**When** startup validation runs
**Then** verify all agent chains have:
- Primary provider exists in providers.yaml
- All fallback providers exist in providers.yaml
- No duplicates in chain (primary not in fallbacks, no duplicate fallbacks)
- At least 1 provider in chain (primary)

**Error Example:**
```
ConfigurationError: Agent 'mary' references unknown provider 'invalid_provider' in chain
Available providers: groq, cerebras, gemini, openrouter
```

### AC3: Provider-to-API-Key Validation
**Given** providers.yaml and Settings are loaded
**When** startup validation runs
**Then** verify for each enabled provider:
- Corresponding API key exists in Settings
- API key is not empty

**Mapping:**
- `groq` provider → `GROQ_API_KEY` env var
- `cerebras` provider → `CEREBRAS_API_KEY` env var
- `gemini` provider → `GEMINI_API_KEY` env var
- `openrouter` provider → `OPENROUTER_API_KEY` env var
- `together` provider → `TOGETHER_API_KEY` env var (optional)

**Error Example:**
```
ConfigurationError: Provider 'groq' is enabled but GROQ_API_KEY is not set
Please set the API key in your .env file (see .env.example)
```

### AC4: Startup Validation Function
**Given** application is starting up
**When** `validate_config()` is called
**Then**:
- Load ConfigLoader and Settings
- Run all validation checks (AC1-AC3)
- If any validation fails, raise `ConfigurationError` with clear message
- If all validations pass, log success message
- Return validated config bundle for use by application

**Integration:**
```python
# In main.py lifespan():
try:
    config_bundle = validate_config()  # Raises ConfigurationError if invalid
    logger.info("✅ Configuration validated successfully")
except ConfigurationError as e:
    logger.error(f"❌ Configuration validation failed: {e}")
    raise  # Fail-fast: don't start app with invalid config
```

---

## Technical Notes

### 1. ConfigBundle Model
Create a model to bundle all validated configuration:

```python
# src/config/validation.py
from dataclasses import dataclass
from src.config.loader import ConfigLoader
from src.config.settings import Settings
from src.config.models import RateLimitsConfig, AgentChainsConfig, ProvidersConfig

@dataclass
class ConfigBundle:
    """Validated configuration bundle"""
    settings: Settings
    rate_limits: RateLimitsConfig
    agent_chains: AgentChainsConfig
    providers: ProvidersConfig
```

### 2. ConfigurationError Exception
```python
# src/config/validation.py
class ConfigurationError(Exception):
    """Raised when configuration validation fails"""
    pass
```

### 3. Validation Functions
Break down validation into smaller functions:

```python
def validate_rate_limits(rate_limits: RateLimitsConfig) -> None:
    """Validate rate limit values"""
    # Check rpm > 0, burst >= rpm, tokens_per_minute > 0
    # Raise ConfigurationError with specific details
    pass

def validate_agent_chains(
    agent_chains: AgentChainsConfig,
    providers: ProvidersConfig
) -> None:
    """Validate agent chains reference valid providers"""
    # Check primary/fallback providers exist
    # Check no duplicates
    # Raise ConfigurationError with specific details
    pass

def validate_provider_api_keys(
    providers: ProvidersConfig,
    settings: Settings
) -> None:
    """Validate enabled providers have API keys"""
    # Map provider name to settings field
    # Check enabled providers have non-empty keys
    # Raise ConfigurationError with specific details
    pass

def validate_config(config_dir: str = "config") -> ConfigBundle:
    """
    Validate all configuration on startup.

    Args:
        config_dir: Directory containing YAML config files

    Returns:
        ConfigBundle with validated configuration

    Raises:
        ConfigurationError: If any validation fails

    Example:
        >>> config = validate_config()
        >>> print(f"Loaded {len(config.agent_chains.mary.fallbacks)} fallbacks for Mary")
    """
    # 1. Load all configs
    loader = ConfigLoader(config_dir)
    settings = get_settings()

    rate_limits = loader.load_rate_limits()
    agent_chains = loader.load_agent_chains()
    providers = loader.load_providers()

    # 2. Run validations
    validate_rate_limits(rate_limits)
    validate_agent_chains(agent_chains, providers)
    validate_provider_api_keys(providers, settings)

    # 3. Return validated bundle
    return ConfigBundle(
        settings=settings,
        rate_limits=rate_limits,
        agent_chains=agent_chains,
        providers=providers
    )
```

### 4. Provider-to-API-Key Mapping
```python
PROVIDER_API_KEY_MAP = {
    'groq': 'groq_api_key',
    'cerebras': 'cerebras_api_key',
    'gemini': 'gemini_api_key',
    'openrouter': 'openrouter_api_key',
    'together': 'together_api_key',
}

def get_provider_api_key(provider_name: str, settings: Settings) -> Optional[str]:
    """Get API key for provider from settings"""
    field_name = PROVIDER_API_KEY_MAP.get(provider_name)
    if not field_name:
        return None
    return getattr(settings, field_name, None)
```

---

## Test Structure

### Test File: `tests/unit/test_config/test_validation.py`

```python
"""Unit tests for config validation"""

import pytest
from src.config.validation import (
    validate_rate_limits,
    validate_agent_chains,
    validate_provider_api_keys,
    validate_config,
    ConfigurationError,
    ConfigBundle
)

# Test 1: validate_rate_limits - valid config
def test_validate_rate_limits_success():
    """Test rate limits validation with valid config"""
    # All providers have rpm > 0, burst >= rpm, tokens_per_minute > 0
    # Should not raise

# Test 2: validate_rate_limits - rpm = 0
def test_validate_rate_limits_rpm_zero():
    """Test rate limits validation fails when rpm = 0"""
    # groq.rpm = 0
    # Should raise ConfigurationError mentioning 'rpm must be > 0'

# Test 3: validate_rate_limits - burst < rpm
def test_validate_rate_limits_burst_less_than_rpm():
    """Test rate limits validation fails when burst < rpm"""
    # groq.burst = 10, groq.rpm = 20
    # Should raise ConfigurationError mentioning 'burst must be >= rpm'

# Test 4: validate_rate_limits - tokens_per_minute = 0
def test_validate_rate_limits_tokens_zero():
    """Test rate limits validation fails when tokens_per_minute = 0"""
    # Should raise ConfigurationError

# Test 5: validate_agent_chains - valid config
def test_validate_agent_chains_success():
    """Test agent chains validation with valid config"""
    # All chains reference existing providers
    # No duplicates
    # Should not raise

# Test 6: validate_agent_chains - unknown primary provider
def test_validate_agent_chains_unknown_primary():
    """Test agent chains validation fails with unknown primary"""
    # mary.primary = 'invalid_provider'
    # Should raise ConfigurationError with available providers list

# Test 7: validate_agent_chains - unknown fallback provider
def test_validate_agent_chains_unknown_fallback():
    """Test agent chains validation fails with unknown fallback"""
    # mary.fallbacks = ['groq', 'invalid_provider']
    # Should raise ConfigurationError

# Test 8: validate_agent_chains - duplicate in chain
def test_validate_agent_chains_duplicate():
    """Test agent chains validation fails with duplicate provider"""
    # mary.primary = 'groq', mary.fallbacks = ['groq', 'cerebras']
    # Should raise ConfigurationError about duplicate

# Test 9: validate_provider_api_keys - all keys present
def test_validate_provider_api_keys_success():
    """Test provider API keys validation with all keys"""
    # All enabled providers have API keys in Settings
    # Should not raise

# Test 10: validate_provider_api_keys - missing required key
def test_validate_provider_api_keys_missing():
    """Test provider API keys validation fails when key missing"""
    # groq provider enabled but groq_api_key = None in Settings
    # Should raise ConfigurationError with provider name and env var

# Test 11: validate_provider_api_keys - optional provider without key
def test_validate_provider_api_keys_optional_missing():
    """Test optional provider without API key is allowed"""
    # together provider enabled but together_api_key = None
    # Should not raise (together is optional)

# Test 12: validate_config - full integration success
def test_validate_config_success():
    """Test full config validation with valid configs"""
    # Load from test fixtures
    # All validations pass
    # Returns ConfigBundle with all configs

# Test 13: validate_config - fails on invalid rate limits
def test_validate_config_invalid_rate_limits():
    """Test validate_config fails when rate limits invalid"""
    # rpm = 0 in rate_limits.yaml
    # Should raise ConfigurationError early

# Test 14: validate_config - fails on invalid agent chains
def test_validate_config_invalid_agent_chains():
    """Test validate_config fails when agent chains invalid"""
    # Unknown provider in chain
    # Should raise ConfigurationError

# Test 15: validate_config - fails on missing API key
def test_validate_config_missing_api_key():
    """Test validate_config fails when API key missing"""
    # Provider enabled but API key not set
    # Should raise ConfigurationError

# Test 16: ConfigBundle structure
def test_config_bundle_structure():
    """Test ConfigBundle contains all required configs"""
    # Create ConfigBundle manually
    # Verify has settings, rate_limits, agent_chains, providers attributes
```

**Expected Test Count:** 16 tests

---

## Definition of Done

- [ ] `src/config/validation.py` created with:
  - [ ] `ConfigurationError` exception class
  - [ ] `ConfigBundle` dataclass
  - [ ] `validate_rate_limits()` function
  - [ ] `validate_agent_chains()` function
  - [ ] `validate_provider_api_keys()` function
  - [ ] `validate_config()` main function
  - [ ] `PROVIDER_API_KEY_MAP` constant

- [ ] `tests/unit/test_config/test_validation.py` created with:
  - [ ] 16 tests covering all validation scenarios
  - [ ] Test fixtures for valid/invalid configs
  - [ ] All tests passing

- [ ] `src/main.py` updated:
  - [ ] Import `validate_config` from `src.config.validation`
  - [ ] Call `validate_config()` in `lifespan()` startup
  - [ ] Handle `ConfigurationError` with clear logging
  - [ ] Use `ConfigBundle` in application

- [ ] Test fixtures created:
  - [ ] `tests/fixtures/config/invalid_rate_limits_rpm_zero.yaml`
  - [ ] `tests/fixtures/config/invalid_agent_chains_unknown_provider.yaml`
  - [ ] Other invalid config fixtures as needed

- [ ] All existing tests still passing
- [ ] Sprint status updated: Story 7.3 marked as DONE
- [ ] Epic 7 progress: 3/5 stories complete (60%)

---

## Integration Example

```python
# src/main.py
from src.config.validation import validate_config, ConfigurationError

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("🚀 Initializing Squad API...")

    try:
        # Validate all configuration (Settings + YAML configs)
        config = validate_config(config_dir="config")
        logger.info("✅ Configuration validated successfully")

        # Use validated config throughout application
        settings = config.settings
        rate_limits = config.rate_limits
        agent_chains = config.agent_chains
        providers = config.providers

    except ConfigurationError as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        raise RuntimeError(
            f"Invalid configuration detected on startup. "
            f"Please fix the following issue: {e}"
        ) from e

    # ... rest of startup logic
```

---

## Error Message Examples

### Rate Limits Error
```
ConfigurationError: Invalid rate limit configuration for provider 'groq':
  - rpm must be > 0 (got 0)

Fix: Edit config/rate_limits.yaml and set groq.rpm to a positive value (e.g., 30)
```

### Agent Chains Error
```
ConfigurationError: Agent chain 'mary' references unknown provider 'invalid_provider'

Available providers in config/providers.yaml:
  - groq
  - cerebras
  - gemini
  - openrouter

Fix: Edit config/agent_chains.yaml and use a valid provider name
```

### API Key Error
```
ConfigurationError: Provider 'groq' is enabled in config/providers.yaml but API key is missing

Required environment variable: GROQ_API_KEY
Get your API key at: https://console.groq.com/keys

Fix: Add GROQ_API_KEY to your .env file (see .env.example for template)
```

---

## Notes

- **Validation order matters:** Load all configs first, then validate cross-references
- **Clear error messages:** Include provider/agent name, expected value, actual value, fix instructions
- **Fail-fast:** Don't start application if any validation fails
- **Logging:** Log validation success and failure for troubleshooting
- **Optional providers:** Together AI is optional, don't fail if API key missing unless provider is actually used
- **Test coverage goal:** 90%+ on `src/config/validation.py`

---

## Related Stories

- ✅ Story 7.1: YAML Config Loader (dependency)
- ✅ Story 7.2: Environment Variables Validation (dependency)
- ⏳ Story 7.4: Config Documentation (will document validation rules)
- ⏳ Story 7.5: Config Change Monitoring (will re-run validation on reload)
