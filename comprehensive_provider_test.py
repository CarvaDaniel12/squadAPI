#!/usr/bin/env python3
"""
Comprehensive Provider Test Suite for Squad API

This script performs comprehensive testing of all LLM providers including:
- Real API connectivity tests
- Health checks for all providers
- Performance benchmarking
- API key validation and documentation
- Complete system validation without stubs
- Detailed test reporting

Usage:
    python comprehensive_provider_test.py --all
    python comprehensive_provider_test.py --provider groq
    python comprehensive_provider_test.py --health-check
    python comprehensive_provider_test.py --documentation
"""

import asyncio
import os
import sys
import json
import time
import argparse
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import Squad API components
try:
    from src.providers.factory import ProviderFactory
    from src.models.provider import ProviderConfig
    from src.health.checker import HealthChecker
    from src.health.probes import ProviderProbe
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


@dataclass
class ProviderTestResult:
    """Test result for a single provider"""
    provider_name: str
    provider_type: str
    configured: bool
    api_key_available: bool
    health_check_passed: bool
    api_call_successful: bool
    latency_ms: Optional[int] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    error_message: Optional[str] = None
    response_preview: Optional[str] = None
    model: Optional[str] = None
    rpm_limit: Optional[int] = None


@dataclass
class TestReport:
    """Complete test report"""
    timestamp: str
    total_providers: int
    configured_providers: int
    api_keys_available: int
    health_checks_passed: int
    api_calls_successful: int
    provider_results: List[ProviderTestResult]
    system_status: str
    recommendations: List[str]


class Colors:
    """Terminal colors for output formatting"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    PURPLE = '\033[95m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str, char: str = '=', width: int = 80):
    """Print formatted header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{char * width}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text:^{width}}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{char * width}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}[✓] {text}{Colors.RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}[✗] {text}{Colors.RESET}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}[⚠] {text}{Colors.RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}[ℹ] {text}{Colors.RESET}")


def print_detail(text: str, indent: int = 0):
    """Print detailed message"""
    prefix = "  " * indent
    print(f"{Colors.WHITE}{prefix}{text}{Colors.RESET}")


class ComprehensiveProviderTester:
    """Comprehensive provider testing suite"""

    def __init__(self):
        self.factory = ProviderFactory()
        self.test_results: List[ProviderTestResult] = []
        self.start_time = datetime.now()

        # Load environment variables
        load_dotenv()

        # API key requirements documentation
        self.api_key_requirements = {
            "groq": {
                "env_var": "GROQ_API_KEY",
                "description": "Groq API Key for Llama 3.3 70B and other models",
                "url": "https://console.groq.com/keys",
                "free_tier": True,
                "models": ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"]
            },
            "cerebras": {
                "env_var": "CEREBRAS_API_KEY",
                "description": "Cerebras API Key for Llama 3.1 models",
                "url": "https://cloud.cerebras.ai/",
                "free_tier": True,
                "models": ["llama3.1-8b", "llama3.1-70b"]
            },
            "gemini": {
                "env_var": "GEMINI_API_KEY",
                "description": "Google Gemini API Key for Gemini 2.0 Flash and other models",
                "url": "https://aistudio.google.com/app/apikey",
                "free_tier": True,
                "models": ["gemini-2.0-flash-exp", "gemini-1.5-pro"]
            },
            "openrouter": {
                "env_var": "OPENROUTER_API_KEY",
                "description": "OpenRouter API Key for accessing multiple models",
                "url": "https://openrouter.ai/keys",
                "free_tier": True,
                "models": ["openrouter/auto", "openrouter/gemini-2.0-flash", "openrouter/qwen3"]
            },
            "anthropic": {
                "env_var": "ANTHROPIC_API_KEY",
                "description": "Anthropic API Key for Claude models",
                "url": "https://console.anthropic.com/",
                "free_tier": False,
                "models": ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
            }
        }

    async def test_provider_configuration(self, provider_name: str) -> Dict[str, Any]:
        """Test provider configuration and API key availability"""
        print_detail(f"Testing configuration for {provider_name}...")

        result = ProviderTestResult(
            provider_name=provider_name,
            provider_type="unknown",
            configured=False,
            api_key_available=False,
            health_check_passed=False,
            api_call_successful=False
        )

        try:
            # Load all providers to check configuration
            providers = self.factory.create_all("config/providers.yaml")

            if provider_name not in providers:
                result.error_message = f"Provider '{provider_name}' not configured in config/providers.yaml"
                return result

            provider = providers[provider_name]
            result.configured = True
            result.provider_type = provider.config.type
            result.model = provider.config.model
            result.rpm_limit = provider.config.rpm_limit

            # Check API key availability
            api_key_env = f"{provider_name.upper()}_API_KEY"
            api_key = os.getenv(api_key_env)
            result.api_key_available = bool(api_key)

            if not api_key:
                result.error_message = f"API key not found: {api_key_env}"
                return result

            print_success(f"Provider configured: {provider_name} ({provider.config.type})")
            print_info(f"Model: {provider.config.model}")
            print_info(f"API Key: {api_key_env} ✓")

            return result

        except Exception as e:
            result.error_message = f"Configuration error: {str(e)}"
            return result

    async def test_provider_health(self, provider_name: str, provider) -> bool:
        """Test provider health check"""
        try:
            print_detail(f"Running health check for {provider_name}...")
            start_time = time.time()

            is_healthy = await provider.health_check()
            elapsed_ms = int((time.time() - start_time) * 1000)

            if is_healthy:
                print_success(f"Health check passed ({elapsed_ms}ms)")
                return True
            else:
                print_warning(f"Health check failed (returned False)")
                return False

        except Exception as e:
            print_error(f"Health check error: {str(e)}")
            return False

    async def test_provider_api_call(self, provider_name: str, provider) -> Dict[str, Any]:
        """Test provider with actual API call"""
        try:
            print_detail(f"Making API call to {provider_name}...")
            start_time = time.time()

            # Test prompt optimized for brevity and success
            response = await provider.call(
                system_prompt="You are a helpful assistant. Respond with a single sentence.",
                user_prompt="Say 'Hello from Squad API test!' and nothing else.",
                max_tokens=50,
                temperature=0.1
            )

            elapsed_ms = int((time.time() - start_time) * 1000)

            print_success(f"API call successful ({elapsed_ms}ms)")
            print_detail(f"Response: {response.content[:100]}...")
            print_detail(f"Tokens: {response.tokens_input} in, {response.tokens_output} out")

            return {
                "successful": True,
                "latency_ms": elapsed_ms,
                "tokens_input": response.tokens_input,
                "tokens_output": response.tokens_output,
                "response_preview": response.content[:100],
                "finish_reason": response.finish_reason
            }

        except Exception as e:
            print_error(f"API call error: {str(e)}")
            return {
                "successful": False,
                "error": str(e)
            }

    async def test_single_provider(self, provider_name: str) -> ProviderTestResult:
        """Test a single provider comprehensively"""
        print_header(f"Testing Provider: {provider_name.upper()}", "─", 60)

        # Test configuration first
        config_result = await self.test_provider_configuration(provider_name)

        if not config_result.configured:
            self.test_results.append(config_result)
            return config_result

        if not config_result.api_key_available:
            self.test_results.append(config_result)
            return config_result

        try:
            # Get provider instance
            providers = self.factory.create_all("config/providers.yaml")
            provider = providers[provider_name]

            # Test health check
            health_passed = await self.test_provider_health(provider_name, provider)
            config_result.health_check_passed = health_passed

            # Test API call if health check passed
            if health_passed:
                api_result = await self.test_provider_api_call(provider_name, provider)
                config_result.api_call_successful = api_result["successful"]
                config_result.latency_ms = api_result.get("latency_ms")
                config_result.tokens_input = api_result.get("tokens_input")
                config_result.tokens_output = api_result.get("tokens_output")
                config_result.response_preview = api_result.get("response_preview")

                if not api_result["successful"]:
                    config_result.error_message = api_result["error"]
            else:
                config_result.error_message = "Health check failed"

        except Exception as e:
            config_result.error_message = f"Test execution error: {str(e)}"
            traceback.print_exc()

        self.test_results.append(config_result)
        return config_result

    async def test_all_providers(self) -> List[ProviderTestResult]:
        """Test all configured providers"""
        print_header("COMPREHENSIVE PROVIDER TEST SUITE", "=")
        print_info(f"Starting test suite at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # Load providers to see what's configured
            providers = self.factory.create_all("config/providers.yaml")
            provider_names = list(providers.keys())

            print_info(f"Found {len(provider_names)} configured providers: {provider_names}")

            # Test each provider
            for provider_name in provider_names:
                await self.test_single_provider(provider_name)
                await asyncio.sleep(1)  # Rate limiting courtesy delay

        except Exception as e:
            print_error(f"Failed to load providers: {str(e)}")

        return self.test_results

    async def test_health_checks_only(self):
        """Test health checks for all providers without API calls"""
        print_header("PROVIDER HEALTH CHECKS ONLY", "=")

        try:
            providers = self.factory.create_all("config/providers.yaml")
            provider_names = list(providers.keys())

            for provider_name in provider_names:
                try:
                    result = await self.test_single_provider(provider_name)

                    status = "✓ HEALTHY" if result.health_check_passed else "✗ UNHEALTHY"
                    print(f"{provider_name:12} - {status}")

                except Exception as e:
                    print_error(f"Health check failed for {provider_name}: {str(e)}")

        except Exception as e:
            print_error(f"Failed to test health checks: {str(e)}")

    def generate_api_documentation(self):
        """Generate API key requirements documentation"""
        print_header("API KEY REQUIREMENTS DOCUMENTATION", "=")

        for provider_name, requirements in self.api_key_requirements.items():
            print(f"\n{Colors.BOLD}{provider_name.upper()}{Colors.RESET}")
            print(f"Environment Variable: {Colors.CYAN}{requirements['env_var']}{Colors.RESET}")
            print(f"Description: {requirements['description']}")
            print(f"Setup URL: {requirements['url']}")
            print(f"Free Tier: {'✓' if requirements['free_tier'] else '✗'}")
            print(f"Available Models:")

            for model in requirements['models']:
                print(f"  • {model}")

            # Check current status
            env_var = requirements['env_var']
            status = "✓ CONFIGURED" if os.getenv(env_var) else "✗ MISSING"
            print(f"Current Status: {status}")
            print("-" * 50)

    def generate_test_report(self) -> TestReport:
        """Generate comprehensive test report"""
        # Calculate statistics
        total_providers = len(self.test_results)
        configured_providers = sum(1 for r in self.test_results if r.configured)
        api_keys_available = sum(1 for r in self.test_results if r.api_key_available)
        health_checks_passed = sum(1 for r in self.test_results if r.health_check_passed)
        api_calls_successful = sum(1 for r in self.test_results if r.api_call_successful)

        # Determine system status
        if api_calls_successful == total_providers and total_providers > 0:
            system_status = "EXCELLENT"
        elif api_calls_successful > 0:
            system_status = "GOOD"
        elif health_checks_passed > 0:
            system_status = "PARTIAL"
        else:
            system_status = "CRITICAL"

        # Generate recommendations
        recommendations = []

        if api_keys_available == 0:
            recommendations.append("Set up at least one API key to use Squad API")

        if health_checks_passed == 0:
            recommendations.append("Check network connectivity and API key validity")

        if api_calls_successful < configured_providers:
            recommendations.append("Review failed providers for configuration issues")

        if total_providers < 3:
            recommendations.append("Consider configuring additional providers for redundancy")

        if not recommendations:
            recommendations.append("All systems operational - maintain current configuration")

        return TestReport(
            timestamp=self.start_time.isoformat(),
            total_providers=total_providers,
            configured_providers=configured_providers,
            api_keys_available=api_keys_available,
            health_checks_passed=health_checks_passed,
            api_calls_successful=api_calls_successful,
            provider_results=self.test_results,
            system_status=system_status,
            recommendations=recommendations
        )

    def print_test_summary(self, report: TestReport):
        """Print test summary"""
        print_header("TEST SUMMARY", "=")

        # Overall status
        status_colors = {
            "EXCELLENT": Colors.GREEN,
            "GOOD": Colors.BLUE,
            "PARTIAL": Colors.YELLOW,
            "CRITICAL": Colors.RED
        }

        status_color = status_colors.get(report.system_status, Colors.WHITE)
        print(f"System Status: {status_color}{Colors.BOLD}{report.system_status}{Colors.RESET}")

        # Statistics
        print(f"\nStatistics:")
        print(f"  Total Providers:     {report.total_providers}")
        print(f"  Configured:          {report.configured_providers}")
        print(f"  API Keys Available:  {report.api_keys_available}")
        print(f"  Health Checks:       {report.health_checks_passed}")
        print(f"  API Calls Success:   {report.api_calls_successful}")

        # Success rate
        if report.configured_providers > 0:
            success_rate = (report.api_calls_successful / report.configured_providers) * 100
            print(f"  Success Rate:        {success_rate:.1f}%")

        # Provider details
        print(f"\nProvider Details:")
        for result in report.provider_results:
            status_icon = "✓" if result.api_call_successful else "✗"
            latency = f"{result.latency_ms}ms" if result.latency_ms else "N/A"
            print(f"  {status_icon} {result.provider_name:12} - Latency: {latency:8} - Model: {result.model or 'N/A'}")

        # Recommendations
        print(f"\nRecommendations:")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"  {i}. {rec}")

    def save_test_report(self, report: TestReport, filename: str = "provider_test_report.json"):
        """Save test report to JSON file"""
        # Convert dataclasses to dictionaries for JSON serialization
        report_dict = asdict(report)

        with open(filename, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)

        print_info(f"Test report saved to: {filename}")

    def save_api_documentation(self, filename: str = "api_key_requirements.md"):
        """Save API documentation to Markdown file"""
        content = f"""# Squad API - Provider Configuration Guide

Generated on: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}

## API Key Requirements

This document lists all LLM providers supported by Squad API and their setup requirements.

"""

        for provider_name, requirements in self.api_key_requirements.items():
            env_var = requirements['env_var']
            status = "✅ CONFIGURED" if os.getenv(env_var) else "❌ MISSING"

            content += f"""### {provider_name.upper()}

- **Environment Variable**: `{env_var}`
- **Description**: {requirements['description']}
- **Setup URL**: [{requirements['url']}]({requirements['url']})
- **Free Tier**: {'✅ Yes' if requirements['free_tier'] else '❌ No (Paid)'}
- **Current Status**: {status}

**Available Models**:
"""
            for model in requirements['models']:
                content += f"- `{model}`\n"

            content += "\n"

        content += """## Setup Instructions

1. Get your API keys from the respective providers
2. Add them to your `.env` file in the project root
3. Restart the Squad API server
4. Run `python comprehensive_provider_test.py --all` to verify configuration

## Troubleshooting

- Ensure all API keys are valid and have sufficient quota
- Check network connectivity to provider endpoints
- Review provider-specific rate limits
- See logs for detailed error messages

"""

        with open(filename, 'w') as f:
            f.write(content)

        print_info(f"API documentation saved to: {filename}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Comprehensive Squad API Provider Testing Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Test all configured providers'
    )

    parser.add_argument(
        '--provider',
        type=str,
        help='Test specific provider (groq, cerebras, gemini, openrouter, anthropic)'
    )

    parser.add_argument(
        '--health-check',
        action='store_true',
        help='Test health checks for all providers only'
    )

    parser.add_argument(
        '--documentation',
        action='store_true',
        help='Generate API key requirements documentation'
    )

    parser.add_argument(
        '--save-report',
        type=str,
        help='Save test report to specified filename'
    )

    args = parser.parse_args()

    # Validate arguments
    if not any([args.all, args.provider, args.health_check, args.documentation]):
        parser.print_help()
        print_error("\nPlease specify an action: --all, --provider, --health-check, or --documentation")
        sys.exit(1)

    tester = ComprehensiveProviderTester()

    try:
        if args.documentation:
            tester.generate_api_documentation()

        if args.health_check:
            await tester.test_health_checks_only()

        if args.all:
            await tester.test_all_providers()
            report = tester.generate_test_report()
            tester.print_test_summary(report)

            if args.save_report:
                tester.save_test_report(report, args.save_report)
            else:
                tester.save_test_report(report)

            tester.save_api_documentation()

        if args.provider:
            await tester.test_single_provider(args.provider)
            report = tester.generate_test_report()
            tester.print_test_summary(report)

            if args.save_report:
                tester.save_test_report(report, args.save_report)

    except KeyboardInterrupt:
        print_warning("\n\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
