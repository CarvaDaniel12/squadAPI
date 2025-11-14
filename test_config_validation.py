#!/usr/bin/env python3
"""
Test configuration validation to see the exact error
"""

import sys
import os
import traceback

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_config_validation():
    """Test configuration validation and show the specific error"""
    print("=== CONFIGURATION VALIDATION TEST ===")

    try:
        from src.config.validation import validate_config, ConfigurationError

        try:
            config = validate_config(config_dir="config")
            print("SUCCESS: Configuration validation passed")
            print(f"Providers found: {list(config.providers.__dict__.keys()) if config.providers else 'None'}")
            return True

        except ConfigurationError as e:
            print("FAIL: Configuration validation failed")
            print(f"Error: {e}")
            print("\nFull traceback:")
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_config_validation()
    sys.exit(0 if success else 1)
