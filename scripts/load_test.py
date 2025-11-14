"""Load testing script using Locust framework."""

import random
from locust import HttpUser, task, between, events
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class LoadMetrics:
    """Track custom metrics during load test."""
    total_429s: int = 0
    total_503s: int = 0
    fallback_count: int = 0
    provider_stats: Dict = field(default_factory=dict)


class SquadApiUser(HttpUser):
    """Simulates a user interacting with Squad API."""

    # Think time between tasks: 1-3 seconds
    wait_time = between(1, 3)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metrics = LoadMetrics()
        self.agents = ["financial_advisor", "travel_planner", "tech_support", "legal_expert"]
        self.prompts = [
            "What's the best investment strategy?",
            "Plan a trip to Tokyo for 5 days",
            "How do I fix my WiFi connection?",
            "Calculate ROI for my portfolio",
            "Recommend 5-star hotels in Paris",
            "What are my legal rights as a tenant?",
            "Create a retirement plan for me",
            "Best credit cards for travel rewards?",
            "How to optimize database queries?",
            "What's the weather tomorrow?"
        ]

    @task(80)
    def task_chat(self):
        """80% of requests: POST /agents/chat"""
        payload = {
            "user_id": f"user_{random.randint(1, 1000)}",
            "agent_id": random.choice(self.agents),
            "task": random.choice(self.prompts),
            "conversation_history": []
        }

        with self.client.post(
            "/agents/chat",
            json=payload,
            catch_response=True,
            timeout=30
        ) as response:
            if response.status_code == 429:
                self.metrics.total_429s += 1
                response.success()  # 429 is expected during load testing
            elif response.status_code == 503:
                self.metrics.total_503s += 1
                response.success()  # 503 when fallback is triggered
            elif response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Unexpected status {response.status_code}: {response.text[:100]}")

    @task(15)
    def task_health(self):
        """15% of requests: GET /health"""
        with self.client.get(
            "/health",
            catch_response=True,
            timeout=10
        ) as response:
            if response.status_code in [200, 503]:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(5)
    def task_metrics(self):
        """5% of requests: GET /metrics"""
        with self.client.get(
            "/metrics",
            catch_response=True,
            timeout=10
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Metrics endpoint failed: {response.status_code}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print summary statistics when test completes."""
    print("\n" + "="*60)
    print("LOAD TEST SUMMARY")
    print("="*60)

    # Get aggregated stats
    stats = environment.stats
    total = stats.total.num_requests
    failed = stats.total.num_failures

    print(f"Total Requests: {total}")
    print(f"Failed Requests: {failed}")
    print(f"Success Rate: {((total - failed) / total * 100):.2f}%" if total > 0 else "N/A")
    print(f"429 Rate Limited: {getattr(environment, 'total_429s', 0)}")
    print(f"503 Service Degraded: {getattr(environment, 'total_503s', 0)}")
    print(f"Response Time Median: {stats.total.median_response_time}ms")
    print(f"Response Time P95: {stats.total.get_response_time_percentile(0.95)}ms")
    print(f"Response Time P99: {stats.total.get_response_time_percentile(0.99)}ms")
    print(f"Max Response Time: {stats.total.max_response_time}ms")
    print("="*60)


if __name__ == "__main__":
    import sys

    # Default configuration
    users = 10
    spawn_rate = 10
    duration = 60
    host = "http://localhost:8000"

    # Parse command line arguments
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--users":
            users = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--spawn-rate":
            spawn_rate = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--duration":
            duration = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--host":
            host = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    print(f"Starting load test:")
    print(f"  Users: {users}")
    print(f"  Spawn rate: {spawn_rate} users/sec")
    print(f"  Duration: {duration} seconds")
    print(f"  Host: {host}")
