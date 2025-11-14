#!/usr/bin/env python3
"""
Squad API Client - Example Integration Script
Demonstrates how to use Squad API from ANY project/folder

This file can be copied to ANY project and used independently
"""

import requests
import json
import sys
from typing import Optional, Dict, Any

class SquadAPI:
    """Simple Squad API client for integration with any project"""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "SquadAPI-Client/1.0"
        }

    def _make_request(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a request to the Squad API"""
        try:
            if data is None:
                response = requests.get(f"{self.base_url}/{endpoint}", headers=self.headers, timeout=self.timeout)
            else:
                response = requests.post(
                    f"{self.base_url}/{endpoint}",
                    json=data,
                    headers=self.headers,
                    timeout=self.timeout
                )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"Failed to connect to Squad API at {self.base_url}"
            }

    def ask(self, agent: str, prompt: str, conversation_id: str = None) -> str:
        """Ask a specific agent for help"""
        data = {
            "prompt": prompt
        }
        if conversation_id:
            data["conversation_id"] = conversation_id

        result = self._make_request(f"v1/agents/{agent}", data)

        if result.get("response"):
            return result.get("response", "No response received")
        else:
            return f"Error: {result.get('detail', 'Unknown error')}"

    def health_check(self) -> Dict[str, Any]:
        """Check if Squad API is healthy and running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "api_running": True,
                    "message": "Squad API is running and ready"
                }
            else:
                return {
                    "status": "error",
                    "api_running": False,
                    "message": f"API returned status code: {response.status_code}"
                }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "api_running": False,
                "message": f"Cannot connect to Squad API: {str(e)}"
            }

def demo_usage():
    """Demonstrate how to use Squad API from any project"""

    print("🚀 Squad API Integration Demo")
    print("=" * 50)

    # Initialize client (works from ANY folder)
    squad = SquadAPI()

    # Check if Squad API is running
    print("1. Checking Squad API status...")
    health = squad.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Message: {health['message']}")

    if not health['api_running']:
        print("\n❌ Squad API is not running!")
        print("   To start it, go to your Squad API folder and run:")
        print("   activate_squad_complete.bat")
        return

    print("\n2. Testing different agents...")

    # Test dev agent
    print("\n🔧 Testing DEV agent...")
    response = squad.ask("dev", "Write a simple Python function to calculate factorial")
    print(f"   Response: {response[:100]}...")

    # Test analyst agent
    print("\n📊 Testing ANALYST agent...")
    response = squad.ask("analyst", "Explain what makes a good API design")
    print(f"   Response: {response[:100]}...")

    # Test architect agent
    print("\n🏗️  Testing ARCHITECT agent...")
    response = squad.ask("architect", "What are the key components of a microservices architecture?")
    print(f"   Response: {response[:100]}...")

    print("\n✅ Integration demo completed!")

def main():
    """Main function - can be called from any project"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        agent = sys.argv[2] if len(sys.argv) > 2 else "dev"
        prompt = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else "Hello from integration test"

        squad = SquadAPI()

        if command == "ask":
            response = squad.ask(agent, prompt)
            print(response)
        elif command == "health":
            health = squad.health_check()
            print(json.dumps(health, indent=2))
        else:
            print("Usage: python squad_integration.py [ask|health] [agent] [prompt]")
            print("Example: python squad_integration.py ask dev 'Create a hello world function'")
    else:
        demo_usage()

if __name__ == "__main__":
    main()
