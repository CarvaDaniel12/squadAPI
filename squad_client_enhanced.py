"""
Enhanced Squad API Client - Easy Integration for Any Project
===========================================================

This enhanced client provides seamless integration with Squad API from any Python project.
It includes auto-discovery, connection pooling, async support, and better error handling.

Installation:
    pip install requests asyncio aiohttp

Usage:
    from squad_client_enhanced import SquadClient, SquadAsyncClient

    # Synchronous client
    squad = SquadClient()
    response = squad.ask("dev", "Create a Flask API")

    # Asynchronous client
    async with SquadAsyncClient() as squad:
        response = await squad.ask("dev", "Create a FastAPI endpoint")

Features:
    - Auto-discovery of Squad API
    - Connection pooling
    - Async/await support
    - Better error handling
    - Cost tracking
    - Agent health monitoring
"""

import json
import time
import asyncio
import aiohttp
import requests
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from enum import Enum


class AgentType(Enum):
    """Available agent types"""
    DEV = "dev"
    ANALYST = "analyst"
    ARCHITECT = "architect"
    REVIEWER = "reviewer"
    QA = "qa"
    PM = "pm"


@dataclass
class SquadResponse:
    """Structured response from Squad API"""
    success: bool
    response: str
    agent: str
    tokens_used: int = 0
    cost: float = 0.0
    conversation_id: Optional[str] = None
    error: Optional[str] = None


class SquadClient:
    """Enhanced Squad API Client with auto-discovery and connection pooling"""

    def __init__(self,
                 base_url: str = "http://localhost:8000",
                 timeout: int = 60,
                 max_retries: int = 3,
                 auto_discover: bool = True):
        """
        Initialize Squad Client

        Args:
            base_url: Squad API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            auto_discover: Automatically discover Squad API if not available
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries

        # Connection pool for better performance
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'SquadClient/2.0'
        })

        self._agent_health = {}

        if auto_discover:
            self._discover_api()

        self._validate_connection()

    def _discover_api(self):
        """Auto-discover Squad API if not at default location"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=2)
            if response.status_code == 200:
                print(f"✓ Found Squad API at {self.base_url}")
                return
        except:
            pass

        # Try alternative locations
        alternative_urls = [
            "http://127.0.0.1:8000",
            "http://localhost:8080",
            "http://127.0.0.1:8080"
        ]

        for url in alternative_urls:
            try:
                response = self.session.get(f"{url}/health", timeout=2)
                if response.status_code == 200:
                    print(f"✓ Discovered Squad API at {url}")
                    self.base_url = url
                    return
            except:
                continue

    def _validate_connection(self):
        """Validate connection to Squad API"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✓ Squad API connection validated")
                return True
        except Exception as e:
            print(f"⚠ Could not connect to Squad API: {e}")

        print(f"💡 To start Squad API:")
        print(f"   1. Navigate to your Squad API directory")
        print(f"   2. Run: activate_squad.bat")
        print(f"   3. Or manually: python src/main.py")
        return False

    def ask(self,
            agent: Union[str, AgentType],
            prompt: str,
            max_tokens: int = 2000,
            temperature: float = 0.7,
            conversation_id: Optional[str] = None,
            context: Optional[str] = None) -> SquadResponse:
        """
        Ask Squad API for help with a task

        Args:
            agent: Which agent to use
            prompt: What you want the agent to do
            max_tokens: Maximum response length
            temperature: Creativity level (0.0-1.0)
            conversation_id: Continue a conversation
            context: Additional context for the request

        Returns:
            SquadResponse object with structured data
        """
        if isinstance(agent, AgentType):
            agent = agent.value

        # Build payload
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        if conversation_id:
            payload["conversation_id"] = conversation_id

        if context:
            payload["context"] = context

        # Retry logic
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    f"{self.base_url}/v1/agents/{agent}",
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()

                data = response.json()

                return SquadResponse(
                    success=True,
                    response=data.get("response", ""),
                    agent=agent,
                    tokens_used=data.get("tokens_used", 0),
                    cost=data.get("cost", 0.0),
                    conversation_id=data.get("conversation_id")
                )

            except requests.exceptions.Timeout:
                last_error = f"Request timeout after {self.timeout}s"
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue

            except requests.exceptions.ConnectionError:
                last_error = "Connection error - Squad API may not be running"
                break

            except Exception as e:
                last_error = f"HTTP Error: {e}"
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue

        return SquadResponse(
            success=False,
            response="",
            agent=agent,
            error=last_error or "Unknown error"
        )

    def get_cost_report(self) -> Dict[str, Any]:
        """Get current cost statistics"""
        try:
            response = self.session.get(f"{self.base_url}/cost/stats", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def check_agent_health(self, agent: Union[str, AgentType]) -> bool:
        """Check if an agent is healthy and available"""
        if isinstance(agent, AgentType):
            agent = agent.value

        try:
            response = self.session.post(
                f"{self.base_url}/v1/agents/{agent}",
                json={"prompt": "health_check", "max_tokens": 10},
                timeout=10
            )
            is_healthy = response.status_code == 200
            self._agent_health[agent] = is_healthy
            return is_healthy
        except:
            self._agent_health[agent] = False
            return False

    def get_available_agents(self) -> List[str]:
        """Get list of available agents"""
        try:
            response = self.session.get(f"{self.base_url}/v1/agents", timeout=5)
            if response.status_code == 200:
                return response.json().get("agents", [])
        except:
            pass

        # Fallback to known agents
        return [agent.value for agent in AgentType]

    def batch_ask(self, requests_list: List[Dict[str, Any]]) -> List[SquadResponse]:
        """Process multiple requests in batch"""
        responses = []

        for request in requests_list:
            response = self.ask(
                agent=request["agent"],
                prompt=request["prompt"],
                **request.get("kwargs", {})
            )
            responses.append(response)

            # Small delay to avoid overwhelming the API
            time.sleep(0.1)

        return responses

    def close(self):
        """Close the client session"""
        self.session.close()


class SquadAsyncClient:
    """Asynchronous Squad API Client"""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 60):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={'Content-Type': 'application/json'}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def ask(self,
                  agent: Union[str, AgentType],
                  prompt: str,
                  max_tokens: int = 2000,
                  temperature: float = 0.7,
                  conversation_id: Optional[str] = None) -> SquadResponse:
        """Async version of ask method"""
        if isinstance(agent, AgentType):
            agent = agent.value

        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        if conversation_id:
            payload["conversation_id"] = conversation_id

        try:
            async with self.session.post(
                f"{self.base_url}/v1/agents/{agent}",
                json=payload
            ) as response:
                response.raise_for_status()
                data = await response.json()

                return SquadResponse(
                    success=True,
                    response=data.get("response", ""),
                    agent=agent,
                    tokens_used=data.get("tokens_used", 0),
                    cost=data.get("cost", 0.0),
                    conversation_id=data.get("conversation_id")
                )

        except Exception as e:
            return SquadResponse(
                success=False,
                response="",
                agent=agent,
                error=str(e)
            )

    async def batch_ask(self, requests_list: List[Dict[str, Any]]) -> List[SquadResponse]:
        """Process multiple requests concurrently"""
        tasks = []

        for request in requests_list:
            task = self.ask(
                agent=request["agent"],
                prompt=request["prompt"],
                **request.get("kwargs", {})
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                responses[i] = SquadResponse(
                    success=False,
                    response="",
                    agent=requests_list[i].get("agent", "unknown"),
                    error=str(response)
                )

        return responses


# Convenience functions for easy integration
def quick_ask(prompt: str, agent: str = "dev", **kwargs) -> str:
    """Quick one-liner for simple requests"""
    client = SquadClient()
    response = client.ask(agent, prompt, **kwargs)
    client.close()
    return response.response if response.success else f"Error: {response.error}"


def create_squad_integration():
    """Generate integration code for other projects"""
    integration_code = '''
# Squad API Integration Template
# Copy this code to your project

from squad_client_enhanced import SquadClient, AgentType

class YourProjectAI:
    def __init__(self):
        self.squad = SquadClient()

    def generate_code(self, requirement):
        """Generate code using dev agent"""
        return self.squad.ask(AgentType.DEV, requirement)

    def analyze_data(self, data_description):
        """Analyze data using analyst agent"""
        return self.squad.ask(AgentType.ANALYST, f"Analyze this data: {data_description}")

    def design_architecture(self, requirements):
        """Design system architecture using architect agent"""
        return self.squad.ask(AgentType.ARCHITECT, requirements)

    def close(self):
        self.squad.close()

# Usage example:
# ai = YourProjectAI()
# code = ai.generate_code("Create a user authentication system")
# print(code.response)
'''
    return integration_code


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Enhanced Squad API Client")
        print("Usage examples:")
        print("  python squad_client_enhanced.py ask dev 'Create a Flask API'")
        print("  python squad_client_enhanced.py agents")
        print("  python squad_client_enhanced.py cost")
        print("  python squad_client_enhanced.py integration")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "ask":
        if len(sys.argv) < 4:
            print("Usage: ask <agent> <prompt>")
            sys.exit(1)

        agent = sys.argv[2]
        prompt = " ".join(sys.argv[3:])

        client = SquadClient()
        response = client.ask(agent, prompt)
        client.close()

        if response.success:
            print(f"🤖 {agent.upper()} Agent Response:")
            print("=" * 50)
            print(response.response)
            print("=" * 50)
            print(f"💰 Cost: ${response.cost:.4f}")
            print(f"🔢 Tokens: {response.tokens_used}")
        else:
            print(f"❌ Error: {response.error}")

    elif command == "agents":
        client = SquadClient()
        agents = client.get_available_agents()
        client.close()
        print("Available Agents:")
        for agent in agents:
            print(f"  • {agent}")

    elif command == "cost":
        client = SquadClient()
        cost_report = client.get_cost_report()
        client.close()
        print("Cost Report:")
        print(json.dumps(cost_report, indent=2))

    elif command == "integration":
        print(create_squad_integration())

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
