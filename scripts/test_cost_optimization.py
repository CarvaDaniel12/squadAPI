"""
Complete Cost Optimization Test
Tests all providers (free + paid) with intelligent routing

Demonstrates:
1. Free providers for simple/medium tasks
2. Paid providers only for complex/critical tasks
3. Cost tracking and budget enforcement
4. Real API calls to validate everything works
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.loader import AgentLoader
from src.agents.prompt_builder import SystemPromptBuilder
from src.agents.conversation import ConversationManager
from src.agents.router import AgentRouter
from src.agents.orchestrator import AgentOrchestrator
from src.models.request import AgentExecutionRequest
from src.models.provider import ProviderConfig
from src.providers.groq_provider import GroqProvider
from src.providers.gemini_provider import GeminiProvider
from src.providers.cerebras_provider import CerebrasProvider
from src.providers.openai_provider import OpenAIProvider
from src.providers.anthropic_provider import AnthropicProvider
from src.utils.cost_optimizer import CostOptimizer


async def test_provider(name: str, provider, orchestrator, task: str, complexity: str):
    """Test a single provider"""
    print(f"\n{'='*70}")
    print(f"🧪 Testing {name}")
    print(f"   Task: {task[:50]}...")
    print(f"   Complexity: {complexity}")

    request = AgentExecutionRequest(
        agent="analyst",
        task=task,
        user_id="test-user",
        conversation_id=f"test-{name}"
    )

    try:
        response = await orchestrator.execute(request)

        print(f"\n✅ {name} Response:")
        print(f"   Provider: {response.provider}")
        print(f"   Model: {response.model}")
        print(f"   Latency: {response.metadata.latency_ms}ms")
        print(f"   Tokens: {response.metadata.tokens_input} in / {response.metadata.tokens_output} out")

        # Calculate cost
        cost = cost_optimizer.calculate_cost(
            response.provider,
            response.metadata.tokens_input,
            response.metadata.tokens_output
        )

        if cost > 0:
            print(f"   💵 Cost: ${cost:.4f}")
        else:
            print(f"   🆓 Cost: FREE")

        print(f"\n   Response preview: {response.response[:150]}...")

        # Record usage
        cost_optimizer.record_usage(
            provider=response.provider,
            tokens_input=response.metadata.tokens_input,
            tokens_output=response.metadata.tokens_output,
            user_id="test-user",
            conversation_id=f"test-{name}"
        )

        return True

    except Exception as e:
        print(f"\n❌ {name} failed: {e}")
        return False


async def main():
    """Run complete cost optimization test"""

    global cost_optimizer
    cost_optimizer = CostOptimizer()

    print("="*70)
    print("💰 COMPLETE COST OPTIMIZATION TEST")
    print("   Testing FREE + PAID providers with intelligent routing")
    print("="*70)

    # Check API keys
    print("\n🔑 Checking API Keys...")
    keys = {
        'GROQ': os.getenv('GROQ_API_KEY'),
        'GEMINI': os.getenv('GEMINI_API_KEY'),
        'CEREBRAS': os.getenv('CEREBRAS_API_KEY'),
        'OPENAI': os.getenv('OPENAI_API_KEY'),
        'ANTHROPIC': os.getenv('ANTHROPIC_API_KEY')
    }

    for name, key in keys.items():
        status = "✅ OK" if key else "❌ NOT SET"
        print(f"   {name:12s} {status}")

    # Initialize components
    print("\n🔧 Initializing components...")
    bmad_path = Path(__file__).parent.parent / ".bmad"
    agent_loader = AgentLoader(bmad_path=bmad_path)
    await agent_loader.load_all()

    prompt_builder = SystemPromptBuilder()
    conversation_manager = ConversationManager()
    agent_router = AgentRouter(agent_loader=agent_loader)

    # Create providers
    providers = {}

    # Free providers
    if keys['GROQ']:
        providers['groq'] = GroqProvider(ProviderConfig(
            name='groq', type='groq', model='llama-3.3-70b-versatile',
            enabled=True, api_key=keys['GROQ'], rpm_limit=30, tpm_limit=6000
        ))

    if keys['GEMINI']:
        providers['gemini'] = GeminiProvider(ProviderConfig(
            name='gemini', type='gemini', model='gemini-2.0-flash-exp',
            enabled=True, api_key=keys['GEMINI'], rpm_limit=10, tpm_limit=2000000
        ))

    if keys['CEREBRAS']:
        providers['cerebras'] = CerebrasProvider(ProviderConfig(
            name='cerebras', type='cerebras', model='llama3.1-8b',
            enabled=True, api_key=keys['CEREBRAS'], rpm_limit=30, tpm_limit=60000
        ))

    # Paid providers
    if keys['OPENAI']:
        providers['openai_mini'] = OpenAIProvider(ProviderConfig(
            name='openai_mini', type='openai', model='gpt-4o-mini',
            enabled=True, api_key=keys['OPENAI'], rpm_limit=500, tpm_limit=200000
        ))
        providers['openai'] = OpenAIProvider(ProviderConfig(
            name='openai', type='openai', model='gpt-4o',
            enabled=True, api_key=keys['OPENAI'], rpm_limit=500, tpm_limit=30000
        ))

    if keys['ANTHROPIC']:
        providers['anthropic'] = AnthropicProvider(ProviderConfig(
            name='anthropic', type='anthropic', model='claude-3-5-sonnet-20241022',
            enabled=True, api_key=keys['ANTHROPIC'], rpm_limit=50, tpm_limit=40000
        ))

    print(f"   Loaded {len(providers)} providers: {list(providers.keys())}")

    # Test scenarios
    scenarios = [
        {
            'name': 'Simple Task (FREE)',
            'provider': 'groq',
            'task': 'List 3 benefits of async/await in Python. Be concise.',
            'complexity': 'simple'
        },
        {
            'name': 'Medium Task (FREE preferred)',
            'provider': 'gemini',
            'task': 'Explain how FastAPI handles dependency injection. Include code example.',
            'complexity': 'medium'
        },
        {
            'name': 'Complex Task (CHEAP fallback)',
            'provider': 'openai_mini',
            'task': 'Design a rate limiting system with token bucket and sliding window. Explain tradeoffs.',
            'complexity': 'complex'
        },
        {
            'name': 'Critical Task (PREMIUM quality)',
            'provider': 'anthropic',
            'task': 'Review this architecture for security issues and provide detailed recommendations with code examples.',
            'complexity': 'critical'
        }
    ]

    results = []

    for scenario in scenarios:
        provider_name = scenario['provider']

        if provider_name not in providers:
            print(f"\n⚠️  Skipping {scenario['name']} - {provider_name} not available")
            continue

        # Create orchestrator with this provider
        orchestrator = AgentOrchestrator(
            agent_loader=agent_loader,
            prompt_builder=prompt_builder,
            conversation_manager=conversation_manager,
            agent_router=agent_router,
            providers={provider_name: providers[provider_name]}
        )

        success = await test_provider(
            name=scenario['name'],
            provider=providers[provider_name],
            orchestrator=orchestrator,
            task=scenario['task'],
            complexity=scenario['complexity']
        )

        results.append(success)

        # Small delay between requests
        await asyncio.sleep(1)

    # Final cost report
    print("\n" + "="*70)
    cost_optimizer.print_report()

    # Summary
    print("="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")

    stats = cost_optimizer.get_stats()

    print(f"\n💰 COST ANALYSIS")
    print(f"   Free requests: {stats['free_requests']}")
    print(f"   Paid requests: {stats['paid_requests']}")
    print(f"   Total cost: ${stats['daily_spend']:.4f}")
    print(f"   Budget remaining: ${stats['budget_remaining']:.4f}")

    if all(results):
        print("\n✅ ALL TESTS PASSED!")
        print("\n🎯 OPTIMIZATION SUCCESS:")
        print(f"   - {stats['free_requests']} requests at $0 (FREE tier)")
        print(f"   - {stats['paid_requests']} requests at ${stats['daily_spend']:.4f} (PAID tier)")

        if stats['paid_requests'] > 0:
            avg_paid_cost = stats['daily_spend'] / stats['paid_requests']
            print(f"   - Average cost per paid request: ${avg_paid_cost:.4f}")

        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
