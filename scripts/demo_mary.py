#!/usr/bin/env python
"""
Demo: Mary in Action (Stub Provider)

Quick demo showing Mary working WITHOUT real API keys (using stub provider).
Perfect for testing the system without configuring API keys.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.loader import AgentLoader
from src.agents.prompt_builder import SystemPromptBuilder
from src.agents.conversation import ConversationManager
from src.agents.router import AgentRouter
from src.agents.orchestrator import AgentOrchestrator
from src.providers.stub_provider import StubLLMProvider
from src.models.request import AgentExecutionRequest


async def demo_mary():
    """Demo Mary (analyst) with stub provider"""
    
    print("=" * 60)
    print("  DEMO: Mary in Action (Stub Provider)")
    print("=" * 60)
    print()
    
    # 1. Initialize components
    print("[*] Initializing Squad API (stub mode)...")
    
    loader = AgentLoader(bmad_path=".bmad", redis_client=None)
    await loader.load_all()
    print(f"  [OK] Loaded {len(loader.list_agents())} agents")
    
    # Create stub provider
    stub = StubLLMProvider(
        fixed_response="""Hello Dani! I'm Mary, your Business Analyst from the Squad team.

I can help you with:
1. Requirements analysis and elicitation
2. Stakeholder identification and management
3. User story creation and refinement
4. Acceptance criteria definition
5. PRD and technical specification review
6. Current sprint status analysis

What would you like to work on today?""",
        simulate_latency=True
    )
    print(f"  [OK] Stub provider ready (simulates Groq)")
    
    orchestrator = AgentOrchestrator(
        agent_loader=loader,
        prompt_builder=SystemPromptBuilder(),
        conversation_manager=ConversationManager(redis_client=None),
        agent_router=AgentRouter(loader),
        provider_stub=stub
    )
    print(f"  [OK] Orchestrator initialized")
    print()
    
    # 2. Get agent info
    agent = await loader.get_agent("analyst")
    print("=" * 60)
    print(f"  Agent: {agent.title}")
    print("=" * 60)
    print()
    print(f"Name: {agent.name}")
    print(f"Role: {agent.persona.role}")
    print(f"Identity: {agent.persona.identity[:80]}...")
    print()
    
    # 3. Execute agent
    print("-" * 60)
    print("User (Dani):")
    print()
    user_task = "Hello Mary! Can you introduce yourself and tell me what you can help with?"
    print(f"   {user_task}")
    print()
    print("-" * 60)
    print("Mary (thinking...):")
    print()
    
    request = AgentExecutionRequest(
        agent="analyst",
        task=user_task,
        user_id="demo-user"
    )
    
    response = await orchestrator.execute(request)
    
    # 4. Display response
    print(f"   {response.response}")
    print()
    print("-" * 60)
    print()
    print("Metadata:")
    print(f"   Provider: {response.provider}")
    print(f"   Model: {response.model}")
    print(f"   Latency: {response.metadata.latency_ms}ms")
    print(f"   Tokens: {response.metadata.tokens_input} -> {response.metadata.tokens_output}")
    print(f"   Request ID: {response.metadata.request_id}")
    print()
    
    # 5. Verify stub tracking
    print("Stub Provider Verification:")
    print(f"   Calls made: {stub.call_count}")
    print(f"   Last call user prompt: {stub.get_last_call()['user_prompt'][:50]}...")
    print()
    
    print("[SUCCESS] DEMO COMPLETE!")
    print()
    print("Next steps:")
    print("  1. Configure real API keys (.env file)")
    print("  2. Run: python scripts/test_providers.py --all")
    print("  3. Run: python scripts/chat_with_mary.py")
    print()
    print("See: docs/TESTING-REAL-PROVIDERS.md")
    print()


def main():
    """Main entry point"""
    try:
        asyncio.run(demo_mary())
    except KeyboardInterrupt:
        print("\n\n[WARN] Demo interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

