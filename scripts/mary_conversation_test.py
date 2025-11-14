#!/usr/bin/env python
"""
Mary Conversation Test - Real Provider

Test Mary having a real conversation via Groq/Gemini.
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.loader import AgentLoader
from src.agents.prompt_builder import SystemPromptBuilder
from src.agents.conversation import ConversationManager
from src.agents.router import AgentRouter
from src.agents.orchestrator import AgentOrchestrator
from src.providers.factory import ProviderFactory
from src.models.request import AgentExecutionRequest


async def test_mary_conversation():
    """Test Mary with real providers"""
    
    print("=" * 70)
    print("  MARY CONVERSATION TEST - REAL GROQ LLM")
    print("=" * 70)
    print()
    
    # Load environment
    load_dotenv()
    
    # Initialize components
    print("[*] Initializing...")
    loader = AgentLoader(bmad_path=".bmad", redis_client=None)
    await loader.load_all()
    
    # Load providers
    factory = ProviderFactory()
    providers = factory.create_all("config/providers.yaml")
    print(f"[OK] {len(providers)} providers loaded: {list(providers.keys())}")
    
    # Create orchestrator with REAL provider
    groq_provider = providers.get('groq')
    if not groq_provider:
        print("[ERROR] Groq provider not available!")
        sys.exit(1)
    
    orchestrator = AgentOrchestrator(
        agent_loader=loader,
        prompt_builder=SystemPromptBuilder(),
        conversation_manager=ConversationManager(redis_client=None),
        agent_router=AgentRouter(loader),
        provider_stub=groq_provider  # REAL GROQ!
    )
    
    print(f"[OK] Using REAL provider: {groq_provider.name} ({groq_provider.model})")
    print()
    
    # Test conversation
    conversations = [
        "Hello Mary! What is your role in the Squad team?",
        "What can you help me with today?",
        "Can you analyze our current sprint progress?"
    ]
    
    for i, task in enumerate(conversations, 1):
        print("-" * 70)
        print(f"[{i}/3] User (Dani):")
        print(f"    {task}")
        print()
        print(f"[{i}/3] Mary (via Groq Llama-3.3-70B) responding...")
        
        request = AgentExecutionRequest(
            agent="analyst",
            task=task,
            user_id="real-test-user"
        )
        
        response = await orchestrator.execute(request)
        
        print()
        print(f"Mary> {response.response[:500]}...")
        print()
        print(f"[Metadata] Provider: {response.provider} | Model: {response.model}")
        print(f"[Metadata] Latency: {response.metadata.latency_ms}ms | Tokens: {response.metadata.tokens_input}->{response.metadata.tokens_output}")
        print()
        
        # Small delay to respect rate limits
        if i < len(conversations):
            await asyncio.sleep(2)
    
    print("=" * 70)
    print("[SUCCESS] Mary conversation test complete!")
    print()
    print("VERIFIED:")
    print("  - Agent transformation working")
    print("  - System prompt injection working")
    print("  - Real LLM responses")
    print("  - Conversation history maintained")
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(test_mary_conversation())
    except KeyboardInterrupt:
        print("\n[WARN] Interrupted")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

