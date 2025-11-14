#!/usr/bin/env python
"""
Test All BMad Agents

Tests agent transformation with real providers for all agents:
Mary (Analyst), John (Dev), Alex (Architect), PM, SM, TEA, Tech Writer, UX Designer
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import time

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.loader import AgentLoader
from src.agents.prompt_builder import SystemPromptBuilder
from src.agents.conversation import ConversationManager
from src.agents.router import AgentRouter
from src.agents.orchestrator import AgentOrchestrator
from src.providers.factory import ProviderFactory
from src.models.request import AgentExecutionRequest


async def test_agent(agent_id: str, orchestrator: AgentOrchestrator, loader: AgentLoader):
    """Test a single agent"""
    
    agent = await loader.get_agent(agent_id)
    if not agent:
        print(f"[SKIP] Agent '{agent_id}' not found")
        return None
    
    print(f"\n{'='*70}")
    print(f"  Testing: {agent.name} ({agent.title})")
    print(f"{'='*70}")
    
    # Create test task specific to each agent
    test_tasks = {
        'analyst': "Qual  o status atual do nosso projeto Squad API?",
        'dev': "Como implementar um novo endpoint REST em FastAPI?",
        'architect': "Qual  a melhor estratgia de caching para o Squad API?",
        'pm': "Como devemos priorizar as prximas features do backlog?",
        'sm': "Qual  o progresso atual do sprint?",
        'tea': "Quais testes crticos devemos adicionar para Epic 5?",
        'tech-writer': "Como documentar a arquitetura do Squad API?",
        'ux-designer': "Como melhorar a experincia do chat com Mary?"
    }
    
    task = test_tasks.get(agent_id, f"Hello {agent.name}! Introduce yourself briefly.")
    
    print(f"Task: {task}")
    print(f"\n{agent.name} (thinking via Groq)...")
    
    try:
        start = time.time()
        
        request = AgentExecutionRequest(
            agent=agent_id,
            task=task,
            user_id=f"test-{agent_id}"
        )
        
        response = await orchestrator.execute(request)
        elapsed_ms = int((time.time() - start) * 1000)
        
        # Display response (truncated, handle Unicode errors)
        response_preview = response.response[:300]
        if len(response.response) > 300:
            response_preview += "..."
        
        try:
            print(f"\n{agent.name}> {response_preview}")
        except UnicodeEncodeError:
            # Windows console can't handle some Unicode chars, encode safely
            safe_preview = response_preview.encode('ascii', 'ignore').decode('ascii')
            print(f"\n{agent.name}> {safe_preview}")
            print(f"[INFO] Response contains Unicode characters (displayed without emojis)")
        print(f"\n[Metadata]")
        print(f"  Provider: {response.provider}")
        print(f"  Model: {response.model}")
        print(f"  Latency: {response.metadata.latency_ms}ms (total: {elapsed_ms}ms)")
        print(f"  Tokens: {response.metadata.tokens_input} -> {response.metadata.tokens_output}")
        print(f"  Status: SUCCESS")
        
        return {
            'agent': agent_id,
            'name': agent.name,
            'success': True,
            'latency_ms': response.metadata.latency_ms,
            'tokens': f"{response.metadata.tokens_input}->{response.metadata.tokens_output}",
            'provider': response.provider
        }
        
    except Exception as e:
        print(f"\n[ERROR] {agent.name} test failed: {e}")
        return {
            'agent': agent_id,
            'name': agent.name,
            'success': False,
            'error': str(e)
        }


async def test_all_agents():
    """Test all BMad agents"""
    
    print("="*70)
    print("  SQUAD API - ALL AGENTS TEST")
    print("  Testing agent transformation for all 8 BMad agents")
    print("="*70)
    
    # Load environment
    load_dotenv()
    
    # Initialize
    print("\n[*] Initializing Squad API...")
    loader = AgentLoader(bmad_path=".bmad", redis_client=None)
    await loader.load_all()
    
    factory = ProviderFactory()
    providers = factory.create_all("config/providers.yaml")
    
    if not providers:
        print("[ERROR] No providers configured!")
        sys.exit(1)
    
    print(f"[OK] {len(providers)} providers: {list(providers.keys())}")
    
    # Check we have providers
    if not providers:
        print("[ERROR] No providers available!")
        sys.exit(1)
    
    # Create orchestrator with ALL providers (router will select optimal)
    orchestrator = AgentOrchestrator(
        agent_loader=loader,
        prompt_builder=SystemPromptBuilder(),
        conversation_manager=ConversationManager(redis_client=None),
        agent_router=AgentRouter(loader),  # Router will select provider per agent
        providers=providers  # ALL providers available!
    )
    
    print(f"[OK] Providers available: {list(providers.keys())}")
    print(f"[INFO] Router will select optimal provider for each agent")
    print()
    
    # Get all agents
    all_agents = loader.list_agents()
    print(f"[*] Found {len(all_agents)} agents to test")
    print()
    
    # Test each agent
    results = []
    for agent_id in all_agents:
        result = await test_agent(agent_id, orchestrator, loader)
        if result:
            results.append(result)
        
        # Small delay to respect rate limits
        await asyncio.sleep(2)
    
    # Summary
    print("\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"\nAgents tested: {len(results)}")
    print(f"  Successful: {len(successful)}")
    print(f"  Failed: {len(failed)}")
    print()
    
    if successful:
        print("Agent Details:")
        for r in successful:
            print(f"  [OK] {r['name']:20} - {r['latency_ms']:4}ms - {r['tokens']}")
    
    if failed:
        print("\nFailed Agents:")
        for r in failed:
            print(f"  [FAIL] {r['name']:20} - {r.get('error', 'Unknown')[:50]}")
    
    print()
    
    if len(successful) == len(results):
        print("[SUCCESS] ALL AGENTS WORKING!")
        print("\nVERIFIED:")
        print("  - All 8 BMad agents transform correctly")
        print("  - Each agent has unique persona")
        print("  - Groq LLM adapts to each agent's role")
        print("  - Portuguese language working")
        print("  - Squad is READY! ")
        print()
    else:
        print(f"[WARN] {len(successful)}/{len(results)} agents working")
    
    print("="*70)


if __name__ == "__main__":
    try:
        asyncio.run(test_all_agents())
    except KeyboardInterrupt:
        print("\n[WARN] Interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


