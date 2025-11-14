#!/usr/bin/env python
"""
Chat with Mary (and other BMad agents)

Interactive CLI to test agent transformation via real LLM providers.
"""

import asyncio
import os
import sys
import argparse
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
from src.agents.fallback import FallbackExecutor
from src.providers.factory import ProviderFactory
from src.rate_limit.combined import CombinedRateLimiter
from src.rate_limit.semaphore import GlobalSemaphore
from src.models.request import AgentExecutionRequest


# Color codes
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_banner():
    """Print welcome banner"""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}

                                                          
          SQUAD API - Chat with Mary & Team            
                                                          
     Transform external LLMs into BMad agents!          
                                                          

{Colors.RESET}
"""
    print(banner)


async def initialize_squad(agent_id: str = "analyst") -> tuple:
    """Initialize Squad API components"""
    print(f"{Colors.YELLOW} Initializing Squad API...{Colors.RESET}")
    
    # Load environment
    load_dotenv()
    
    # 1. Load agents
    print(f"  {Colors.BLUE}{Colors.RESET} Loading agents from .bmad/...")
    loader = AgentLoader(bmad_path=".bmad", redis_client=None)
    await loader.load_all()
    available_agents = loader.list_agents()
    print(f"    {Colors.GREEN}{Colors.RESET} {len(available_agents)} agents loaded")
    
    # 2. Load providers
    print(f"  {Colors.BLUE}{Colors.RESET} Loading LLM providers...")
    factory = ProviderFactory()
    providers = factory.create_all("config/providers.yaml")
    print(f"    {Colors.GREEN}{Colors.RESET} {len(providers)} providers configured: {list(providers.keys())}")
    
    if not providers:
        print_error(" No providers configured! Set API keys in .env")
        print(f"    See: docs/API-KEYS-SETUP.md")
        sys.exit(1)
    
    # 3. Setup rate limiting
    print(f"  {Colors.BLUE}{Colors.RESET} Setting up rate limiting...")
    rate_limiter = CombinedRateLimiter(redis_client=None)
    for provider_name in providers.keys():
        from src.config.rate_limits import get_rate_limit_config
        config_loader = get_rate_limit_config()
        provider_config = config_loader.get_provider_config(provider_name)
        if provider_config:
            rate_limiter.register_provider(provider_name, provider_config)
    print(f"    {Colors.GREEN}{Colors.RESET} Rate limiting configured")
    
    # 4. Setup semaphore
    semaphore = GlobalSemaphore(max_concurrent=12)
    
    # 5. Setup fallback
    print(f"  {Colors.BLUE}{Colors.RESET} Setting up fallback chains...")
    fallback = FallbackExecutor(providers, fallback_chains={})
    print(f"    {Colors.GREEN}{Colors.RESET} Fallback chains ready")
    
    # 6. Create orchestrator
    orchestrator = AgentOrchestrator(
        agent_loader=loader,
        prompt_builder=SystemPromptBuilder(),
        conversation_manager=ConversationManager(redis_client=None),
        agent_router=AgentRouter(loader),
        rate_limiter=rate_limiter,
        global_semaphore=semaphore,
        provider_stub=None  # Use real providers!
    )
    
    print(f"\n{Colors.GREEN} Squad API initialized!{Colors.RESET}\n")
    
    return orchestrator, loader, fallback, providers


async def chat_session(agent_id: str, user_name: str = "Dani"):
    """Run interactive chat session"""
    print_banner()
    
    # Initialize
    orchestrator, loader, fallback, providers = await initialize_squad(agent_id)
    
    # Get agent info
    agent = await loader.get_agent(agent_id)
    if not agent:
        print_error(f"Agent '{agent_id}' not found!")
        print(f"Available agents: {loader.list_agents()}")
        sys.exit(1)
    
    # Welcome message
    print(f"{Colors.MAGENTA}{Colors.BOLD}You are chatting with: {agent.title}{Colors.RESET}")
    print(f"{Colors.CYAN}Agent: {agent.name}{Colors.RESET}")
    print(f"{Colors.CYAN}Persona: {agent.persona.summary[:100]}...{Colors.RESET}")
    print(f"{Colors.CYAN}Providers: {list(providers.keys())}{Colors.RESET}")
    print()
    print(f"{Colors.YELLOW}Commands:{Colors.RESET}")
    print(f"  /help    - Show help")
    print(f"  /agents  - List all agents")
    print(f"  /switch  - Switch to different agent")
    print(f"  /stats   - Show conversation stats")
    print(f"  /quit    - Exit chat")
    print()
    print(f"{Colors.GREEN}Start chatting! (Press Ctrl+C or type '/quit' to exit){Colors.RESET}")
    print("" * 60)
    print()
    
    # Chat loop
    user_id = f"cli-{user_name.lower()}"
    message_count = 0
    
    while True:
        try:
            # Get user input
            user_input = input(f"{Colors.BOLD}{user_name}>{Colors.RESET} ")
            
            if not user_input.strip():
                continue
            
            # Handle commands
            if user_input.startswith('/'):
                command = user_input.lower().strip()
                
                if command == '/quit' or command == '/exit':
                    print(f"\n{Colors.YELLOW}Goodbye! {Colors.RESET}\n")
                    break
                
                elif command == '/help':
                    print(f"\n{Colors.CYAN}Available commands:{Colors.RESET}")
                    print("  /help    - Show this help")
                    print("  /agents  - List all available agents")
                    print("  /switch  - Switch to different agent")
                    print("  /stats   - Show conversation statistics")
                    print("  /quit    - Exit chat\n")
                    continue
                
                elif command == '/agents':
                    agents = loader.list_agents()
                    print(f"\n{Colors.CYAN}Available agents:{Colors.RESET}")
                    for ag in agents:
                        print(f"  - {ag}")
                    print()
                    continue
                
                elif command == '/stats':
                    print(f"\n{Colors.CYAN}Conversation Stats:{Colors.RESET}")
                    print(f"  Messages sent: {message_count}")
                    print(f"  Current agent: {agent_id}")
                    print(f"  User ID: {user_id}")
                    print()
                    continue
                
                elif command == '/switch':
                    print(f"\n{Colors.YELLOW}Agent switching not yet implemented{Colors.RESET}")
                    print(f"Restart script with --agent <agent_name>\n")
                    continue
                
                else:
                    print(f"{Colors.RED}Unknown command: {command}{Colors.RESET}")
                    print(f"Type /help for available commands\n")
                    continue
            
            # Execute agent
            print(f"\n{Colors.BLUE} {agent.name} is thinking...{Colors.RESET}")
            
            request = AgentExecutionRequest(
                agent=agent_id,
                task=user_input,
                user_id=user_id
            )
            
            start = time.time()
            response = await orchestrator.execute(request)
            elapsed_ms = int((time.time() - start) * 1000)
            
            # Display response
            print(f"\n{Colors.MAGENTA}{Colors.BOLD}{agent.name}>{Colors.RESET} {response.response}")
            print()
            print(f"{Colors.CYAN}[{response.provider}/{response.model}  {elapsed_ms}ms  {response.metadata.tokens_input}{response.metadata.tokens_output} tokens]{Colors.RESET}")
            print("" * 60)
            print()
            
            message_count += 1
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Goodbye! {Colors.RESET}\n")
            break
        
        except Exception as e:
            print(f"\n{Colors.RED}Error: {e}{Colors.RESET}\n")
            continue


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Chat with BMad agents via Squad API",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--agent',
        type=str,
        default='analyst',
        help='Agent to chat with (default: analyst)'
    )
    
    parser.add_argument(
        '--user',
        type=str,
        default='Dani',
        help='Your name (default: Dani)'
    )
    
    args = parser.parse_args()
    
    # Run chat session
    try:
        asyncio.run(chat_session(args.agent, args.user))
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()


