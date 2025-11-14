#!/usr/bin/env python3
"""
Simple provider debug - no emojis
"""
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set PYTHONPATH
sys.path.insert(0, '.')

def test_provider_loading():
    """Test provider loading directly"""
    try:
        print("Testing provider imports...")

        # Test imports one by one
        try:
            from src.providers.groq_provider import GroqProvider
            print("GROQ: OK")
        except Exception as e:
            print(f"GROQ FAILED: {e}")

        try:
            from src.providers.cerebras_provider import CerebrasProvider
            print("CEREBRAS: OK")
        except Exception as e:
            print(f"CEREBRAS FAILED: {e}")

        try:
            from src.providers.gemini_provider import GeminiProvider
            print("GEMINI: OK")
        except Exception as e:
            print(f"GEMINI FAILED: {e}")

        try:
            from src.providers.openrouter_provider import OpenRouterProvider
            print("OPENROUTER: OK")
        except Exception as e:
            print(f"OPENROUTER FAILED: {e}")

        print("\nTesting ProviderFactory...")
        try:
            from src.providers.factory import ProviderFactory
            factory = ProviderFactory()
            print(f"Factory created with {len(factory.PROVIDER_CLASSES)} types: {list(factory.PROVIDER_CLASSES.keys())}")
        except Exception as e:
            print(f"ProviderFactory failed: {e}")
            return False

        print("\nTesting provider creation...")
        try:
            # Test creating providers
            config_path = "config/providers.yaml"
            providers = factory.create_all(config_path)
            print(f"Created {len(providers)} providers: {list(providers.keys())}")

            # Check if 'openrouter' is in the list
            if 'openrouter' in providers:
                print("OpenRouter provider: CREATED")
            else:
                print("OpenRouter provider: NOT FOUND")
                print("Available providers:", list(providers.keys()))

        except Exception as e:
            print(f"Provider creation failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        print("\nTesting environment variables...")
        api_keys = ['GROQ_API_KEY', 'CEREBRAS_API_KEY', 'GEMINI_API_KEY', 'OPENROUTER_API_KEY']
        for key in api_keys:
            value = os.getenv(key)
            if value:
                print(f"{key}: FOUND")
            else:
                print(f"{key}: NOT FOUND")

        return True

    except Exception as e:
        print(f"Overall test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== DEBUGGING SQUAD API PROVIDER LOADING ===")

    success = test_provider_loading()

    if success:
        print("\nProvider debugging completed")
    else:
        print("\nProvider debugging found issues")
