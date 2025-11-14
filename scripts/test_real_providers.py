"""
Real Provider Integration Test - Squad API
Tests orchestrator with actual external APIs (Groq, Gemini, etc.)

Requires API keys in .env file:
- GROQ_API_KEY
- GEMINI_API_KEY
- CEREBRAS_API_KEY
- OPENROUTER_API_KEY
"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Add src to path
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


async def test_groq_provider():
    """Test with real Groq API"""

    print("🚀 Testing Groq Provider (Llama 3.3 70B)\n")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("⚠️  GROQ_API_KEY not found in environment")
        return False

    print(f"✅ API Key loaded: {api_key[:10]}...")

    # Initialize components
    bmad_path = Path(__file__).parent.parent / "public" / ".bmad"
    agent_loader = AgentLoader(bmad_path=bmad_path)
    prompt_builder = SystemPromptBuilder()
    conversation_manager = ConversationManager()
    agent_router = AgentRouter(agent_loader=agent_loader)

    # Create Groq provider
    groq_config = ProviderConfig(
        name="groq",
        type="groq",
        model="llama-3.3-70b-versatile",
        enabled=True,
        api_key=api_key,
        rpm_limit=30,
        tpm_limit=6000
    )
    groq_provider = GroqProvider(config=groq_config)

    orchestrator = AgentOrchestrator(
        agent_loader=agent_loader,
        prompt_builder=prompt_builder,
        conversation_manager=conversation_manager,
        agent_router=agent_router,
        providers={"groq": groq_provider}
    )

    # Test execution
    print("\n📝 Sending request to Groq...")

    request = AgentExecutionRequest(
        agent="analyst",
        task="List 3 key benefits of using async/await in Python. Be concise.",
        user_id="test-user",
        conversation_id="test-groq-001"
    )

    try:
        response = await orchestrator.execute(request)

        print("\n✅ Groq Response Received!\n")
        print(f"📊 Metadata:")
        print(f"   Provider: {response.provider}")
        print(f"   Model: {response.model}")
        print(f"   Latency: {response.metadata.latency_ms}ms")
        print(f"   Tokens In: {response.metadata.tokens_input}")
        print(f"   Tokens Out: {response.metadata.tokens_output}")
        print(f"\n💬 Response:\n{response.response}\n")

        return True

    except Exception as e:
        print(f"\n❌ Groq test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_gemini_provider():
    """Test with real Gemini API"""

    print("\n" + "="*60)
    print("🚀 Testing Gemini Provider (Gemini 2.0 Flash)\n")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️  GEMINI_API_KEY not found in environment")
        return False

    print(f"✅ API Key loaded: {api_key[:10]}...")

    # Initialize components
    bmad_path = Path(__file__).parent.parent / ".bmad"
    agent_loader = AgentLoader(bmad_path=bmad_path)

    # Load agents
    await agent_loader.load_all()

    prompt_builder = SystemPromptBuilder()
    conversation_manager = ConversationManager()
    agent_router = AgentRouter(agent_loader=agent_loader)

    # Create Gemini provider
    gemini_config = ProviderConfig(
        name="gemini",
        type="gemini",
        model="gemini-2.0-flash-exp",
        enabled=True,
        api_key=api_key,
        rpm_limit=10,
        tpm_limit=2000000
    )
    gemini_provider = GeminiProvider(config=gemini_config)

    orchestrator = AgentOrchestrator(
        agent_loader=agent_loader,
        prompt_builder=prompt_builder,
        conversation_manager=conversation_manager,
        agent_router=agent_router,
        providers={"gemini": gemini_provider}
    )

    # Test execution
    print("\n📝 Sending request to Gemini...")

    request = AgentExecutionRequest(
        agent="analyst",
        task="What are the main advantages of using FastAPI? List 3 points briefly.",
        user_id="test-user",
        conversation_id="test-gemini-001"
    )

    try:
        response = await orchestrator.execute(request)

        print("\n✅ Gemini Response Received!\n")
        print(f"📊 Metadata:")
        print(f"   Provider: {response.provider}")
        print(f"   Model: {response.model}")
        print(f"   Latency: {response.metadata.latency_ms}ms")
        print(f"   Tokens In: {response.metadata.tokens_input}")
        print(f"   Tokens Out: {response.metadata.tokens_output}")
        print(f"\n💬 Response:\n{response.response}\n")

        return True

    except Exception as e:
        print(f"\n❌ Gemini test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all real provider tests"""

    print("="*60)
    print("SQUAD API - REAL PROVIDER INTEGRATION TESTS")
    print("="*60 + "\n")

    # Check .env loaded
    print("🔑 Checking API Keys...")
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not groq_key and not gemini_key:
        print("\n❌ No API keys found!")
        print("Make sure .env file exists with:")
        print("  - GROQ_API_KEY=xxx")
        print("  - GEMINI_API_KEY=xxx")
        return 1

    results = []

    # Test Groq
    if groq_key:
        results.append(await test_groq_provider())

    # Test Gemini
    if gemini_key:
        results.append(await test_gemini_provider())

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")

    if all(results):
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
