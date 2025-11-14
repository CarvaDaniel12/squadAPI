# Squad API - Configuration Guide

**Last Updated:** 2025-11-13
**Epic:** 7 - Configuration System
**Version:** 1.0.0

---

## Table of Contents

1. [Overview](#overview)
2. [Environment Variables](#environment-variables)
3. [YAML Configuration Files](#yaml-configuration-files)
4. [Validation Rules](#validation-rules)
5. [Quick Start](#quick-start)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

---

## Overview

Squad API uses a **two-layer configuration system**:

1. **Environment Variables** (`.env`) - API keys, secrets, application settings
2. **YAML Config Files** (`config/`) - Rate limits, agent chains, provider settings

All configuration is **validated on startup** using Pydantic models. The application will **fail-fast** with clear error messages if configuration is invalid.

### Configuration Flow

```
Application Startup
    ↓
Load .env file → Settings (pydantic-settings)
    ↓
Load config/*.yaml → ConfigLoader (Pydantic models)
    ↓
validate_config() → Cross-validation
    ↓
✅ ConfigBundle → Ready to use
```

---

## Environment Variables

Environment variables are loaded from `.env` file and validated using **pydantic-settings**.

### Required Variables

These **must** be set for the application to start:

```bash
# Groq API Key (REQUIRED)
# Get yours at: https://console.groq.com/keys
GROQ_API_KEY=gsk_your_groq_api_key_here

# Cerebras API Key (REQUIRED)
# Get yours at: https://cloud.cerebras.ai/
CEREBRAS_API_KEY=csk_your_cerebras_api_key_here

# Google Gemini API Key (REQUIRED)
# Get yours at: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=AIzaSy_your_gemini_api_key_here

# OpenRouter API Key (REQUIRED)
# Get yours at: https://openrouter.ai/keys
OPENROUTER_API_KEY=sk-or-v1-your_openrouter_api_key_here
```

### Optional Variables

These have sensible defaults but can be customized:

```bash
# Together AI API Key (optional - for future use)
# Get yours at: https://api.together.xyz/settings/api-keys
TOGETHER_API_KEY=your_together_api_key_here

# Slack Webhook URL for alerts (optional - Epic 6)
# Create webhook at: https://api.slack.com/messaging/webhooks
# Format: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX

# Enable Slack alerts (true/false)
SLACK_ALERTS_ENABLED=false

# Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Redis connection URL
REDIS_URL=redis://localhost:6379

# PostgreSQL connection URL
POSTGRES_URL=postgresql://squad:squad@localhost:5432/squad_api
```

### Validation Rules

- **Required fields** must be set (non-empty strings)
- **Slack webhook URL** must start with `https://hooks.slack.com/`
- **Log level** must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL (case-insensitive)
- **Together API key** is optional (provider can be disabled)

### Getting API Keys

| Provider | URL | Notes |
|----------|-----|-------|
| **Groq** | https://console.groq.com/keys | Free tier available, fast inference |
| **Cerebras** | https://cloud.cerebras.ai/ | High-performance LLM inference |
| **Gemini** | https://aistudio.google.com/app/apikey | Google's Gemini models |
| **OpenRouter** | https://openrouter.ai/keys | Access to multiple models |
| **Together** | https://api.together.xyz/settings/api-keys | Optional, for future use |

---

## YAML Configuration Files

YAML config files are located in `config/` directory and validated using **Pydantic models**.

### 1. Rate Limits (`config/rate_limits.yaml`)

Defines rate limiting rules for each provider.

**Example:**
```yaml
groq:
  rpm: 30                    # Requests per minute
  burst: 40                  # Burst capacity
  tokens_per_minute: 100000  # Token limit per minute

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

# Optional: Together AI (if using)
together:
  rpm: 25
  burst: 35
  tokens_per_minute: 90000
```

**Validation Rules:**
- `rpm` must be > 0 (requests per minute)
- `burst` must be >= `rpm` (burst capacity must be at least equal to rpm)
- `tokens_per_minute` must be > 0 (token budget must be positive)

**Common Values:**
- **Free tier providers:** rpm: 10-15, burst: 15-20
- **Paid tier providers:** rpm: 30-60, burst: 40-80
- **Token limits:** Usually 50k-200k tokens per minute

### 2. Agent Chains (`config/agent_chains.yaml`)

Defines fallback chains for each agent.

**Example:**
```yaml
mary:
  primary: groq              # Primary provider
  fallbacks:                 # Fallback providers (in order)
    - cerebras
    - gemini
    - openrouter

john:
  primary: cerebras
  fallbacks:
    - groq
    - gemini

alex:
  primary: gemini
  fallbacks:
    - openrouter
    - groq

# Optional agents
amelia:
  primary: openrouter
  fallbacks:
    - groq

bob:
  primary: together
  fallbacks:
    - groq
    - cerebras
```

**Validation Rules:**
- `primary` provider must exist in `providers.yaml`
- All `fallbacks` providers must exist in `providers.yaml`
- No duplicates allowed (primary can't be in fallbacks, no duplicate fallbacks)
- At least 1 provider required (primary)

**Best Practices:**
- **Fast providers first:** Use Groq/Cerebras as primary for low-latency
- **Diverse fallbacks:** Mix different providers for resilience
- **Cost-effective chains:** Put free-tier providers in fallback
- **3-4 providers per chain:** Balance resilience vs complexity

### 3. Providers (`config/providers.yaml`)

Defines provider configurations (models, timeouts, etc.).

**Example:**
```yaml
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

# Optional: Together AI
together:
  enabled: false
  model: meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
  api_key_env: TOGETHER_API_KEY
  base_url: https://api.together.xyz/v1
  timeout: 30
```

**Validation Rules:**
- **Enabled providers** must have corresponding API key set in `.env`
- **Disabled providers** can skip API key
- `timeout` is in seconds (recommended: 30-60s)
- `model` must be valid for the provider

**Recommended Models:**
- **Groq:** `llama-3.1-70b-versatile` (fast, high quality)
- **Cerebras:** `llama3.1-8b` (ultra-fast, good quality)
- **Gemini:** `gemini-1.5-flash` (free tier, balanced)
- **OpenRouter:** `meta-llama/llama-3.1-8b-instruct:free` (free tier)

---

## Validation Rules

All configuration is validated on startup using `validate_config()`.

### Validation Steps

1. **Load Settings** from `.env` (pydantic-settings validation)
2. **Load YAML configs** (Pydantic model validation)
3. **Cross-validate:**
   - Rate limits have positive values
   - Agent chains reference existing providers
   - Enabled providers have API keys

### Error Messages

**Missing API Key:**
```
ConfigurationError: Provider 'groq' is enabled in config/providers.yaml but API key is missing

Required environment variable: GROQ_API_KEY
Get your API key at: https://console.groq.com/keys

Fix: Add GROQ_API_KEY to your .env file (see .env.example for template)
```

**Invalid Rate Limit:**
```
ConfigurationError: Invalid rate limit configuration for provider 'groq':
  - rpm must be > 0 (got 0)

Fix: Edit config/rate_limits.yaml and set groq.rpm to a positive value (e.g., 30)
```

**Unknown Provider in Chain:**
```
ConfigurationError: Agent chain 'mary' references unknown provider 'invalid_provider'

Available providers in config/providers.yaml:
  - groq
  - cerebras
  - gemini
  - openrouter

Fix: Edit config/agent_chains.yaml and use a valid provider name
```

---

## Quick Start

### 1. Copy Environment Template

```bash
cp .env.example .env
```

### 2. Set Required API Keys

Edit `.env` and add your API keys:

```bash
GROQ_API_KEY=gsk_your_actual_key_here
CEREBRAS_API_KEY=csk_your_actual_key_here
GEMINI_API_KEY=AIzaSy_your_actual_key_here
OPENROUTER_API_KEY=sk-or-v1-your_actual_key_here
```

### 3. Review YAML Configs

Check `config/` directory:
- ✅ `rate_limits.yaml` - Adjust limits based on your tier
- ✅ `agent_chains.yaml` - Customize fallback chains
- ✅ `providers.yaml` - Enable/disable providers

### 4. Start Application

```bash
# With Docker
docker-compose up

# Without Docker
uvicorn src.main:app --reload
```

### 5. Verify Configuration

Check startup logs:

```
🚀 Initializing Squad API...
🔍 Validating configuration...
✅ Configuration validated successfully
Settings loaded: 4/4 required API keys, log_level=INFO, slack_alerts=False
✅ Loaded 3 BMad agents
✅ Squad API initialized!
```

---

## Troubleshooting

### Issue: "Field required" error on startup

**Cause:** Missing required API key in `.env`

**Solution:**
1. Check which key is missing in the error message
2. Add the key to `.env` file
3. Ensure the key is not empty
4. Restart the application

### Issue: "Provider X is enabled but API key is missing"

**Cause:** Provider enabled in `providers.yaml` but API key not set

**Solution:**
1. **Option A:** Add the API key to `.env`
2. **Option B:** Disable the provider in `config/providers.yaml`:
   ```yaml
   provider_name:
     enabled: false  # Change to false
   ```

### Issue: "Unknown provider in agent chain"

**Cause:** Agent chain references provider that doesn't exist or is disabled

**Solution:**
1. Check available providers in `config/providers.yaml`
2. Update agent chain in `config/agent_chains.yaml` to use existing provider
3. Or enable the missing provider in `providers.yaml`

### Issue: "rpm must be > 0"

**Cause:** Invalid rate limit value in `rate_limits.yaml`

**Solution:**
1. Open `config/rate_limits.yaml`
2. Set `rpm` to positive value (e.g., 30)
3. Ensure `burst >= rpm`
4. Ensure `tokens_per_minute > 0`

### Issue: "Slack webhook must start with https://hooks.slack.com/"

**Cause:** Invalid Slack webhook URL format

**Solution:**
1. Get correct webhook URL from Slack: https://api.slack.com/messaging/webhooks
2. Update `SLACK_WEBHOOK_URL` in `.env`
3. Format: `https://hooks.slack.com/services/T.../B.../XXX...`

---

## Best Practices

### Security

- ✅ **Never commit `.env`** - Keep API keys secret
- ✅ **Use `.env.example`** - Template without secrets
- ✅ **Rotate keys regularly** - Update API keys periodically
- ✅ **Limit key permissions** - Use read-only keys when possible
- ✅ **Monitor usage** - Watch for unexpected API usage

### Performance

- ✅ **Set realistic rate limits** - Match your provider tier
- ✅ **Use burst capacity** - Handle traffic spikes gracefully
- ✅ **Fast providers first** - Groq/Cerebras for low latency
- ✅ **Diverse fallback chains** - Mix fast and reliable providers
- ✅ **Monitor metrics** - Track success rates and latencies

### Reliability

- ✅ **3-4 fallback providers** - Balance resilience vs complexity
- ✅ **Test all providers** - Ensure API keys work
- ✅ **Mix provider types** - Don't rely on single vendor
- ✅ **Set reasonable timeouts** - 30-60s recommended
- ✅ **Enable Slack alerts** - Get notified of issues

### Cost Optimization

- ✅ **Free tier providers** - Use Gemini/OpenRouter free models
- ✅ **Rate limit compliance** - Avoid overage charges
- ✅ **Token tracking** - Monitor token consumption
- ✅ **Disable unused providers** - Reduce complexity
- ✅ **Review usage monthly** - Optimize based on patterns

### Development Workflow

- ✅ **Local `.env` file** - For development
- ✅ **Separate configs per environment** - dev/staging/prod
- ✅ **Version control YAML configs** - Track changes
- ✅ **Test config changes** - Validate before deploying
- ✅ **Document customizations** - Add comments in YAML

---

## Configuration Files Reference

### Directory Structure

```
squad-api/
├── .env                          # Environment variables (DO NOT COMMIT)
├── .env.example                  # Template (commit this)
├── config/
│   ├── rate_limits.yaml          # Rate limiting rules
│   ├── agent_chains.yaml         # Agent fallback chains
│   └── providers.yaml            # Provider configurations
├── src/
│   └── config/
│       ├── settings.py           # Environment variable validation
│       ├── loader.py             # YAML config loader
│       ├── models.py             # Pydantic models
│       └── validation.py         # Cross-validation logic
└── docs/
    └── configuration.md          # This guide
```

### Configuration Classes

```python
from src.config.validation import validate_config

# Load and validate all configuration
config = validate_config(config_dir="config")

# Access validated config
settings = config.settings              # Settings instance
rate_limits = config.rate_limits        # RateLimitsConfig instance
agent_chains = config.agent_chains      # AgentChainsConfig instance
providers = config.providers            # ProvidersConfig instance

# Example usage
groq_rpm = config.rate_limits.groq.rpm                  # 30
mary_primary = config.agent_chains.mary.primary         # "groq"
groq_enabled = config.providers.groq.enabled            # True
api_key_summary = config.settings.get_api_key_summary() # {'groq': True, ...}
```

---

## Advanced Configuration

### Custom Rate Limits Per Agent

Currently not supported directly, but you can:
1. Create agent-specific providers in `providers.yaml`
2. Configure different rate limits in `rate_limits.yaml`
3. Assign agents to specific providers in `agent_chains.yaml`

### Dynamic Configuration Reload

Coming in Story 7.5 (Config Change Monitoring):
- Hot-reload of YAML configs without restart
- File watching with `watchdog`
- Graceful config updates

### Multiple Environments

**Development:**
```bash
# .env.development
LOG_LEVEL=DEBUG
SLACK_ALERTS_ENABLED=false
```

**Production:**
```bash
# .env.production
LOG_LEVEL=INFO
SLACK_ALERTS_ENABLED=true
```

**Usage:**
```bash
# Development
cp .env.development .env

# Production
cp .env.production .env
```

### Monitoring Configuration

**Prometheus Metrics:**
- Provider success rates
- Rate limit utilization
- Token consumption
- Fallback frequencies

**Slack Alerts:**
- 429 rate limit errors (5min cooldown)
- High latency warnings (15min cooldown)
- Provider health issues (15min cooldown)

---

## FAQ

### Q: Can I use the same API key for multiple providers?

**A:** No, each provider requires its own API key from their respective platforms.

### Q: What happens if a provider is disabled?

**A:** Disabled providers are skipped in fallback chains. If an agent's primary provider is disabled, the first enabled fallback is used.

### Q: Can I add custom providers?

**A:** Yes, implement a provider class extending `BaseProvider` and add configuration to YAML files. See `src/providers/` for examples.

### Q: How do I test my configuration?

**A:** Run the application with `LOG_LEVEL=DEBUG` and check startup logs. All validation errors will be logged clearly.

### Q: Can I disable validation temporarily?

**A:** No, validation is always enforced to prevent runtime failures. Fix configuration issues instead.

### Q: What's the difference between rpm and burst?

**A:** `rpm` is sustained requests per minute. `burst` is maximum concurrent requests allowed. Example: rpm=30, burst=40 allows 40 quick requests, then throttles to 30/min.

### Q: How do I update configuration in production?

**A:**
1. Update YAML files or `.env`
2. Restart the application (required for env vars)
3. For YAML configs, Story 7.5 will enable hot-reload

---

## Support

**Documentation:**
- Architecture: `docs/architecture.md`
- API Reference: `docs/API-KEYS-SETUP.md`
- Troubleshooting: `docs/runbooks/`

**Issues:**
- Check logs with `LOG_LEVEL=DEBUG`
- Review error messages carefully
- Verify all API keys are valid
- Test providers individually

**Need Help?**
- Review this guide thoroughly
- Check `docs/runbooks/troubleshooting-guide.md`
- Run validation: `python -c "from src.config.validation import validate_config; validate_config()"`

---

**Epic 7: Configuration System** - 3/5 stories complete
**Story 7.4: Config Documentation** - ✅ DONE
