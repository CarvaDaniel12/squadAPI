#!/usr/bin/env python3
"""
Test Squad API directly to check if LLMs are working
"""
import requests
import json

def test_api():
    base_url = "http://localhost:8000"

    # Test health
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

    # Test agents list
    print("\nTesting agents list...")
    try:
        response = requests.get(f"{base_url}/v1/agents")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {data['count']} agents:")
            for agent in data['agents'][:3]:  # Show first 3
                print(f"  - {agent['id']}: {agent['name']}")
        else:
            print(f"Agents list failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"Agents list failed: {e}")
        return False

    # Test dev agent
    print("\nTesting dev agent...")
    try:
        payload = {
            "prompt": "Write a simple Python function to calculate fibonacci numbers"
        }
        response = requests.post(
            f"{base_url}/v1/agents/dev",
            json=payload,
            timeout=60
        )

        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Provider used: {data.get('provider', 'unknown')}")
            print(f"Model used: {data.get('model', 'unknown')}")
            print(f"Response length: {len(data.get('response', ''))} characters")
            print("\n--- RESPONSE PREVIEW ---")
            print(data.get('response', '')[:500] + "..." if len(data.get('response', '')) > 500 else data.get('response', ''))
            print("--- END PREVIEW ---")
            return True
        else:
            print(f"API call failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False

    except Exception as e:
        print(f"API call failed: {e}")
        return False

if __name__ == "__main__":
    success = test_api()
    if success:
        print("\n✅ API Test PASSED - LLMs are working!")
    else:
        print("\n❌ API Test FAILED - LLMs are not working properly")
