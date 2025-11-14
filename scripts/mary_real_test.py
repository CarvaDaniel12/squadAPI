"""
Test Mary with REAL LLM Provider (Groq)
"""
import asyncio
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.loader import AgentLoader
from src.agents.prompt_builder import SystemPromptBuilder
from src.agents.conversation import ConversationManager
from src.agents.router import AgentRouter
from src.agents.orchestrator import AgentOrchestrator
from src.providers.groq_provider import GroqProvider
from src.providers.gemini_provider import GeminiProvider
from src.models.request import AgentExecutionRequest
from src.models.provider import ProviderConfig
import os


async def test_mary_real():
    """Test Mary with real Groq provider"""
    print("=" * 60)
    print("  MARY IN ACTION - REAL LLM TEST")
    print("=" * 60)
    print()
    
    # Load environment
    load_dotenv()
    
    # 1. Load agents
    print("[*] Loading agents...")
    loader = AgentLoader(bmad_path=".bmad", redis_client=None)
    await loader.load_all()
    print(f"[OK] Loaded {len(loader.list_agents())} agents")
    print()
    
    # 2. Create REAL provider (Groq)
    print("[*] Creating Groq provider (REAL LLM)...")
    
    groq_config = ProviderConfig(
        name="groq",
        type="groq",
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        rpm_limit=30,
        tpm_limit=20000
    )
    
    real_provider = GroqProvider(groq_config)
    print(f"[OK] Groq provider ready: {real_provider.model}")
    print()
    
    # 3. Create orchestrator with REAL provider
    orchestrator = AgentOrchestrator(
        agent_loader=loader,
        prompt_builder=SystemPromptBuilder(),
        conversation_manager=ConversationManager(redis_client=None),
        agent_router=AgentRouter(loader),
        rate_limiter=None,  # Disabled for test
        global_semaphore=None,  # Disabled for test
        provider_stub=real_provider  # Using REAL provider!
    )
    print("[OK] Orchestrator initialized with REAL Groq provider")
    print()
    
    # 4. Get agent info
    agent = await loader.get_agent("analyst")
    print("=" * 60)
    print(f"  Agent: {agent.title}")
    print("=" * 60)
    print(f"Name: {agent.name}")
    print(f"Role: {agent.persona.role}")
    print()
    
    # 5. Test Mary with REAL LLM!
    print("-" * 60)
    print("USER (Dani):")
    print()
    user_task = "Hello Mary! Briefly introduce yourself and tell me what you can help with. Keep it under 100 words."
    print(f"   {user_task}")
    print()
    print("-" * 60)
    print(f"MARY (thinking via Groq Llama-3.3-70B...):")
    print()
    
    request = AgentExecutionRequest(
        agent="analyst",
        task=user_task,
        user_id="real-test-user"
    )
    
    start = time.time()
    response = await orchestrator.execute(request)
    elapsed_ms = int((time.time() - start) * 1000)
    
    # 6. Display REAL response!
    print("   " + response.response.replace("\n", "\n   "))
    print()
    print("-" * 60)
    print()
    print("METADATA:")
    print(f"   Provider: {response.provider}")
    print(f"   Model: {response.model}")
    print(f"   Latency: {response.metadata.latency_ms}ms (total: {elapsed_ms}ms)")
    print(f"   Tokens: {response.metadata.tokens_input} -> {response.metadata.tokens_output}")
    print(f"   Request ID: {response.metadata.request_id}")
    print()
    print("=" * 60)
    print("[SUCCESS] MARY IS ALIVE WITH REAL LLM!")
    print("=" * 60)
    print()
    print("What just happened:")
    print("  1. Loaded Mary's agent definition (.bmad/bmm/agents/analyst.md)")
    print("  2. Built complete system prompt (~450 tokens)")
    print("  3. Called Groq API with Llama-3.3-70B")
    print("  4. Received REAL response from LLM")
    print("  5. Mary transformed external LLM into BMad agent!")
    print()
    print("Next steps:")
    print("  - Test with different agents (pm, dev, architect)")
    print("  - Test fallback chains (disable Groq, use Gemini)")
    print("  - Run interactive chat: python scripts/chat_with_mary.py")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(test_mary_real())
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

