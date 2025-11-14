"""
Test OpenRouter Smart Fallback System

Demonstrates automatic fallback when models fail:
1. Try with a model that's likely down
2. System auto-discovers available FREE models
3. Automatically retries with best available
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.providers.openrouter_provider import OpenRouterProvider
from src.models.provider import ProviderConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_smart_fallback():
    """Test smart fallback system"""

    # Load environment
    load_dotenv()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("❌ OPENROUTER_API_KEY not found in .env")
        return

    print("\n" + "="*80)
    print("🧪 TESTING OPENROUTER SMART FALLBACK")
    print("="*80 + "\n")

    # Test 1: Start with a model that might be down
    print("📝 Test 1: Trying with potentially unavailable model")
    print("-" * 80)

    config = ProviderConfig(
        name="openrouter",
        type="openrouter",
        model="google/gemini-flash-1.5:free",  # Might be down
        temperature=0.7,
        max_tokens=100,
        timeout=30,
        rpm_limit=20,
        tpm_limit=100000
    )

    provider = OpenRouterProvider(config)

    try:
        print(f"\n🎯 Starting with model: {provider.model}")

        response = await provider.call(
            system_prompt="You are a helpful coding assistant.",
            user_prompt="Write a Python hello world in one line",
            task_type="code",  # Hint for smart model selection
            enable_fallback=True
        )

        print(f"\n✅ SUCCESS!")
        print(f"   Model used: {response.model}")
        print(f"   Response: {response.content[:200]}")
        print(f"   Tokens: {response.tokens_input}/{response.tokens_output}")
        print(f"   Latency: {response.latency_ms}ms")

    except Exception as e:
        print(f"\n❌ FAILED: {e}")

    # Test 2: Reasoning task
    print("\n" + "-" * 80)
    print("📝 Test 2: Testing reasoning task (will pick DeepSeek if available)")
    print("-" * 80)

    try:
        response = await provider.call(
            system_prompt="You are a math expert.",
            user_prompt="What is 15 * 23?",
            task_type="reasoning",  # Should pick DeepSeek if available
            enable_fallback=True
        )

        print(f"\n✅ SUCCESS!")
        print(f"   Model used: {response.model}")
        print(f"   Response: {response.content[:200]}")
        print(f"   Latency: {response.latency_ms}ms")

    except Exception as e:
        print(f"\n❌ FAILED: {e}")

    # Test 3: Force a model we know is down
    print("\n" + "-" * 80)
    print("📝 Test 3: Force using a definitely unavailable model")
    print("-" * 80)

    config_bad = ProviderConfig(
        name="openrouter",
        type="openrouter",
        model="fake/nonexistent-model:free",  # Definitely doesn't exist
        temperature=0.7,
        max_tokens=100,
        timeout=30,
        rpm_limit=20,
        tpm_limit=100000
    )

    provider_bad = OpenRouterProvider(config_bad)

    try:
        print(f"\n🎯 Starting with fake model: {provider_bad.model}")

        response = await provider_bad.call(
            system_prompt="You are helpful.",
            user_prompt="Say hi",
            enable_fallback=True
        )

        print(f"\n✅ SUCCESS after fallback!")
        print(f"   Model used: {response.model}")
        print(f"   Response: {response.content[:200]}")

    except Exception as e:
        print(f"\n⚠️ Expected failure (all models exhausted): {e}")

    # Show stats
    print("\n" + "="*80)
    print("📊 FALLBACK SYSTEM STATS")
    print("="*80)
    stats = provider.smart_fallback.get_stats()
    print(f"   Cached models: {stats['cached_models']}")
    print(f"   Failed models: {stats['failed_models']}")
    print(f"   Cache age: {stats['cache_age_minutes']:.1f} minutes")

    # Show available models
    print("\n" + "="*80)
    print("📋 AVAILABLE FREE MODELS (Top 10)")
    print("="*80)

    models = await provider.smart_fallback.discover_free_models()
    for i, model in enumerate(models[:10], 1):
        print(f"{i:2d}. {model['id']:50s} ({model['context']:>6,} tokens)")

    print(f"\nTotal FREE models available: {len(models)}")
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(test_smart_fallback())
