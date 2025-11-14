#!/usr/bin/env python3
"""
Simple debug script to verify the fix
"""

import os
from dotenv import load_dotenv

print("=== Environment Variable Debug ===")

# Load .env file
load_dotenv()

print("1. Testing environment variable loading...")

# Test each API key
api_keys = {
    'ANTHROPIC_API_KEY': 'ANTHROPIC_API_KEY',
    'GROQ_API_KEY': 'GROQ_API_KEY',
    'GEMINI_API_KEY': 'GEMINI_API_KEY',
    'OPENROUTER_API_KEY': 'OPENROUTER_API_KEY',
    'CEREBRAS_API_KEY': 'CEREBRAS_API_KEY'
}

for env_var, display_name in api_keys.items():
    value = os.getenv(env_var)
    if value:
        print(f"OK {display_name}: {value[:10]}... ({len(value)} chars)")
    else:
        print(f"MISSING {display_name}: NOT FOUND")

print("\n2. Testing provider factory initialization...")

try:
    from src.providers.factory import ProviderFactory

    factory = ProviderFactory()
    print(f"OK Provider factory created with {len(factory.PROVIDER_CLASSES)} provider types")

    # Test creating a single provider (groq - should work since we have the API key)
    groq_config = {
        'type': 'groq',
        'enabled': True,
        'model': 'llama-3.3-70b-versatile',
        'api_key_env': 'GROQ_API_KEY',
        'timeout': 30,
        'name': 'groq_test'
    }

    groq_provider = factory.create_provider('groq_test', groq_config)
    if groq_provider:
        print(f"OK Groq provider created successfully")
    else:
        print(f"FAILED to create Groq provider")

except Exception as e:
    print(f"ERROR testing provider factory: {e}")
    import traceback
    traceback.print_exc()

print("\n3. Testing config loading...")

try:
    from src.config.validation import validate_config
    config = validate_config(config_dir="config")
    print(f"OK Configuration loaded successfully")

    # Test provider-specific config
    if hasattr(config, 'providers') and config.providers:
        print(f"OK Provider config found")
        providers = config.providers

        # Check each provider
        for provider_name in ['groq', 'anthropic', 'gemini', 'cerebras', 'openrouter']:
            if hasattr(providers, provider_name):
                provider_config = getattr(providers, provider_name)
                print(f"OK {provider_name}: enabled={provider_config.enabled}")
            else:
                print(f"NOT_FOUND {provider_name}: not found in config")
    else:
        print(f"FAILED No provider config found")

except Exception as e:
    print(f"ERROR loading config: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Debug Complete ===")
