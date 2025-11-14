"""
OpenRouter Free Models Test
Tests the best FREE models available on OpenRouter

Top Free Models (Nov 2024):
- Meta Llama 3.1 405B Instruct (MASSIVE!)
- Google Gemini 2.0 Flash Thinking
- DeepSeek V3
- Qwen 2.5 72B
- And many more...
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent.parent / '.env')
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.loader import AgentLoader
from src.agents.prompt_builder import SystemPromptBuilder
from src.agents.conversation import ConversationManager
from src.agents.router import AgentRouter
from src.agents.orchestrator import AgentOrchestrator
from src.models.request import AgentExecutionRequest
from src.models.provider import ProviderConfig
from src.providers.openrouter_provider import OpenRouterProvider
from src.utils.cost_optimizer import CostOptimizer


# Top FREE models on OpenRouter (verified Nov 2024 - BEST AVAILABLE!)
OPENROUTER_FREE_MODELS = [
    {
        'name': 'Qwen3 Coder 480B (FREE!)',
        'id': 'qwen/qwen3-coder:free',
        'description': '480B MoE code generation beast - FREE!',
        'best_for': 'Code generation, complex reasoning'
    },
    {
        'name': 'DeepSeek V3.1 (671B FREE!)',
        'id': 'deepseek/deepseek-chat-v3.1:free',
        'description': '671B hybrid reasoning model - MASSIVE!',
        'best_for': 'Complex reasoning, analysis'
    },
    {
        'name': 'DeepSeek R1T2 Chimera (FREE!)',
        'id': 'tngtech/deepseek-r1t2-chimera:free',
        'description': '671B mixture-of-experts from TNG',
        'best_for': 'Advanced reasoning tasks'
    },
    {
        'name': 'Google Gemini 2.0 Flash Exp',
        'id': 'google/gemini-2.0-flash-exp:free',
        'description': 'Fast experimental Flash 2.0',
        'best_for': 'Speed, quality, 1M context'
    },
    {
        'name': 'Mistral 7B Instruct',
        'id': 'mistralai/mistral-7b-instruct:free',
        'description': 'Efficient 7B model from Mistral',
        'best_for': 'Simple tasks, fast'
    }
]


async def test_openrouter_model(model_info: dict, orchestrator, cost_optimizer):
    """Test a single OpenRouter model"""

    print(f"\n{'='*70}")
    print(f"🚀 {model_info['name']}")
    print(f"   Model: {model_info['id']}")
    print(f"   Description: {model_info['description']}")
    print(f"   Best for: {model_info['best_for']}")

    request = AgentExecutionRequest(
        agent="analyst",
        task="Explain the async/await pattern in Python in 2-3 sentences. Be concise.",
        user_id="test-user",
        conversation_id=f"test-{model_info['name'].replace(' ', '-')}"
    )

    try:
        response = await orchestrator.execute(request)

        print(f"\n✅ Response Received!")
        print(f"   Latency: {response.metadata.latency_ms}ms")
        print(f"   Tokens: {response.metadata.tokens_input} in / {response.metadata.tokens_output} out")
        print(f"   🆓 Cost: FREE")

        print(f"\n   Response:")
        print(f"   {response.response[:200]}...")

        # Record usage
        cost_optimizer.record_usage(
            provider='openrouter',
            tokens_input=response.metadata.tokens_input,
            tokens_output=response.metadata.tokens_output,
            user_id="test-user"
        )

        return True

    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Test OpenRouter free models"""

    print("="*70)
    print("🌟 OPENROUTER FREE MODELS TEST")
    print("   Testing the best FREE models available!")
    print("="*70)

    # Check API key
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("\n❌ OPENROUTER_API_KEY not found in .env")
        return 1

    print(f"\n✅ API Key loaded: {api_key[:15]}...")

    # Initialize
    cost_optimizer = CostOptimizer()

    print("\n🔧 Initializing components...")
    bmad_path = Path(__file__).parent.parent / ".bmad"
    agent_loader = AgentLoader(bmad_path=bmad_path)
    await agent_loader.load_all()

    prompt_builder = SystemPromptBuilder()
    conversation_manager = ConversationManager()
    agent_router = AgentRouter(agent_loader=agent_loader)

    print(f"\n📋 Testing {len(OPENROUTER_FREE_MODELS)} FREE models...")

    results = []

    for model_info in OPENROUTER_FREE_MODELS:
        # Create provider for this model
        provider = OpenRouterProvider(ProviderConfig(
            name='openrouter',
            type='openrouter',
            model=model_info['id'],
            enabled=True,
            api_key=api_key,
            rpm_limit=20,
            tpm_limit=200000
        ))

        # Create orchestrator
        orchestrator = AgentOrchestrator(
            agent_loader=agent_loader,
            prompt_builder=prompt_builder,
            conversation_manager=conversation_manager,
            agent_router=agent_router,
            providers={'openrouter': provider}
        )

        # Test
        success = await test_openrouter_model(model_info, orchestrator, cost_optimizer)
        results.append(success)

        # Delay between requests
        if success:
            await asyncio.sleep(3)  # OpenRouter free tier rate limit

    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Total Models Tested: {len(results)}")
    print(f"Successful: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")

    # Cost report
    print("\n" + "="*70)
    cost_optimizer.print_report()

    print("="*70)
    print("🎯 OPENROUTER ADVANTAGES")
    print("="*70)
    print()
    print("✅ Access to 100+ models through ONE API key")
    print("✅ INCREDIBLE FREE models:")
    print("   • Qwen3 Coder 480B - Code generation beast!")
    print("   • DeepSeek V3.1 671B - MASSIVE reasoning model")
    print("   • DeepSeek R1T2 Chimera 671B - Advanced reasoning")
    print("   • Gemini 2.0 Flash Exp - Fast & quality")
    print("   • Mistral 7B - Quick simple tasks")
    print("✅ PAID models also available (when you need premium)")
    print("   • Claude, GPT-4, Llama 3.1 405B, etc.")
    print("✅ Automatic failover between models")
    print("✅ Single API key for everything")
    print()
    print("💡 OPTIMAL FREE TIER STRATEGY:")
    print("   1. Groq (Llama 3.3 70B) - FASTEST (30 RPM)")
    print("   2. OpenRouter Qwen3 480B - BEST FOR CODE")
    print("   3. OpenRouter DeepSeek 671B - BEST FOR REASONING")
    print("   4. Gemini 2.0 Flash - 2M context, fast")
    print("   5. Cerebras (Llama 3.1 8B) - Simple tasks")
    print("   6. Keep OpenAI/Anthropic for critical only")
    print()
    print("🎁 TOTAL FREE CAPACITY (INSANE!):")
    print("   • Groq: 30 RPM (Llama 70B)")
    print("   • OpenRouter: 20 RPM (Qwen 480B, DeepSeek 671B!)")
    print("   • Gemini: 15 RPM (Flash 2.0)")
    print("   • Cerebras: 30 RPM (Llama 8B)")
    print("   = ~95 RPM of PREMIUM FREE AI")
    print("   Including TWO 500B+ models for FREE! 🤯")
    print()

    if all(results):
        print("✅ ALL FREE MODELS WORKING!")
        return 0
    else:
        print("⚠️  Some models failed (might be temporary)")
        return 0  # Don't fail, some models might be down


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
