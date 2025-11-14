#!/usr/bin/env python3
"""
Debug script for provider initialization issues
"""

import os
import sys
from pathlib import Path

# Set PYTHONPATH
sys.path.append('.')

from dotenv import load_dotenv

# Load environment variables
project_root = Path('.')
env_paths = [
    project_root / '.env',
    Path.cwd() / '.env',
    Path('.env'),
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path, override=False)
        print(f'[OK] Loaded .env from: {env_path}')
        break
else:
    print('[WARN] No .env file found')

# Check API keys
api_keys = ['OPENAI_API_KEY', 'GROQ_API_KEY', 'OPENROUTER_API_KEY', 'CEREBRAS_API_KEY', 'ANTHROPIC_API_KEY', 'GEMINI_API_KEY']
for key in api_keys:
    value = os.getenv(key)
    if value:
        print(f'[OK] {key}: {value[:20]}...')
    else:
        print(f'[FAIL] {key}: Not set')

print('\n' + '='*50)

from src.config.validation import validate_config
from src.providers.factory import ProviderFactory

try:
    print('Validating configuration...')
    config = validate_config(config_dir='config')
    providers = config.providers

    print(f'[OK] Configuration validated successfully')
    print(f'[INFO] Found {len(providers.__dict__)} providers in config')

    for provider_name, provider_config in providers.__dict__.items():
        if hasattr(provider_config, 'enabled') and provider_config.enabled:
            print(f'[OK] Provider {provider_name}: enabled={provider_config.enabled}, model={provider_config.model}')
        elif hasattr(provider_config, 'enabled'):
            print(f'[WARN] Provider {provider_name}: enabled={provider_config.enabled} (disabled)')

    print('\nTesting ProviderFactory...')
    factory = ProviderFactory()
    print(f'[OK] Factory initialized with {len(factory.PROVIDER_CLASSES)} provider classes')
    print(f'[INFO] Available provider types: {list(factory.PROVIDER_CLASSES.keys())}')

    # Create providers
    print('\nCreating provider instances...')
    llm_providers = {}
    all_provider_names = ['groq', 'gemini', 'cerebras', 'openrouter', 'anthropic', 'openai']

    for provider_name in all_provider_names:
        provider_config = getattr(providers, provider_name, None)
        if provider_config and provider_config.enabled:
            provider_dict = {
                'name': provider_name,
                'type': provider_name,
                'enabled': provider_config.enabled,
                'model': provider_config.model,
                'api_key_env': provider_config.api_key_env,
                'timeout': provider_config.timeout,
                'rpm_limit': getattr(provider_config, 'rpm_limit', 60),
                'tpm_limit': getattr(provider_config, 'tpm_limit', 100000),
            }
            if hasattr(provider_config, 'base_url') and provider_config.base_url:
                provider_dict['base_url'] = provider_config.base_url

            try:
                provider_instance = factory.create_provider(provider_name, provider_dict)
                if provider_instance:
                    llm_providers[provider_name] = provider_instance
                    print(f'[OK] Successfully created provider: {provider_name}')
                else:
                    print(f'[WARN] Provider {provider_name} returned None')
            except Exception as e:
                print(f'[FAIL] Failed to create provider {provider_name}: {e}')

    print(f'\n[INFO] Total created providers: {len(llm_providers)}')
    print(f'[INFO] Provider keys: {list(llm_providers.keys())}')

    if llm_providers:
        print('\n[SUCCESS] Providers are working correctly!')
    else:
        print('\n[FAILURE] No providers were created successfully')

except Exception as e:
    print(f'[ERROR] Error: {e}')
    import traceback
    traceback.print_exc()
