#!/usr/bin/env python
"""
Test LLM Providers

Script to validate real LLM provider connections and API keys.
Tests each configured provider and reports health status.
"""

import asyncio
import os
import sys
import argparse
import time
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.providers.factory import ProviderFactory
from src.models.provider import ProviderConfig


# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text:^60}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}[OK] {text}{Colors.RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}[ERROR] {text}{Colors.RESET}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}[WARN] {text}{Colors.RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}[INFO] {text}{Colors.RESET}")


async def test_provider(provider_name: str, factory: ProviderFactory) -> dict:
    """
    Test a single provider
    
    Returns:
        Dict with test results
    """
    print(f"\n{Colors.BOLD}Testing: {provider_name}{Colors.RESET}")
    print("-" * 40)
    
    provider = factory.get_provider(provider_name)
    
    if not provider:
        print_error(f"Provider '{provider_name}' not found or disabled")
        return {
            'provider': provider_name,
            'configured': False,
            'healthy': False,
            'test_passed': False,
            'error': 'Provider not configured'
        }
    
    # Check API key
    api_key_env = f"{provider_name.upper()}_API_KEY"
    has_api_key = bool(os.getenv(api_key_env))
    
    if not has_api_key:
        print_warning(f"API key not found: {api_key_env}")
        return {
            'provider': provider_name,
            'configured': False,
            'healthy': False,
            'test_passed': False,
            'error': f'{api_key_env} not set'
        }
    
    print_info(f"API key found: {api_key_env}")
    print_info(f"Model: {provider.model}")
    print_info(f"RPM Limit: {provider.rpm_limit}")
    
    # Test 1: Health Check
    print(f"\n{Colors.YELLOW}Test 1: Health Check...{Colors.RESET}")
    try:
        start = time.time()
        is_healthy = await provider.health_check()
        elapsed_ms = int((time.time() - start) * 1000)
        
        if is_healthy:
            print_success(f"Health check passed ({elapsed_ms}ms)")
        else:
            print_error("Health check failed")
            return {
                'provider': provider_name,
                'configured': True,
                'healthy': False,
                'test_passed': False,
                'error': 'Health check returned False'
            }
    except Exception as e:
        print_error(f"Health check error: {e}")
        return {
            'provider': provider_name,
            'configured': True,
            'healthy': False,
            'test_passed': False,
            'error': str(e)
        }
    
    # Test 2: Simple Call
    print(f"\n{Colors.YELLOW}Test 2: Simple LLM Call...{Colors.RESET}")
    try:
        start = time.time()
        response = await provider.call(
            system_prompt="You are a helpful assistant that responds concisely.",
            user_prompt="Say 'Hello from Squad API!' and nothing else.",
            max_tokens=50,
            temperature=0.7
        )
        elapsed_ms = int((time.time() - start) * 1000)
        
        print_success(f"Call successful ({elapsed_ms}ms)")
        print_info(f"Response: {response.content[:100]}...")
        print_info(f"Tokens: {response.tokens_input} in, {response.tokens_output} out")
        print_info(f"Finish Reason: {response.finish_reason}")
        
        return {
            'provider': provider_name,
            'configured': True,
            'healthy': True,
            'test_passed': True,
            'latency_ms': elapsed_ms,
            'tokens_input': response.tokens_input,
            'tokens_output': response.tokens_output,
            'response_preview': response.content[:100]
        }
        
    except Exception as e:
        print_error(f"LLM call error: {e}")
        return {
            'provider': provider_name,
            'configured': True,
            'healthy': True,
            'test_passed': False,
            'error': str(e)
        }


async def test_all_providers(config_path: str = "config/providers.yaml"):
    """Test all configured providers"""
    print_header("SQUAD API - PROVIDER TEST SUITE")
    
    # Load environment variables
    load_dotenv()
    
    # Create factory
    factory = ProviderFactory()
    
    try:
        providers = factory.create_all(config_path)
        print_success(f"Loaded {len(providers)} providers from config")
    except Exception as e:
        print_error(f"Failed to load providers: {e}")
        return
    
    if not providers:
        print_warning("No providers configured!")
        print_info("Configure API keys in .env file")
        print_info("See: docs/API-KEYS-SETUP.md")
        return
    
    # Test each provider
    results = []
    for provider_name in providers.keys():
        result = await test_provider(provider_name, factory)
        results.append(result)
        await asyncio.sleep(1)  # Rate limit courtesy delay
    
    # Summary
    print_header("TEST SUMMARY")
    
    configured = [r for r in results if r['configured']]
    healthy = [r for r in results if r['healthy']]
    passed = [r for r in results if r['test_passed']]
    
    print(f"Providers tested: {len(results)}")
    print(f"  {Colors.GREEN}Configured: {len(configured)}{Colors.RESET}")
    print(f"  {Colors.GREEN}Healthy: {len(healthy)}{Colors.RESET}")
    print(f"  {Colors.GREEN}Tests passed: {len(passed)}{Colors.RESET}")
    
    if len(passed) == 0:
        print_error("\nNo providers working! Check API keys.")
        print_info("See: docs/API-KEYS-SETUP.md")
        sys.exit(1)
    
    elif len(passed) == len(results):
        print_success("\nALL PROVIDERS WORKING!")
        print_info("You're ready to use Squad API!")
    
    else:
        print_warning(f"\n{len(passed)}/{len(results)} providers working")
        print_info("Consider configuring more providers for higher throughput")
    
    # Details
    print(f"\n{Colors.BOLD}Provider Details:{Colors.RESET}")
    for result in results:
        status = "[OK]" if result['test_passed'] else "[FAIL]"
        latency = result.get('latency_ms', 'N/A')
        print(f"  {status} {result['provider']:12} - Latency: {latency}ms")
    
    print()


async def test_single_provider(provider_name: str, config_path: str = "config/providers.yaml"):
    """Test a single provider"""
    print_header(f"TESTING PROVIDER: {provider_name.upper()}")
    
    # Load environment
    load_dotenv()
    
    # Create factory
    factory = ProviderFactory()
    factory.create_all(config_path)
    
    # Test provider
    result = await test_provider(provider_name, factory)
    
    # Summary
    if result['test_passed']:
        print_success(f"\n{provider_name} is working!")
        print_info(f"Latency: {result.get('latency_ms', 'N/A')}ms")
        print_info(f"Model: {factory.get_provider(provider_name).model}")
    else:
        print_error(f"\n{provider_name} test failed")
        print_info(f"Error: {result.get('error', 'Unknown')}")
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Test Squad API LLM providers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test all providers
  python scripts/test_providers.py --all
  
  # Test specific provider
  python scripts/test_providers.py --provider groq
  
  # Test with custom config
  python scripts/test_providers.py --all --config my-config.yaml
        """
    )
    
    parser.add_argument(
        '--provider',
        type=str,
        help='Test specific provider (groq, cerebras, gemini, openrouter)'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Test all configured providers'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/providers.yaml',
        help='Path to providers.yaml (default: config/providers.yaml)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.all and not args.provider:
        parser.print_help()
        print_error("\nError: Specify --all or --provider <name>")
        sys.exit(1)
    
    # Run tests
    try:
        if args.all:
            asyncio.run(test_all_providers(args.config))
        else:
            asyncio.run(test_single_provider(args.provider, args.config))
    except KeyboardInterrupt:
        print_warning("\n\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

