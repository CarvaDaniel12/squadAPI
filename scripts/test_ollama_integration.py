"""Test script for Ollama integration with LocalPromptOptimizer.

This script validates:
1. Ollama is running and accessible
2. Required model (qwen3:8b) is available
3. LocalPromptOptimizer can synthesize responses
4. End-to-end flow works correctly
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import aiohttp
from src.providers.local_prompt_optimizer import LocalPromptOptimizer
from src.config.models import PromptOptimizerConfig
from src.models.prompt_plan import PromptPlan, AgileMetadata, SpecialistTask


async def check_ollama_running():
    """Check if Ollama is running and accessible."""
    print("\n1️⃣  Checking Ollama service...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://localhost:11434/api/tags",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = data.get("models", [])
                    print(f"   ✓ Ollama is running")
                    print(f"   ✓ Found {len(models)} models")

                    # List available models
                    if models:
                        print("\n   Available models:")
                        for model in models[:5]:  # Show first 5
                            name = model.get("name", "unknown")
                            size_gb = model.get("size", 0) / (1024**3)
                            print(f"     - {name} ({size_gb:.1f}GB)")

                    # Check for recommended model
                    model_names = [m.get("name", "") for m in models]
                    if any("qwen3" in name for name in model_names):
                        print("   ✓ qwen3 model found!")
                        return True
                    elif any("llama3.2" in name for name in model_names):
                        print("   ✓ llama3.2 model found (alternative)")
                        return True
                    elif any("phi3" in name for name in model_names):
                        print("   ✓ phi3 model found (alternative)")
                        return True
                    else:
                        print("\n   ⚠️  Recommended model not found")
                        print("   💡 Run: ollama pull qwen3:8b")
                        return False
                else:
                    print(f"   ✗ Ollama returned HTTP {resp.status}")
                    return False
    except asyncio.TimeoutError:
        print("   ✗ Ollama not responding (timeout)")
        print("   💡 Is Ollama running? Try: ollama serve")
        return False
    except Exception as exc:
        print(f"   ✗ Error connecting to Ollama: {exc}")
        print("   💡 Install Ollama from https://ollama.ai")
        return False


async def test_simple_generation():
    """Test basic Ollama generation."""
    print("\n2️⃣  Testing basic generation...")
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "qwen3:8b",
                "prompt": "Say 'Hello from Ollama!' and nothing else.",
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 50
                }
            }

            async with session.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    response = result.get("response", "").strip()
                    print(f"   ✓ Model response: {response[:100]}")
                    return True
                else:
                    error = await resp.text()
                    print(f"   ✗ Generation failed: HTTP {resp.status}")
                    print(f"   Error: {error}")
                    return False
    except Exception as exc:
        print(f"   ✗ Generation error: {exc}")
        return False


async def test_prompt_optimizer():
    """Test LocalPromptOptimizer with Ollama."""
    print("\n3️⃣  Testing LocalPromptOptimizer...")

    # Create config
    config = PromptOptimizerConfig(
        enabled=True,
        runtime="ollama",
        endpoint="http://localhost:11434",
        model_path="qwen3:8b",
        max_context_tokens=4096,
        temperature=0.3,
        bmad_config="config/bmad_method.yaml",
        aggregation_prompt="Summarize outputs"
    )

    optimizer = LocalPromptOptimizer(config)

    # Create a mock PromptPlan
    plan = PromptPlan(
        user_request="Explain how async/await works in Python",
        normalized_problem="Technical explanation needed",
        agile=AgileMetadata(
            sprint_goal="Test Ollama integration",
            backlog_item_id="TEST-001",
            priority="P2",
            acceptance_criteria=["Ollama responds correctly"],
            ceremonies=["Planning"],
            bmad_phase="Blueprint",
            compliance_checklist=["Test executed"],
            requires_approval=False
        ),
        tasks=[
            SpecialistTask(
                id="task-1",
                role="developer",
                provider="groq",
                expertise_context="Python expert",
                task_prompt="Explain async/await",
                expected_outputs=["Explanation"],
                definition_of_done=["Complete"]
            )
        ],
        aggregation_strategy="local_summarizer",
        post_processing_prompt="Summarize"
    )

    # Test synthesis with multiple outputs
    specialist_outputs = [
        "async/await is Python's syntax for asynchronous programming. It allows concurrent execution without blocking.",
        "The async keyword defines a coroutine function. await pauses execution until the awaited operation completes.",
        "This pattern is essential for I/O-bound operations like API calls, file operations, and network requests."
    ]

    print("   📝 Synthesizing 3 specialist outputs...")
    synthesized = await optimizer.synthesize(plan, specialist_outputs)

    if synthesized:
        print(f"   ✓ Synthesis successful!")
        print(f"\n   Synthesized response ({len(synthesized)} chars):")
        print(f"   {synthesized[:300]}...")
        return True
    else:
        print("   ✗ Synthesis failed (returned None)")
        return False


async def main():
    """Run all Ollama integration tests."""
    print("=" * 60)
    print("🧪 Ollama Integration Test Suite")
    print("=" * 60)

    results = []

    # Test 1: Ollama running
    results.append(("Ollama Service", await check_ollama_running()))

    # Test 2: Basic generation
    if results[0][1]:  # Only if Ollama is running
        results.append(("Basic Generation", await test_simple_generation()))
    else:
        results.append(("Basic Generation", False))
        print("\n⚠️  Skipping remaining tests (Ollama not available)")

    # Test 3: Prompt optimizer
    if all(r[1] for r in results):  # Only if previous tests passed
        results.append(("Prompt Optimizer", await test_prompt_optimizer()))
    else:
        results.append(("Prompt Optimizer", False))
        print("\n⚠️  Skipping prompt optimizer test")

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} {name}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)

    print(f"\nTotal: {passed_count}/{total_count} passed")

    if passed_count == total_count:
        print("\n🎉 All tests passed! Ollama integration is ready.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
