"""
Basic Integration Test - Squad API
Tests orchestrator with stub provider (no external API keys needed)
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.loader import AgentLoader
from src.agents.prompt_builder import SystemPromptBuilder
from src.agents.conversation import ConversationManager
from src.agents.router import AgentRouter
from src.agents.orchestrator import AgentOrchestrator
from src.models.request import AgentExecutionRequest
from src.providers.stub_provider import StubProvider


async def test_basic_orchestration():
    """Test basic agent orchestration with stub provider"""

    print("🚀 Starting Squad API Integration Test (Stub Provider)\n")

    # 1. Initialize components
    print("📦 Initializing components...")
    agent_loader = AgentLoader()
    prompt_builder = SystemPromptBuilder()
    conversation_manager = ConversationManager()
    agent_router = AgentRouter()

    # Use stub provider (no API keys needed)
    stub_provider = StubProvider()
    providers = {"stub": stub_provider}

    # Create orchestrator
    orchestrator = AgentOrchestrator(
        agent_loader=agent_loader,
        prompt_builder=prompt_builder,
        conversation_manager=conversation_manager,
        agent_router=agent_router,
        providers=providers
    )

    print("✅ Components initialized\n")

    # 2. Test execution
    print("🎯 Testing agent execution...")

    request = AgentExecutionRequest(
        agent="analyst",
        task="Analyze the current project status and provide recommendations",
        user_id="test-user",
        conversation_id="test-integration-001"
    )

    try:
        response = await orchestrator.execute(request)

        print("✅ Execution successful!\n")
        print(f"📊 Response Details:")
        print(f"   Agent: {response.agent_name}")
        print(f"   Provider: {response.provider}")
        print(f"   Model: {response.model}")
        print(f"   Latency: {response.metadata.latency_ms}ms")
        print(f"   Tokens In: {response.metadata.tokens_input}")
        print(f"   Tokens Out: {response.metadata.tokens_output}")
        print(f"\n💬 Response:\n{response.response[:200]}...")

        return True

    except Exception as e:
        print(f"❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_conversation_continuity():
    """Test multi-turn conversation"""

    print("\n" + "="*60)
    print("🔄 Testing Conversation Continuity\n")

    agent_loader = AgentLoader()
    prompt_builder = SystemPromptBuilder()
    conversation_manager = ConversationManager()
    agent_router = AgentRouter()
    stub_provider = StubProvider()

    orchestrator = AgentOrchestrator(
        agent_loader=agent_loader,
        prompt_builder=prompt_builder,
        conversation_manager=conversation_manager,
        agent_router=agent_router,
        providers={"stub": stub_provider}
    )

    conv_id = "test-conversation-002"

    # First message
    print("📝 Message 1...")
    req1 = AgentExecutionRequest(
        agent="analyst",
        task="What are the main risks?",
        user_id="test-user",
        conversation_id=conv_id
    )
    resp1 = await orchestrator.execute(req1)
    print(f"   Response: {resp1.response[:100]}...")

    # Second message (should have context)
    print("\n📝 Message 2 (with context)...")
    req2 = AgentExecutionRequest(
        agent="analyst",
        task="How can we mitigate them?",
        user_id="test-user",
        conversation_id=conv_id
    )
    resp2 = await orchestrator.execute(req2)
    print(f"   Response: {resp2.response[:100]}...")

    # Check conversation history
    history = await conversation_manager.get_messages("test-user", "analyst")
    print(f"\n✅ Conversation has {len(history)} messages in history")

    return True


async def main():
    """Run all integration tests"""

    print("="*60)
    print("SQUAD API - INTEGRATION TESTS")
    print("="*60 + "\n")

    results = []

    # Test 1: Basic orchestration
    results.append(await test_basic_orchestration())

    # Test 2: Conversation continuity
    results.append(await test_conversation_continuity())

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
