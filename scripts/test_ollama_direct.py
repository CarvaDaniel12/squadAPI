"""Direct Ollama test - simple and working."""
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import aiohttp


async def test_ollama_basic():
    """Test Ollama with a simple request."""
    print("Testing Ollama basic generation...")

    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "qwen3:8b",
                "prompt": "Say 'Ollama is working!' and nothing else.",
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
                    print(f"SUCCESS: Model response: {response}")
                    return True
                else:
                    error = await resp.text()
                    print(f"ERROR: Generation failed: HTTP {resp.status}")
                    print(f"Error: {error}")
                    return False
    except Exception as exc:
        print(f"ERROR: Generation error: {exc}")
        return False


async def test_local_optimizer():
    """Test the LocalPromptOptimizer."""
    print("\nTesting LocalPromptOptimizer...")

    try:
        from src.providers.local_prompt_optimizer import LocalPromptOptimizer
        from src.config.models import PromptOptimizerConfig
        from src.models.prompt_plan import PromptPlan, AgileMetadata, SpecialistTask

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
        print(f"Optimizer enabled: {optimizer.enabled}")

        # Create a simple prompt plan
        plan = PromptPlan(
            user_request="Test request",
            normalized_problem="Simple test",
            agile=AgileMetadata(
                sprint_goal="Test Ollama integration",
                backlog_item_id="TEST-001",
                priority="P1",
                acceptance_criteria=["Works"],
                ceremonies=["Planning"],
                bmad_phase="Blueprint",
                compliance_checklist=["Test completed"],
                requires_approval=False
            ),
            tasks=[
                SpecialistTask(
                    id="task-1",
                    role="developer",
                    provider="ollama",
                    expertise_context="Test expert",
                    task_prompt="Test task",
                    expected_outputs=["Test output"],
                    definition_of_done=["Complete"]
                )
            ],
            aggregation_strategy="local_summarizer",
            post_processing_prompt="Summarize"
        )

        # Test synthesis
        outputs = [
            "This is test output 1",
            "This is test output 2",
            "This is test output 3"
        ]

        print(f"Testing synthesis with {len(outputs)} outputs...")
        synthesized = await optimizer.synthesize(plan, outputs)

        if synthesized:
            print(f"SUCCESS: Synthesis worked!")
            print(f"Result: {synthesized[:200]}...")
            return True
        else:
            print("WARNING: Synthesis returned None")
            return False

    except Exception as exc:
        print(f"ERROR: Local optimizer test failed: {exc}")
        return False


async def main():
    """Run the direct tests."""
    print("=" * 50)
    print("DIRECT OLLAMA INTEGRATION TEST")
    print("=" * 50)

    # Test 1: Basic Ollama
    result1 = await test_ollama_basic()

    # Test 2: Local optimizer
    result2 = await test_local_optimizer()

    print("\n" + "=" * 50)
    print("RESULTS:")
    print(f"Basic Ollama: {'PASS' if result1 else 'FAIL'}")
    print(f"Local Optimizer: {'PASS' if result2 else 'FAIL'}")

    if result1 and result2:
        print("\nSUCCESS: All tests passed!")
        return 0
    else:
        print("\nWARNING: Some tests failed")
        return 1


if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
