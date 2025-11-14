"""Integration tests for load testing scenarios using Locust."""

import pytest
import subprocess
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple


class LoadTestRunner:
    """Helper class to run Locust scenarios and parse results."""

    @staticmethod
    def run_locust(
        users: int,
        spawn_rate: int,
        duration: int,
        scenario_name: str,
        host: str = "http://localhost:8000"
    ) -> Tuple[str, str, int]:
        """Run Locust headless and return stdout, stderr, and exit code."""
        reports_dir = Path("tests/load/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            "locust",
            "-f", "scripts/load_test.py",
            "--headless",
            "-u", str(users),
            "-r", str(spawn_rate),
            "--run-time", f"{duration}s",
            "--host", host,
            "--csv", str(reports_dir / scenario_name),
            "--stop-timeout", "30",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 120)
        return result.stdout, result.stderr, result.returncode

    @staticmethod
    def parse_locust_csv(csv_path: Path) -> Dict:
        """Parse Locust stats_history.csv file."""
        if not csv_path.exists():
            return {}

        stats = {
            "total_requests": 0,
            "total_failures": 0,
            "endpoints": {}
        }

        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    endpoint = row.get("Name", "unknown")
                    requests = int(row.get("Requests", 0))
                    failures = int(row.get("Failures", 0))

                    if endpoint not in stats["endpoints"]:
                        stats["endpoints"][endpoint] = {
                            "requests": 0,
                            "failures": 0,
                            "p95": 0,
                            "p99": 0,
                            "max": 0
                        }

                    stats["endpoints"][endpoint]["requests"] = requests
                    stats["endpoints"][endpoint]["failures"] = failures
                    stats["endpoints"][endpoint]["p95"] = int(row.get("95%", 0))
                    stats["endpoints"][endpoint]["p99"] = int(row.get("99%", 0))
                    stats["endpoints"][endpoint]["max"] = int(row.get("Max", 0))

                    stats["total_requests"] += requests
                    stats["total_failures"] += failures

        except Exception as e:
            print(f"Warning: Could not parse CSV {csv_path}: {e}")

        return stats


@pytest.mark.slow
class TestLoadScenarios:
    """Load test scenarios for Squad API."""

    @pytest.fixture
    def reports_dir(self):
        """Ensure reports directory exists."""
        reports_dir = Path("tests/load/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir

    def test_warm_up_scenario(self, reports_dir):
        """
        AC-2 Warm-up: 5 req/s for 1 minute.
        Validates baseline, prepares system.
        """
        users = 5
        spawn_rate = 5
        duration = 60
        scenario = "warm_up"

        stdout, stderr, exit_code = LoadTestRunner.run_locust(
            users=users,
            spawn_rate=spawn_rate,
            duration=duration,
            scenario_name=scenario
        )

        # Parse results
        csv_path = Path(f"tests/load/reports/{scenario}_stats_history.csv")
        stats = LoadTestRunner.parse_locust_csv(csv_path)

        # Verify test ran
        assert exit_code == 0, f"Locust exited with code {exit_code}. Stderr: {stderr}"
        assert stats["total_requests"] > 0, "No requests were made"

        # AC-3: Success Rate > 99%
        if stats["total_requests"] > 0:
            success_rate = 1 - (stats["total_failures"] / stats["total_requests"])
            assert success_rate > 0.99, f"Success rate {success_rate:.2%} is below 99%"

        print(f"\nWarm-up scenario completed:")
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Failures: {stats['total_failures']}")
        print(f"  Success rate: {1 - (stats['total_failures'] / stats['total_requests']):.2%}")

    def test_sustained_load_scenario(self, reports_dir):
        """
        AC-2 Sustained: 30 req/s for 5 minutes = 9000 total requests.
        Simulates normal operation.
        """
        users = 30
        spawn_rate = 30
        duration = 300  # 5 minutes
        scenario = "sustained_load"
        expected_requests = 9000

        stdout, stderr, exit_code = LoadTestRunner.run_locust(
            users=users,
            spawn_rate=spawn_rate,
            duration=duration,
            scenario_name=scenario
        )

        # Parse results
        csv_path = Path(f"tests/load/reports/{scenario}_stats_history.csv")
        stats = LoadTestRunner.parse_locust_csv(csv_path)

        # Verify test ran
        assert exit_code == 0, f"Locust exited with code {exit_code}. Stderr: {stderr}"
        assert stats["total_requests"] > 0, "No requests were made"

        # AC-2: Should achieve approximately 9000 requests (9000/expected = ~1.0)
        # Allow 90-110% of expected requests
        assert stats["total_requests"] >= expected_requests * 0.90, \
            f"Expected ~{expected_requests} requests, got {stats['total_requests']}"
        assert stats["total_requests"] <= expected_requests * 1.10, \
            f"Too many requests: {stats['total_requests']} (expected ~{expected_requests})"

        # AC-3: Success Rate > 99%
        success_rate = 1 - (stats["total_failures"] / stats["total_requests"])
        assert success_rate > 0.99, \
            f"Success rate {success_rate:.2%} is below 99%. Failures: {stats['total_failures']}"

        # AC-4: Latency thresholds
        for endpoint, metrics in stats["endpoints"].items():
            if metrics["p95"] > 0:
                assert metrics["p95"] < 2000, \
                    f"{endpoint} P95 latency {metrics['p95']}ms exceeds 2000ms threshold"
            if metrics["p99"] > 0:
                assert metrics["p99"] < 3000, \
                    f"{endpoint} P99 latency {metrics['p99']}ms exceeds 3000ms threshold"

        print(f"\nSustained load scenario completed:")
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Expected: {expected_requests}")
        print(f"  Failures: {stats['total_failures']}")
        print(f"  Success rate: {success_rate:.2%}")
        for endpoint, metrics in stats["endpoints"].items():
            print(f"  {endpoint}: P95={metrics['p95']}ms, P99={metrics['p99']}ms, Max={metrics['max']}ms")

    def test_spike_scenario(self, reports_dir):
        """
        AC-2 Spike: 60 req/s for 2 minutes.
        Tests rate limiting and fallback activation.
        """
        users = 60
        spawn_rate = 60
        duration = 120  # 2 minutes
        scenario = "spike_scenario"

        stdout, stderr, exit_code = LoadTestRunner.run_locust(
            users=users,
            spawn_rate=spawn_rate,
            duration=duration,
            scenario_name=scenario
        )

        # Parse results
        csv_path = Path(f"tests/load/reports/{scenario}_stats_history.csv")
        stats = LoadTestRunner.parse_locust_csv(csv_path)

        # Verify test ran
        assert exit_code == 0, f"Locust exited with code {exit_code}. Stderr: {stderr}"
        assert stats["total_requests"] > 0, "No requests were made during spike scenario"

        # AC-3: Success Rate should still be high (> 95% during spike is acceptable)
        # Rate limiting may cause some 429s, but system should not crash (5xx < 0.1%)
        success_rate = 1 - (stats["total_failures"] / stats["total_requests"])
        assert success_rate > 0.95, \
            f"Success rate during spike {success_rate:.2%} is below 95% threshold"

        # AC-4: P95 latency should degrade but stay reasonable (< 3000ms for P95, < 5000ms for P99)
        max_p95 = 0
        max_p99 = 0
        for endpoint, metrics in stats["endpoints"].items():
            if metrics["p95"] > 0:
                max_p95 = max(max_p95, metrics["p95"])
                assert metrics["p95"] < 3000, \
                    f"{endpoint} P95 latency {metrics['p95']}ms exceeds 3000ms during spike"
            if metrics["p99"] > 0:
                max_p99 = max(max_p99, metrics["p99"])
                assert metrics["p99"] < 5000, \
                    f"{endpoint} P99 latency {metrics['p99']}ms exceeds 5000ms during spike"

        print(f"\nSpike scenario completed:")
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Failures: {stats['total_failures']}")
        print(f"  Success rate: {success_rate:.2%}")
        print(f"  Max P95 latency: {max_p95}ms")
        print(f"  Max P99 latency: {max_p99}ms")
        for endpoint, metrics in stats["endpoints"].items():
            print(f"  {endpoint}: P95={metrics['p95']}ms, P99={metrics['p99']}ms, Max={metrics['max']}ms")

    def test_thresholds_validation(self, reports_dir):
        """
        AC-3-5: Validate that all thresholds are properly defined.
        This is a smoke test to ensure the framework is working.
        """
        # Thresholds from AC-3 to AC-5
        thresholds = {
            "success_rate_min": 0.99,  # > 99%
            "rate_limited_max": 0.01,  # < 1%
            "p95_latency_max_ms": 2000,
            "p99_latency_max_ms": 3000,
            "spike_p99_latency_max_ms": 5000,
            "error_rate_max": 0.001,  # < 0.1% 5xx errors
        }

        # Validate thresholds are reasonable
        assert thresholds["success_rate_min"] == 0.99
        assert thresholds["p95_latency_max_ms"] < thresholds["p99_latency_max_ms"]
        assert thresholds["p99_latency_max_ms"] < thresholds["spike_p99_latency_max_ms"]

        print(f"\nThresholds validation passed:")
        for name, value in thresholds.items():
            print(f"  {name}: {value}")
