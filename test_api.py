#!/usr/bin/env python3
"""Test Squad API endpoints"""
import requests
import json

def test_endpoints():
    base_url = "http://localhost:8000"

    print("[TEST] Squad API Endpoint Validation\n")

    # Test 1: Health
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f" [200] GET /health")
        print(f"  Status: {response.json()['status']}\n")
    except Exception as e:
        print(f" [ERROR] /health - {e}\n")

    # Test 2: Agents
    try:
        response = requests.get(f"{base_url}/agents", timeout=5)
        print(f" [200] GET /agents")
        agents = response.json().get('agents', {})
        print(f"  Agents loaded: {len(agents)}")
        for name, config in agents.items():
            print(f"    - {name}: {config.get('role', 'unknown')}")
        print()
    except Exception as e:
        print(f" [ERROR] /agents - {e}\n")

    # Test 3: Providers
    try:
        response = requests.get(f"{base_url}/providers", timeout=5)
        print(f" [200] GET /providers")
        providers = response.json().get('providers', {})
        print(f"  Providers loaded: {len(providers)}")
        for name, config in providers.items():
            status = " enabled" if config.get('enabled') else " disabled"
            print(f"    - {name}: {config.get('model')} ({status})")
        print()
    except Exception as e:
        print(f" [ERROR] /providers - {e}\n")

    # Test 4: Task submission (simple echo task)
    try:
        task_data = {
            "agent": "mary",
            "task": "Respond with: API is working correctly",
            "provider_overrides": None
        }
        response = requests.post(f"{base_url}/task", json=task_data, timeout=30)
        print(f" [{response.status_code}] POST /task")
        if response.status_code == 200:
            result = response.json()
            print(f"  Task ID: {result.get('task_id')}")
            print(f"  Status: {result.get('status')}")
            print()
        else:
            print(f"  Error: {response.text}\n")
    except Exception as e:
        print(f" [ERROR] /task - {e}\n")

if __name__ == "__main__":
    test_endpoints()

