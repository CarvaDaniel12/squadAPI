#!/usr/bin/env python3
"""
Environment Variable Debugging Script
Helps diagnose why API keys aren't being loaded properly
"""

import os
import sys
from pathlib import Path

def print_separator(title=""):
    if title:
        print(f"\n{'='*60}")
        print(f" {title}")
        print(f"{'='*60}")
    else:
        print(f"{'='*60}")

def check_file_location():
    print_separator("FILE LOCATION CHECK")

    print(f"Current working directory: {os.getcwd()}")
    print(f"Script location: {Path(__file__).parent.absolute()}")

    # Check for .env file in different locations
    possible_locations = [
        Path.cwd() / ".env",                    # Current directory
        Path(__file__).parent / ".env",         # Script directory
        Path.cwd().parent / ".env",             # Parent of current directory
    ]

    print("\nChecking for .env file in these locations:")
    found_files = []
    for location in possible_locations:
        if location.exists():
            print(f"  ✓ FOUND: {location}")
            found_files.append(location)
        else:
            print(f"  ✗ Missing: {location}")

    return found_files

def check_env_file_content(env_path):
    print_separator("ENV FILE CONTENT")

    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        print(f"File: {env_path}")
        print(f"Total lines: {len(lines)}")
        print(f"File size: {env_path.stat().st_size} bytes")

        # Check for API key lines
        api_key_lines = []
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith('#') and '_API_KEY' in line:
                api_key_lines.append((i, line))

        print(f"\nAPI Key Lines Found: {len(api_key_lines)}")
        for line_num, line in api_key_lines:
            # Hide actual API key for security
            if '=' in line:
                key, value = line.split('=', 1)
                hidden_value = value[:4] + '*' * (len(value) - 4) if len(value) > 4 else '*' * len(value)
                print(f"  Line {line_num}: {key}={hidden_value}")
            else:
                print(f"  Line {line_num}: {line} (INVALID FORMAT)")

        return api_key_lines

    except Exception as e:
        print(f"Error reading file: {e}")
        return []

def check_python_env_loading():
    print_separator("PYTHON ENVIRONMENT LOADING")

    # Check if python-dotenv is available
    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv is available")

        # Try loading .env file
        env_path = Path.cwd() / ".env"
        if env_path.exists():
            print(f"✓ Loading from: {env_path}")
            load_dotenv(env_path)
        else:
            print("✗ No .env file found in current directory")
            print("Trying default load_dotenv()...")
            load_dotenv()

    except ImportError:
        print("✗ python-dotenv is NOT installed")
        print("Installing it now...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
            print("✓ python-dotenv installed successfully")
            from dotenv import load_dotenv
            load_dotenv()
        except Exception as e:
            print(f"✗ Failed to install python-dotenv: {e}")
            return False

    return True

def check_environment_variables():
    print_separator("ENVIRONMENT VARIABLES CHECK")

    # Expected API key variables
    expected_keys = [
        'GROQ_API_KEY',
        'CEREBRAS_API_KEY',
        'GEMINI_API_KEY',
        'OPENROUTER_API_KEY',
        'ANTHROPIC_API_KEY'
    ]

    print("Checking for expected API key environment variables:")
    found_keys = []

    for key in expected_keys:
        value = os.getenv(key)
        if value:
            # Show first 4 and last 4 characters for security
            if len(value) > 8:
                display_value = f"{value[:4]}...{value[-4:]}"
            else:
                display_value = "*" * len(value)
            print(f"  ✓ {key}: {display_value}")
            found_keys.append(key)
        else:
            print(f"  ✗ {key}: NOT SET")

    print(f"\nSummary: {len(found_keys)}/{len(expected_keys)} API keys found in environment")
    return found_keys

def check_provider_factory():
    print_separator("PROVIDER FACTORY CHECK")

    try:
        # Add project root to path
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))

        from src.providers.factory import ProviderFactory

        print("✓ ProviderFactory import successful")

        factory = ProviderFactory()
        print("✓ ProviderFactory instantiated")

        # Try to create providers
        providers_path = project_root / "config" / "providers.yaml"
        if providers_path.exists():
            print(f"✓ Providers config found: {providers_path}")
            try:
                providers = factory.create_all(str(providers_path))
                print(f"✓ Successfully loaded {len(providers)} providers:")
                for name, provider in providers.items():
                    print(f"    - {name}: {provider.config.type} ({provider.config.model})")
                return True
            except Exception as e:
                print(f"✗ Failed to create providers: {e}")
                return False
        else:
            print(f"✗ Providers config not found: {providers_path}")
            return False

    except Exception as e:
        print(f"✗ ProviderFactory error: {e}")
        return False

def provide_recommendations(found_keys, env_found, factory_working):
    print_separator("RECOMMENDATIONS")

    if not env_found:
        print("❌ ISSUE: No .env file found")
        print("SOLUTION:")
        print("1. Create a .env file in the project root directory")
        print("2. Copy from .env.example and add your API keys")

    if len(found_keys) == 0:
        print("\n❌ ISSUE: No API keys found in environment")
        print("SOLUTION:")
        print("1. Make sure your .env file has the correct format:")
        print("   GROQ_API_KEY=your_actual_key_here")
        print("2. Make sure there are no spaces around the = sign")
        print("3. Make sure you're not adding quotes around the values")
        print("4. Restart your terminal/IDE after changing .env file")

    if not factory_working:
        print("\n❌ ISSUE: Provider factory not working")
        print("SOLUTION:")
        print("1. Check that config/providers.yaml exists and is valid")
        print("2. Make sure you have at least one provider enabled")

    if factory_working and len(found_keys) > 0:
        print("\n✅ Environment setup looks correct!")
        print("Try running the provider test:")
        print("python scripts/test_providers.py --all")

def main():
    print("ENVIRONMENT VARIABLE TROUBLESHOOTING")
    print("This script will help diagnose why your API keys aren't working\n")

    # Step 1: Check file locations
    env_files = check_file_location()

    # Step 2: Check .env file content (if found)
    if env_files:
        for env_file in env_files:
            check_env_file_content(env_file)
            break  # Only check the first found file

    # Step 3: Check Python environment loading
    dotenv_working = check_python_env_loading()

    # Step 4: Check environment variables
    found_keys = check_environment_variables()

    # Step 5: Check provider factory
    factory_working = check_provider_factory()

    # Step 6: Provide recommendations
    provide_recommendations(found_keys, len(env_files) > 0, factory_working)

    print_separator("QUICK FIXES")
    print("If you're still having issues, try these steps:")
    print("1. Delete any existing .env file")
    print("2. Copy .env.example to .env")
    print("3. Edit .env and add your API keys (no quotes, no spaces)")
    print("4. Close and reopen your terminal/IDE")
    print("5. Run this script again to verify")

if __name__ == "__main__":
    main()
