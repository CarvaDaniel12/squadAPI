#!/usr/bin/env python3
"""
Debug the exact orchestration flow
"""

import os
import sys
sys.path.append('.')

from dotenv import load_dotenv
from pathlib import Path
from src.config.validation import validate_config
from src.providers.factory import ProviderFactory

# Load env
project_root = Path('.')
env_paths = [project_root / '.env', Path.cwd() / '.env', Path('.env')]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path, override=False)
        break

# Config
config = validate_config(config_dir='config')
providers = config.providers

# Create providers
provider_factory = ProviderFactory()
llm_providers = {}

for provider_name in ['groq', 'gemini', 'cerebras', 'openrouter', 'anthropic', 'openai']:
    provider_config = getattr(providers, provider_name, None)
    if provider_config and provider_config.enabled:
        provider_dict = {
            'name': provider_name, 'type': provider_name, 'enabled': provider_config.enabled,
            'model': provider_config.model, 'api_key_env': provider_config.api_key_env,
            'timeout': provider_config.timeout,
            'rpm_limit': getattr(provider_config, 'rpm_limit', 60),
            'tpm_limit': getattr(provider_config, 'tpm_limit', 100000),
        }
        if hasattr(provider_config, 'base_url') and provider_config.base_url:
            provider_dict['base_url'] = provider_config.base_url

        try:
            provider_instance = provider_factory.create_provider(provider_name, provider_dict)
            if provider_instance:
                llm_providers[provider_name] = provider_instance
        except Exception as e:
            print(f'[FAIL] {provider_name}: {e}')

print(f'\\n[DEBUG] llm_providers type: {type(llm_providers)}')
print(f'[DEBUG] llm_providers keys: {list(llm_providers.keys())}')
print(f'[DEBUG] llm_providers has groq: {"groq" in llm_providers}')

# Now test the orchestrator creation
try:
    from src.agents.loader import AgentLoader
    from src.agents.prompt_builder import SystemPromptBuilder
    from src.agents.conversation import ConversationManager
    from src.agents.router import AgentRouter
    from src.agents.orchestrator import AgentOrchestrator

    # Create components
    agent_loader = AgentLoader(bmad_path=".bmad")
    prompt_builder = SystemPromptBuilder()
    conversation_manager = ConversationManager(redis_client=None)
    agent_router = AgentRouter(agent_loader)

    print(f'\\n[DEBUG] Creating AgentOrchestrator with {len(llm_providers)} providers...')

    # Create orchestrator with providers
    orchestrator = AgentOrchestrator(
        agent_loader=agent_loader,
        prompt_builder=prompt_builder,
        conversation_manager=conversation_manager,
        agent_router=agent_router,
        providers=llm_providers
    )

    print(f'\\n[DEBUG] Orchestrator created successfully')
    print(f'[DEBUG] Orchestrator has providers: {len(orchestrator.providers)}')
    print(f'[DEBUG] Orchestrator providers keys: {list(orchestrator.providers.keys())}')

    # Test provider access
    if 'groq' in orchestrator.providers:
        print('[DEBUG] SUCCESS: Can access groq from orchestrator.providers')
    else:
        print('[DEBUG] FAILURE: Cannot access groq from orchestrator.providers')

except Exception as e:
    print(f'[ERROR] Orchestrator creation failed: {e}')
    import traceback
    traceback.print_exc()
