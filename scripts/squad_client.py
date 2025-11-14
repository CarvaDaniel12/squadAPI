"""
Squad API Client - Use your AI Squad from any project

Installation (one-time):
    pip install requests

Usage in any project:
    from squad_client import Squad

    squad = Squad()
    response = squad.ask("dev", "Create a Flask API with authentication")
    print(response)

Or use CLI:
    python squad_client.py dev "Create a REST API"
"""

import sys
import json
from typing import Optional, Dict, Any
import requests


class Squad:
    """Client to interact with Squad API from any project."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize Squad client.

        Args:
            base_url: URL where Squad API is running (default: localhost:8000)
        """
        self.base_url = base_url.rstrip('/')
        self._check_connection()

    def _check_connection(self):
        """Check if Squad API is running."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            if response.status_code != 200:
                print(f"⚠️  Squad API returned status {response.status_code}")
                print("💡 Make sure Squad API is running: python src/main.py")
        except requests.exceptions.ConnectionError:
            print("❌ Squad API is not running!")
            print("💡 Start it with: cd 'C:\\Users\\User\\Desktop\\squad api' && python src/main.py")
            sys.exit(1)
        except Exception as exc:
            print(f"⚠️  Error connecting to Squad API: {exc}")

    def ask(
        self,
        agent: str,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        conversation_id: Optional[str] = None
    ) -> str:
        """Ask your AI squad to help with a task.

        Args:
            agent: Which agent to use (dev, analyst, architect, reviewer, qa, pm)
            prompt: What you want the agent to do
            max_tokens: Maximum response length (default: 2000)
            temperature: Creativity 0.0-1.0 (default: 0.7)
            conversation_id: Continue a conversation (optional)

        Returns:
            The agent's response as string

        Example:
            squad = Squad()
            code = squad.ask("dev", "Create a Python function to read CSV files")
            print(code)
        """
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        if conversation_id:
            payload["conversation_id"] = conversation_id

        try:
            response = requests.post(
                f"{self.base_url}/v1/agents/{agent}",
                json=payload,
                timeout=60
            )
            response.raise_for_status()

            data = response.json()
            return data.get("response", "")

        except requests.exceptions.Timeout:
            return "❌ Request timeout (60s). Task might be too complex."
        except requests.exceptions.HTTPError as exc:
            return f"❌ HTTP Error: {exc}"
        except Exception as exc:
            return f"❌ Error: {exc}"

    def cost_report(self) -> Dict[str, Any]:
        """Get current cost statistics.

        Returns:
            Dictionary with cost breakdown
        """
        try:
            response = requests.get(f"{self.base_url}/cost/stats", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            return {"error": str(exc)}

    def list_agents(self) -> list:
        """Get list of available agents.

        Returns:
            List of agent IDs
        """
        return ["analyst", "dev", "architect", "reviewer", "qa", "pm"]


def main():
    """CLI interface for Squad client."""
    if len(sys.argv) < 3:
        print("Usage: python squad_client.py <agent> <prompt>")
        print("\nAvailable agents:")
        print("  dev        - Code generation & debugging")
        print("  analyst    - Research & data analysis")
        print("  architect  - System design & architecture")
        print("  reviewer   - Code review & quality")
        print("  qa         - Test design & validation")
        print("  pm         - Planning & coordination")
        print("\nExample:")
        print('  python squad_client.py dev "Create a FastAPI endpoint for user login"')
        sys.exit(1)

    agent = sys.argv[1]
    prompt = " ".join(sys.argv[2:])

    print(f"🤖 Asking {agent} agent...")
    print(f"📝 Task: {prompt}\n")

    squad = Squad()
    response = squad.ask(agent, prompt)

    print("=" * 80)
    print(response)
    print("=" * 80)

    # Show cost
    print("\n💰 Cost Report:")
    stats = squad.cost_report()
    if "error" not in stats:
        print(f"   Total cost today: ${stats.get('total_cost', 0):.4f}")
        print(f"   FREE tier usage: {stats.get('free_percentage', 0)}%")


if __name__ == "__main__":
    main()
