# Story 5.2: Prometheus Metrics - Latency Tracking

**Epic:** Epic 5 - Observability Foundation
**Story ID:** 5.2
**Status:** ready-for-dev
**Created:** 2025-11-13
**Assigned To:** Dev (Amelia)
**Estimated Effort:** 1-2 hours

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## User Story

**As a** operador,
**I want** métricas de latência,
**So that** posso monitorar performance e identificar bottlenecks.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Acceptance Criteria

**Given** agent execution
**When** request completa
**Then** deve expor:
- ✅ `llm_request_duration_seconds{provider, agent}` - Histogram
- ✅ `llm_provider_latency_seconds{provider}` - Histogram
- ✅ Buckets: (0.5, 1, 2, 5, 10, 30) seconds
- ✅ Permite calcular: P50, P95, P99

**And** query `histogram_quantile(0.95, llm_request_duration_seconds{provider="groq"})` retorna P95

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Technical Approach

**Files:**
- ✅ `src/metrics/observability.py` - **ALREADY IMPLEMENTED**
- ❌ `tests/unit/test_metrics_observability.py` - **MISSING - NEEDS CREATION**

**Metrics Already Defined:**
1. `llm_request_duration_seconds` - Histogram with labels [provider, agent]
2. `llm_provider_latency_seconds` - Histogram with labels [provider]

**Functions Already Implemented:**
```python
# Recording functions
record_latency(provider: str, agent: str, latency_seconds: float)
record_provider_latency(provider: str, latency_seconds: float)

# Context managers for auto-timing
LatencyTracker(provider, agent)  # Sync
AsyncLatencyTracker(provider, agent)  # Async
```

**Integration Points:**
- ✅ Already integrated in `orchestrator.py` line 248:
  ```python
  record_latency(provider_name, request.agent, latency_ms / 1000.0)
  ```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Current Status

**IMPLEMENTATION: ✅ COMPLETE**
- Histogram metrics defined with correct buckets
- Recording functions implemented
- Context managers for auto-timing created
- Already integrated in orchestrator

**TESTING: ❌ MISSING**
- No unit tests exist for latency metrics
- Need to verify histogram recording works
- Need to verify context managers work

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Testing Strategy

**Unit Tests Needed:**
Create `tests/unit/test_metrics_observability.py` with:

1. ✅ `test_record_latency()` - Verify histogram.observe() called
2. ✅ `test_record_provider_latency()` - Verify provider-specific histogram
3. ✅ `test_latency_tracker_context_manager()` - Test sync context manager
4. ✅ `test_async_latency_tracker()` - Test async context manager
5. ✅ `test_latency_with_multiple_providers()` - Different providers
6. ✅ `test_latency_buckets()` - Verify correct bucket distribution
7. ✅ `test_latency_without_prometheus()` - Graceful degradation

**Integration Tests:**
- Verify metrics exposed on `/metrics` endpoint
- Verify Prometheus can scrape and calculate percentiles

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Work Division

| Task | Who | Status |
|------|-----|--------|
| Implementation | ✅ Already done | COMPLETE |
| Create unit tests | **Other LLM** | TODO |
| Run tests | **Other LLM** | TODO |
| Verify coverage >= 70% | **Other LLM** | TODO |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Definition of Done

- [x] Latency metrics implemented (✅ Done)
- [x] Recording functions created (✅ Done)
- [x] Context managers implemented (✅ Done)
- [x] Integration with orchestrator (✅ Done)
- [ ] Unit tests created and passing
- [ ] Code coverage >= 70%
- [ ] Integration test with /metrics endpoint
- [ ] Documentation updated
- [ ] sprint-status.yaml updated

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Notes for Test Implementation

**Test File Location:** `tests/unit/test_metrics_observability.py`

**Key Test Scenarios:**

1. **Basic Recording:**
```python
def test_record_latency():
    """Should record latency in histogram"""
    record_latency('groq', 'analyst', 2.5)
    # Verify histogram was updated
```

2. **Context Manager:**
```python
def test_latency_tracker():
    """Should auto-track latency"""
    with LatencyTracker('groq', 'analyst'):
        time.sleep(0.1)  # Simulate work
    # Verify latency recorded ~0.1s
```

3. **Async Context Manager:**
```python
async def test_async_latency_tracker():
    """Should auto-track async latency"""
    async with AsyncLatencyTracker('groq', 'analyst'):
        await asyncio.sleep(0.1)
    # Verify latency recorded
```

4. **Multiple Labels:**
```python
def test_multiple_providers():
    """Should handle different provider/agent combos"""
    record_latency('groq', 'analyst', 1.0)
    record_latency('cerebras', 'pm', 2.0)
    record_latency('gemini', 'architect', 3.0)
```

5. **Bucket Distribution:**
```python
def test_latency_buckets():
    """Should distribute latencies into correct buckets"""
    # Record latencies in different ranges
    record_latency('groq', 'analyst', 0.3)  # < 0.5
    record_latency('groq', 'analyst', 1.5)  # 1-2
    record_latency('groq', 'analyst', 8.0)  # 5-10
```

6. **Graceful Degradation:**
```python
def test_no_prometheus():
    """Should not crash if prometheus_client unavailable"""
    # Mock PROMETHEUS_AVAILABLE = False
    record_latency('groq', 'analyst', 1.0)
    # Should not raise error
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Validation Commands

```bash
# Run tests
pytest tests/unit/test_metrics_observability.py -v

# Check coverage
pytest tests/unit/test_metrics_observability.py --cov=src/metrics/observability --cov-report=term-missing

# Verify metrics endpoint
curl http://localhost:8000/metrics | grep llm_request_duration
```

Expected output should include:
```
llm_request_duration_seconds_bucket{agent="analyst",provider="groq",le="0.5"} 10
llm_request_duration_seconds_bucket{agent="analyst",provider="groq",le="1.0"} 25
llm_request_duration_seconds_sum{agent="analyst",provider="groq"} 42.3
llm_request_duration_seconds_count{agent="analyst",provider="groq"} 50
```
