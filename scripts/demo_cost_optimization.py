"""
Cost Optimization Demo
Demonstrates intelligent provider routing to minimize costs

Shows:
1. Simple tasks → Free providers only
2. Complex tasks → Free first, paid fallback
3. Budget tracking and enforcement
4. Cost reporting
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.cost_optimizer import CostOptimizer


async def demo_cost_optimization():
    """Demonstrate cost optimization strategies"""

    print("="*70)
    print("💰 COST OPTIMIZATION STRATEGY DEMO")
    print("="*70)
    print()

    optimizer = CostOptimizer()

    # Simulate different task scenarios
    scenarios = [
        {
            'name': 'Simple Analysis (Free Only)',
            'complexity': 'simple',
            'tokens_in': 500,
            'tokens_out': 300,
            'count': 5
        },
        {
            'name': 'Medium Code Generation (Prefer Free)',
            'complexity': 'medium',
            'tokens_in': 1500,
            'tokens_out': 800,
            'count': 3
        },
        {
            'name': 'Complex Architecture (Allow Paid)',
            'complexity': 'complex',
            'tokens_in': 3000,
            'tokens_out': 2000,
            'count': 2
        },
        {
            'name': 'Critical Production Review (Premium OK)',
            'complexity': 'critical',
            'tokens_in': 5000,
            'tokens_out': 3000,
            'count': 1
        }
    ]

    print("📋 SCENARIO TESTING\n")

    for scenario in scenarios:
        print(f"🔹 {scenario['name']}")
        print(f"   Complexity: {scenario['complexity']}")
        print(f"   Tokens: {scenario['tokens_in']} in / {scenario['tokens_out']} out")
        print(f"   Requests: {scenario['count']}")

        # Select provider for this scenario
        available = ['groq', 'cerebras', 'gemini', 'openai_mini', 'openai', 'anthropic']
        provider = optimizer.select_provider(
            task_complexity=scenario['complexity'],
            available_providers=available
        )

        print(f"   ✅ Selected: {provider}")

        # Simulate usage
        for i in range(scenario['count']):
            optimizer.record_usage(
                provider=provider,
                tokens_input=scenario['tokens_in'],
                tokens_output=scenario['tokens_out'],
                user_id=f"user-{i % 3}",  # 3 different users
                conversation_id=f"conv-{scenario['complexity']}-{i}"
            )

        # Calculate cost for this scenario
        total_cost = optimizer.calculate_cost(
            provider,
            scenario['tokens_in'] * scenario['count'],
            scenario['tokens_out'] * scenario['count']
        )

        if total_cost > 0:
            print(f"   💵 Cost: ${total_cost:.4f}")
        else:
            print(f"   🆓 Cost: FREE")

        print()

    # Print final report
    optimizer.print_report()

    # Cost comparison
    print("="*70)
    print("📊 COST COMPARISON: Free vs Paid Strategy")
    print("="*70)
    print()

    # Calculate what it would cost if we used only OpenAI
    total_tokens_in = sum(s['tokens_in'] * s['count'] for s in scenarios)
    total_tokens_out = sum(s['tokens_out'] * s['count'] for s in scenarios)

    openai_cost = optimizer.calculate_cost('openai', total_tokens_in, total_tokens_out)
    anthropic_cost = optimizer.calculate_cost('anthropic', total_tokens_in, total_tokens_out)
    optimized_cost = sum(optimizer.daily_costs.values())

    print(f"If we used ONLY OpenAI:     ${openai_cost:.4f}")
    print(f"If we used ONLY Anthropic:  ${anthropic_cost:.4f}")
    print(f"Our optimized strategy:     ${optimized_cost:.4f}")
    print()

    if optimized_cost > 0:
        openai_savings = ((openai_cost - optimized_cost) / openai_cost * 100) if openai_cost > 0 else 0
        anthropic_savings = ((anthropic_cost - optimized_cost) / anthropic_cost * 100) if anthropic_cost > 0 else 0

        print(f"💰 Savings vs OpenAI:       {openai_savings:.1f}%")
        print(f"💰 Savings vs Anthropic:    {anthropic_savings:.1f}%")
    else:
        print(f"💰 Savings:                  100% (all free!)")

    print()
    print("="*70)
    print("✅ OPTIMIZATION STRATEGY BENEFITS")
    print("="*70)
    print()
    print("✓ Simple tasks use FREE providers (Groq, Gemini, Cerebras)")
    print("✓ Complex tasks try FREE first, fallback to paid if needed")
    print("✓ Budget tracking prevents overspending")
    print("✓ Automatic fallback to free when budget exceeded")
    print("✓ Per-user and per-conversation cost tracking")
    print("✓ Real-time cost monitoring and alerts")
    print()
    print("🎯 RECOMMENDED PROVIDER STRATEGY:")
    print("="*70)
    print()
    print("FREE TIER (Use for 80-90% of requests):")
    print("  • Groq (Llama 3.3 70B)      - Best for code & analysis")
    print("  • Gemini 2.0 Flash          - Best for fast responses")
    print("  • Cerebras (Llama 3.1 8B)   - Best for simple tasks")
    print()
    print("PAID TIER (Use only when necessary):")
    print("  • OpenAI GPT-4o-mini        - Cheap fallback ($0.15/$0.60)")
    print("  • OpenAI GPT-4o             - Complex reasoning ($2.50/$10.00)")
    print("  • Anthropic Claude 3.5      - Critical production ($3.00/$15.00)")
    print()
    print("💡 TIP: With $5/day budget and this strategy, you can handle:")
    print("   - 1000+ free requests/day (Groq, Gemini, Cerebras)")
    print("   - 50-100 paid requests/day (when free tier unavailable)")
    print("   - ~5 critical requests/day (premium models)")
    print()


if __name__ == "__main__":
    asyncio.run(demo_cost_optimization())
