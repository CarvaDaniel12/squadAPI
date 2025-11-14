# Story 9.6: Load Testing com Locust

**Epic:** 9 - Production Readiness
**Story:** 9.6 - Load Testing com Locust
**Priority:** High
**Points:** 8
**Status:** Drafting

---

## Overview

Implementar testes de carga com Locust para validar comportamento da API Squad em cenários de alta concorrência, garantindo que rate limiting, fallback, e providers comportam-se corretamente sob stress. Testes executam 3 cenários: warm-up, sustained load, e spike detection.

---

## Acceptance Criteria (AC)

### AC-1: Locust Framework Integration
- [ ] `scripts/load_test.py` implementado com Locust User class
- [ ] Comportamentos: `task_chat`, `task_health`, `task_metrics` (80% chat, 15% health, 5% metrics)
- [ ] Suporta configuração via CLI: `--users`, `--spawn-rate`, `--duration`, `--host`
- [ ] Integração com local Docker Compose stack (redis, postgres, providers mock/real)

### AC-2: Three Load Test Scenarios
- [ ] **Warm-up Scenario:** 5 req/s por 1 minuto, valida baseline, prepara sistema
- [ ] **Sustained Load Scenario:** 30 req/s por 5 minutos = 9000 total requests, simula tráfego normal
- [ ] **Spike Scenario:** 60 req/s por 2 minutos, detecta degradação graceful (rate limiting, fallback ativam)

### AC-3: Success & Health Metrics
- [ ] Overall success rate **> 99%** (máximo 0.7% failures)
- [ ] 429 Rate Limited responses **< 1%** do total (rate limiting ativo mas permitindo fluxo)
- [ ] HTTP 5xx errors **< 0.1%** (nenhuma crash, fallback mantém sistema up)
- [ ] Response time P95 **< 2000ms** (normal operation)
- [ ] Response time P99 **< 3000ms** (spikes absorvidos)

### AC-4: Latency Distribution
- [ ] Capturar percentis: P50, P75, P90, P95, P99, P99.9, max
- [ ] Max latency durante spike < 5000ms (sistema responde, não trava)
- [ ] Latência não degrada > 2x durante spike (fallback + rate limiting funcionam)

### AC-5: Provider Metrics During Load
- [ ] Rate limit (RPM) tracking por provider: groq, gemini, openrouter, cerebras
- [ ] 429 spike detection: monitora `last_429_time` via health check
- [ ] Fallback activation: conta quantas vezes fallback foi acionado
- [ ] Provider response times: latência média por provider

### AC-6: Rate Limiter Behavior
- [ ] Token bucket refill rate respeitado (não over-consume quota)
- [ ] Sliding window não permite burst > RPM limit
- [ ] Rate limiter backpressure: clientes aguardam gracefully em 429, não crasha
- [ ] Auto-throttle reduz concorrência quando 429 é detectado

### AC-7: Test Execution & Reporting
- [ ] `pytest` runner: `pytest tests/load/test_load_scenarios.py -v`
- [ ] Locust headless execution via script: `python scripts/load_test.py --scenario sustained`
- [ ] HTML report gerado: `locust_report_<timestamp>.html`
- [ ] JSON metrics exportado: `load_test_metrics_<timestamp>.json`
- [ ] Summary printed na CLI com success rate, latencies, 429 count, provider stats

### AC-8: CI/CD Integration (Optional for sprint)
- [ ] Load tests executáveis em CI environment (GitHub Actions)
- [ ] Thresholds configurable via env vars para diferentes stages (dev: 50 users, staging: 500 users, prod: 1000 users)
- [ ] Fail-fast se success rate < 99% ou P95 > 3000ms

---

## Technical Design

### 1. Locust User Class

```python
# scripts/load_test.py

from locust import HttpUser, task, between, events
import random
from dataclasses import dataclass

@dataclass
class LoadMetrics:
    total_429s: int = 0
    fallback_count: int = 0
    provider_stats: dict = field(default_factory=dict)

class SquadApiUser(HttpUser):
    """Simulates a user interacting with Squad API."""

    wait_time = between(1, 3)  # Think time: 1-3 seconds between requests

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metrics = LoadMetrics()

    @task(80)
    def task_chat(self):
        """80% of requests: POST /agents/chat"""
        payload = {
            "user_id": f"user_{random.randint(1, 100)}",
            "agent_id": random.choice(["financial_advisor", "travel_planner", "tech_support"]),
            "task": random.choice([
                "What's the best investment strategy?",
                "Plan a trip to Tokyo",
                "How do I fix my WiFi?",
                "Calculate ROI for my portfolio",
                "Recommend hotels in Paris"
            ]),
            "conversation_history": []
        }

        with self.client.post(
            "/agents/chat",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 429:
                self.metrics.total_429s += 1
            elif response.status_code == 503:
                # Fallback was activated
                self.metrics.fallback_count += 1
            elif response.status_code not in [200, 201]:
                response.failure(f"Unexpected status {response.status_code}")

    @task(15)
    def task_health(self):
        """15% of requests: GET /health"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code not in [200, 503]:
                response.failure(f"Health check failed: {response.status_code}")

    @task(5)
    def task_metrics(self):
        """5% of requests: GET /metrics"""
        with self.client.get("/metrics", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Metrics endpoint failed: {response.status_code}")
```

### 2. Load Test Scenarios

```python
# tests/load/test_load_scenarios.py

import pytest
import subprocess
import json
import re
from pathlib import Path
from datetime import datetime

class TestLoadScenarios:
    """Pytest-based load test scenarios using Locust."""

    @pytest.fixture
    def locust_report_dir(self):
        """Create report directory."""
        reports_dir = Path("tests/load/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir

    def run_locust(self, users, spawn_rate, duration, scenario_name, host="http://localhost:8000"):
        """Helper to run Locust headless."""
        cmd = [
            "locust",
            "-f", "scripts/load_test.py",
            "-u", str(users),
            "-r", str(spawn_rate),
            "--run-time", f"{duration}s",
            "--headless",
            "--host", host,
            f"--csv=tests/load/reports/{scenario_name}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout, result.stderr

    def parse_locust_output(self, stdout, stderr):
        """Parse Locust summary from output."""
        metrics = {
            "total_requests": None,
            "failed_requests": None,
            "avg_response_time": None,
            "p95_response_time": None,
            "p99_response_time": None
        }

        # Extract from stdout/stderr regex patterns
        for line in (stdout + stderr).split("\n"):
            if "Type\tName\tRequests" in line:
                # CSV header, parse following lines
                pass

        return metrics

    @pytest.mark.slow
    def test_warm_up_scenario(self, locust_report_dir):
        """Warm-up: 5 req/s for 1 minute."""
        stdout, stderr = self.run_locust(
            users=5,
            spawn_rate=5,
            duration=60,
            scenario_name="warm_up"
        )

        metrics = self.parse_locust_output(stdout, stderr)

        # Assertions: baseline should be healthy
        assert metrics["failed_requests"] < metrics["total_requests"] * 0.01  # < 1% failures
        assert metrics["p95_response_time"] < 2000  # P95 < 2 seconds

    @pytest.mark.slow
    def test_sustained_load_scenario(self, locust_report_dir):
        """Sustained: 30 req/s for 5 minutes = 9000 requests."""
        users = 30
        duration = 300  # 5 minutes
        expected_requests = 9000  # ~30 req/s * 300s

        stdout, stderr = self.run_locust(
            users=users,
            spawn_rate=30,
            duration=duration,
            scenario_name="sustained_load"
        )

        metrics = self.parse_locust_output(stdout, stderr)

        # Assertions: sustained load should maintain high success
        assert metrics["total_requests"] >= expected_requests * 0.95  # At least 95% of expected
        assert metrics["failed_requests"] / metrics["total_requests"] < 0.01  # < 1% failures
        assert metrics["p95_response_time"] < 2000  # P95 < 2 seconds maintained
        assert metrics["p99_response_time"] < 3000  # P99 < 3 seconds

    @pytest.mark.slow
    def test_spike_scenario(self, locust_report_dir):
        """Spike: 60 req/s for 2 minutes."""
        users = 60
        duration = 120  # 2 minutes

        stdout, stderr = self.run_locust(
            users=users,
            spawn_rate=60,
            duration=duration,
            scenario_name="spike_scenario"
        )

        metrics = self.parse_locust_output(stdout, stderr)

        # Assertions: spike should degrade gracefully but not crash
        assert metrics["total_requests"] > 0
        # During spike, < 1% should be errors (5xx), but 429s are acceptable
        assert metrics["p95_response_time"] < 3000  # P95 absorbs spike but stays < 3s
        assert metrics["p99_response_time"] < 5000  # P99 can go higher under spike
```

### 3. Configuration via Environment

```yaml
# config/load_testing.yaml

scenarios:
  warm_up:
    users: 5
    spawn_rate: 5
    duration: 60
    description: "Baseline warm-up, 5 req/s for 1 minute"

  sustained:
    users: 30
    spawn_rate: 30
    duration: 300
    description: "Sustained load, 30 req/s for 5 minutes (9000 requests total)"

  spike:
    users: 60
    spawn_rate: 60
    duration: 120
    description: "Spike detection, 60 req/s for 2 minutes"

thresholds:
  success_rate_min: 0.99  # > 99%
  rate_limited_max: 0.01  # < 1%
  p95_latency_max_ms: 2000  # P95 < 2 seconds
  p99_latency_max_ms: 3000  # P99 < 3 seconds
  p99_latency_spike_max_ms: 5000  # During spike
  error_rate_max: 0.001  # < 0.1% 5xx errors

provider_settings:
  enabled_providers: ["groq", "gemini"]  # Which providers to test
  track_rpm: true  # Monitor rate limit usage
  track_fallback: true  # Count fallback activations
  track_429s: true  # Count rate limit responses
```

### 4. Metrics Collection & Reporting

```python
# scripts/generate_load_report.py

import json
import csv
from datetime import datetime
from pathlib import Path

class LoadTestReporter:
    """Parse Locust CSV/JSON and generate summary report."""

    def __init__(self, csv_dir):
        self.csv_dir = Path(csv_dir)

    def parse_locust_stats(self, stats_csv_path):
        """Parse stats_history.csv from Locust."""
        stats = []
        with open(stats_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                stats.append({
                    "timestamp": row["Timestamp"],
                    "type": row["Type"],
                    "name": row["Name"],
                    "requests": int(row["Requests"]),
                    "failures": int(row["Failures"]),
                    "median": int(row["Median"]),
                    "p95": int(row["95%"]),
                    "p99": int(row["99%"]),
                    "max": int(row["Max"])
                })
        return stats

    def generate_summary(self, scenario_name):
        """Generate summary JSON report."""
        stats_csv = self.csv_dir / f"{scenario_name}_stats_history.csv"
        stats = self.parse_locust_stats(stats_csv)

        # Aggregate across all endpoints
        total_requests = sum(s["requests"] for s in stats)
        total_failures = sum(s["failures"] for s in stats)
        success_rate = (total_requests - total_failures) / total_requests if total_requests > 0 else 0

        # Aggregate latency percentiles
        p95_values = [s["p95"] for s in stats if s["p95"] > 0]
        p99_values = [s["p99"] for s in stats if s["p99"] > 0]
        max_latency = max(s["max"] for s in stats) if stats else 0

        summary = {
            "scenario": scenario_name,
            "timestamp": datetime.now().isoformat(),
            "total_requests": total_requests,
            "total_failures": total_failures,
            "success_rate": success_rate,
            "failure_rate": 1 - success_rate,
            "p95_latency_ms": max(p95_values) if p95_values else 0,
            "p99_latency_ms": max(p99_values) if p99_values else 0,
            "max_latency_ms": max_latency,
            "thresholds_met": {
                "success_rate": success_rate > 0.99,
                "p95_latency": max(p95_values) < 2000 if p95_values else False,
                "p99_latency": max(p99_values) < 3000 if p99_values else False
            }
        }

        return summary

    def export_json(self, scenario_name, summary):
        """Export summary as JSON."""
        output_path = self.csv_dir / f"summary_{scenario_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Report exported to {output_path}")
        return output_path
```

---

## Testing Strategy

### Unit Tests
None required (Locust handles request generation)

### Integration Tests (Pytest)
- 3 load test scenarios executed via Locust CLI wrapper
- Each scenario validates thresholds (success rate, latency, errors)
- Reports generated and validated

### Execution

```bash
# Run specific scenario
python -m pytest tests/load/test_load_scenarios.py::TestLoadScenarios::test_sustained_load_scenario -v -s

# Or run Locust directly (with UI)
locust -f scripts/load_test.py --host http://localhost:8000

# Or run headless
python scripts/load_test.py --scenario sustained
```

---

## Dependencies

- **locust** >= 2.20.0 - Load testing framework
- Existing: FastAPI, Pydantic, asyncpg, redis

---

## Implementation Tasks

1. Create `scripts/load_test.py` with SquadApiUser class and tasks
2. Create `tests/load/test_load_scenarios.py` with 3 scenario tests
3. Create `scripts/generate_load_report.py` for reporting
4. Create `config/load_testing.yaml` for scenario config
5. Update `requirements.txt` with locust
6. Document in README: "Running Load Tests"
7. Validate thresholds are met across all scenarios
8. Generate sample reports (commit to `tests/load/reports/` directory)

---

## Definition of Done

- ✅ All 3 load test scenarios implemented and passing
- ✅ Thresholds met: > 99% success, < 1% 429s, P95 < 2000ms, P99 < 3000ms
- ✅ Locust HTML report generated and readable
- ✅ JSON metrics exported and validated
- ✅ CLI runnable: `pytest tests/load/test_load_scenarios.py -v`
- ✅ Documentation updated with load testing section
- ✅ Sprint status updated: 9-6-load-testing-com-locust -> ready-for-dev

---

## Notes

- Load tests marked with `@pytest.mark.slow` to skip by default in quick CI runs
- For local development, ensure Docker Compose stack is running before executing load tests
- Provider settings (which providers to use) configurable to test different scenarios
- Rate limiting behavior should be observable in health check endpoint and metrics
