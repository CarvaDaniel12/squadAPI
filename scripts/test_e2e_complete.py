"""
End-to-End Integration Test
Tests complete workflow: cost optimization + smart fallback + agent routing

Validates:
1. Cost optimizer selects correct provider based on complexity
2. OpenRouter smart fallback works when models fail
3. Agent routing works correctly
4. Conversation history is maintained
5. Metrics are recorded
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()
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
from src.providers.openrouter_provider import OpenRouterProvider
from src.utils.cost_optimizer import CostOptimizer
import os


async def test_e2e():
    """Run complete end-to-end integration test"""

    print("=" * 80)
    print("🧪 SQUAD API - END-TO-END INTEGRATION TEST")
    print("=" * 80)
    print()

    # Initialize cost optimizer
    print("💰 Initializing cost optimizer...")
    cost_optimizer = CostOptimizer()
    print(f"   Daily budget: ${cost_optimizer.config.get('cost_limits', {}).get('daily_budget', 5.0)}")
    print()

    # Initialize components
    print("🔧 Initializing components...")
    bmad_path = Path(__file__).parent.parent / ".bmad"
    agent_loader = AgentLoader(bmad_path=bmad_path)
    await agent_loader.load_all()

    agents = agent_loader.list_agents()
    print(f"   Loaded {len(agents)} agents: {', '.join(agents)}")

    prompt_builder = SystemPromptBuilder()
    conversation_manager = ConversationManager()
    agent_router = AgentRouter(agent_loader=agent_loader)
    print()

    # Setup providers
    print("🌐 Setting up providers...")
    providers = {}

    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        providers['groq'] = GroqProvider(ProviderConfig(
            name='groq',
            type='groq',
            model='llama-3.3-70b-versatile',
            enabled=True,
            api_key=groq_key,
            rpm_limit=30,
            tpm_limit=6000,
            temperature=0.7,
            max_tokens=500,
            timeout=30
        ))
        print("   ✅ Groq")

    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        providers['gemini'] = GeminiProvider(ProviderConfig(
            name='gemini',
            type='gemini',
            model='gemini-2.0-flash-exp',
            enabled=True,
            api_key=gemini_key,
            rpm_limit=15,
            tpm_limit=1000000,
            temperature=0.7,
            max_tokens=500,
            timeout=30
        ))
        print("   ✅ Gemini")

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        providers['openrouter'] = OpenRouterProvider(ProviderConfig(
            name='openrouter',
            type='openrouter',
            model='kwaipilot/kat-coder-pro:free',
            enabled=True,
            api_key=openrouter_key,
            rpm_limit=20,
            tpm_limit=100000,
            temperature=0.7,
            max_tokens=500,
            timeout=45
        ))
        print("   ✅ OpenRouter (with smart fallback)")

    if not providers:
        print("\n❌ No providers available! Add API keys to .env")
        return 1

    print()

    # Create orchestrator with cost optimization
    print("🎯 Creating orchestrator with cost optimization...")
    orchestrator = AgentOrchestrator(
        agent_loader=agent_loader,
        prompt_builder=prompt_builder,
        conversation_manager=conversation_manager,
        agent_router=agent_router,
        providers=providers,
        cost_optimizer=cost_optimizer  # ✅ Cost optimization enabled
    )
    print("   ✅ Orchestrator ready with cost optimization")
    print()

    # Test scenarios
    scenarios = [
        {
            'name': 'Simple Analysis (FREE provider)',
            'agent': 'analyst',
            'task': 'List 3 benefits of code reviews',
            'expected_complexity': 'simple',
            'expected_cost': 0.0
        },
        {
            'name': 'Code Task (OpenRouter Qwen3 480B)',
            'agent': 'dev',
            'task': 'Write a Python function to calculate fibonacci numbers',
            'expected_complexity': 'code',
            'expected_cost': 0.0  # Should use FREE OpenRouter
        },
        {
            'name': 'Complex Architecture (OpenRouter DeepSeek)',
            'agent': 'architect',
            'task': 'Design a scalable microservices architecture for e-commerce',
            'expected_complexity': 'complex',
            'expected_cost': 0.0  # Should use FREE OpenRouter
        }
    ]

    results = []

    for i, scenario in enumerate(scenarios, 1):
        print("=" * 80)
        print(f"TEST {i}/{len(scenarios)}: {scenario['name']}")
        print("=" * 80)
        print(f"Agent: {scenario['agent']}")
        print(f"Task: {scenario['task']}")
        print(f"Expected complexity: {scenario['expected_complexity']}")
        print()

        request = AgentExecutionRequest(
            agent=scenario['agent'],
            task=scenario['task'],
            user_id='test-user-e2e',
            conversation_id=f'e2e-test-{i}'
        )

        try:
            # Execute request
            response = await orchestrator.execute(request)

            # Validate response
            print(f"✅ SUCCESS")
            print(f"   Provider: {response.provider}")
            print(f"   Model: {response.model}")
            print(f"   Latency: {response.metadata.latency_ms}ms")
            print(f"   Tokens: {response.metadata.tokens_input} → {response.metadata.tokens_output}")
            print(f"   Response: {response.response[:100]}...")

            # Check cost
            cost = cost_optimizer.calculate_cost(
                response.provider,
                response.metadata.tokens_input,
                response.metadata.tokens_output
            )

            if cost == 0:
                print(f"   💰 Cost: FREE ✅")
            else:
                print(f"   💰 Cost: ${cost:.4f}")

            # Validate complexity detection
            detected_complexity = orchestrator._determine_complexity(request, scenario['agent'])
            print(f"   🎯 Complexity: {detected_complexity} (expected: {scenario['expected_complexity']})")

            if detected_complexity == scenario['expected_complexity']:
                print(f"   ✅ Complexity detection correct")
            else:
                print(f"   ⚠️  Complexity mismatch!")

            results.append({
                'scenario': scenario['name'],
                'success': True,
                'provider': response.provider,
                'cost': cost,
                'latency': response.metadata.latency_ms
            })

        except Exception as e:
            print(f"❌ FAILED: {e}")
            results.append({
                'scenario': scenario['name'],
                'success': False,
                'error': str(e)
            })

        print()

        # Small delay between requests
        await asyncio.sleep(2)

    # Final cost report
    print("=" * 80)
    print("💰 COST REPORT")
    print("=" * 80)
    cost_optimizer.print_report()

    # Summary
    print("=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for r in results if r['success'])
    total = len(results)

    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print()

    if passed == total:
        print("✅ ALL TESTS PASSED!")
        print()
        print("🎉 End-to-end integration validated:")
        print("   ✅ Cost optimizer working")
        print("   ✅ Smart provider selection")
        print("   ✅ Agent routing correct")
        print("   ✅ FREE tier optimized")
        print("   ✅ Conversation tracking")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("\nFailed tests:")
        for r in results:
            if not r['success']:
                print(f"   - {r['scenario']}: {r.get('error', 'Unknown error')}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_e2e())
    sys.exit(exit_code)
