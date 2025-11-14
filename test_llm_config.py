#!/usr/bin/env python3
"""
Test script to verify LLM API configuration - Simplified for Windows Console
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_env_vars():
    """Test if environment variables are properly loaded"""
    print("=== Environment Variables Test ===")

    required_vars = [
        'GROQ_API_KEY',
        'CEREBRAS_API_KEY',
        'GEMINI_API_KEY',
        'OPENROUTER_API_KEY'
    ]

    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Show first 10 characters for security
            masked = value[:10] + '...' if len(value) > 10 else value
            print(f"[OK] {var}: {masked}")
        else:
            print(f"[FAIL] {var}: NOT SET")

    print()

def test_settings_loading():
    """Test Pydantic Settings loading"""
    print("=== Pydantic Settings Test ===")

    try:
        from src.config.settings import get_settings

        settings = get_settings()
        summary = settings.get_api_key_summary()

        print("Settings loaded successfully:")
        for provider, loaded in summary.items():
            status = "[OK]" if loaded else "[FAIL]"
            print(f"{status} {provider}: {loaded}")

        return True

    except Exception as e:
        print(f"[FAIL] Failed to load settings: {e}")
        return False

def test_provider_configs():
    """Test provider configuration loading"""
    print("=== Provider Config Test ===")

    try:
        import yaml
        with open('config/providers.yaml', 'r') as f:
            config = yaml.safe_load(f)

        providers = config.get('providers', {})
        for name, provider_config in providers.items():
            enabled = provider_config.get('enabled', False)
            api_key_env = provider_config.get('api_key_env', 'NOT_SET')
            status = "[OK]" if enabled else "[FAIL]"
            print(f"{status} {name}: enabled={enabled}, api_key_env={api_key_env}")

        return True

    except Exception as e:
        print(f"[FAIL] Failed to load provider config: {e}")
        return False

def test_provider_validation():
    """Test provider API key validation"""
    print("=== Provider Validation Test ===")

    try:
        from src.config.validation import validate_provider_api_keys
        from src.config.settings import get_settings
        import yaml

        # Load providers config
        with open('config/providers.yaml', 'r') as f:
            providers_config = yaml.safe_load(f)

        # Load settings
        settings = get_settings()

        # Validate
        errors = validate_provider_api_keys(providers_config, settings)

        if errors:
            print("Validation errors found:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("[OK] All provider API keys validated successfully")

        return len(errors) == 0

    except Exception as e:
        print(f"[FAIL] Provider validation failed: {e}")
        return False

def main():
    """Run all configuration tests"""
    print("LLM API Configuration Test\n")

    tests = [
        test_env_vars,
        test_settings_loading,
        test_provider_configs,
        test_provider_validation
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"[FAIL] Test {test.__name__} failed with exception: {e}")
            results.append(False)
        print()

    # Summary
    passed = sum(results)
    total = len(results)
    print(f"=== Test Summary ===")
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("[SUCCESS] All tests passed! LLM API configuration is working correctly.")
    else:
        print("[ERROR] Some tests failed. Please check the configuration.")

if __name__ == "__main__":
    main()
