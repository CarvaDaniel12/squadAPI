# Story 5.3: Prometheus Metrics - Token Consumption

Status: drafted

## Story

As a operador,
I want track tokens consumidos,
so that posso monitorar custo e quota usage.

## Acceptance Criteria

**Given** LLM calls retornando token counts
**When** processo response
**Then** deve expor:

1. ✅ `llm_tokens_consumed{provider, type}` - Histogram (type: input/output)
2. ✅ `llm_tokens_total{provider, type}` - Counter total
3. ✅ Buckets: (100, 500, 1000, 2000, 5000, 10000)
4. ✅ Permite calcular: tokens/day, tokens/hour

**And** dashboard mostra quota usage (% of free-tier):
5. ✅ `llm_quota_usage_percent{provider, quota_type}` - Gauge (quota_type: rpm, rpd, tpm)

## Tasks / Subtasks

- [ ] Validate implementation in src/metrics/observability.py (AC: #1,#2,#3)
  - [x] Histogram `llm_tokens_consumed` already defined
  - [x] Counter `llm_tokens_total` already defined
  - [x] Gauge `llm_quota_usage_percent` already defined
  - [x] Recording function `record_tokens()` implemented
  - [x] Quota function `update_quota_usage()` implemented
  - [ ] Verify integration in orchestrator

- [ ] Create unit tests (AC: #1,#2,#3,#4,#5)
  - [ ] Test `record_tokens()` increments both histogram and counter
  - [ ] Test input vs output token separation
  - [ ] Test multiple providers
  - [ ] Test `update_quota_usage()` sets gauge correctly
  - [ ] Test quota percentage calculation
  - [ ] Test graceful degradation (no prometheus_client)
  - [ ] Test concurrent token recording

- [ ] Verify metrics exposed on /metrics endpoint (AC: #1,#2,#5)
  - [ ] Check `llm_tokens_consumed_bucket` appears
  - [ ] Check `llm_tokens_total` appears
  - [ ] Check `llm_quota_usage_percent` appears

## Dev Notes

### Current Implementation Status

**✅ ALREADY IMPLEMENTED:**
File: `src/metrics/observability.py` (lines 52-104)

**Metrics Defined:**
```python
llm_tokens_consumed = Histogram(
    'llm_tokens_consumed',
    'Tokens consumed per request',
    ['provider', 'type'],  # type: input or output
    buckets=(100, 500, 1000, 2000, 5000, 10000)
)

llm_tokens_total = Counter(
    'llm_tokens_total',
    'Total tokens consumed',
    ['provider', 'type']
)

llm_quota_usage_percent = Gauge(
    'llm_quota_usage_percent',
    'Quota usage as percentage of free tier limit',
    ['provider', 'quota_type']  # quota_type: rpm, rpd, tpm
)
```

**Recording Functions:**
```python
def record_tokens(provider: str, input_tokens: int, output_tokens: int):
    """Record token consumption"""
    if llm_tokens_consumed:
        llm_tokens_consumed.labels(provider=provider, type='input').observe(input_tokens)
        llm_tokens_consumed.labels(provider=provider, type='output').observe(output_tokens)

    if llm_tokens_total:
        llm_tokens_total.labels(provider=provider, type='input').inc(input_tokens)
        llm_tokens_total.labels(provider=provider, type='output').inc(output_tokens)

def update_quota_usage(provider: str, quota_type: str, usage_percent: float):
    """Update quota usage gauge"""
    if llm_quota_usage_percent:
        llm_quota_usage_percent.labels(
            provider=provider,
            quota_type=quota_type
        ).set(usage_percent)
```

**Integration Point:**
- `src/agents/orchestrator.py` line 249: `record_tokens(provider_name, tokens_in, tokens_out)`

### Architecture Patterns

- **Pattern:** Dual metric tracking (Histogram + Counter)
  - Histogram: Distribution analysis (percentiles)
  - Counter: Total accumulation (cost tracking)
- **Graceful Degradation:** All functions check `PROMETHEUS_AVAILABLE` before recording
- **Label Strategy:** `provider` + `type` for granular tracking

### Project Structure Notes

**Alignment:**
- Follows Epic 0 Prometheus setup (Story 0.5)
- Consistent with Story 5.1 (request metrics) and 5.2 (latency metrics)
- Uses same `src/metrics/observability.py` module

**Testing Standards:**
- Must follow pytest conventions from `tests/conftest.py`
- Target: >= 70% coverage
- Must test with/without prometheus_client

### References

- [Source: docs/epics.md#Story-5.3-Prometheus-Metrics-Token-Consumption]
- [Source: src/metrics/observability.py#Lines-52-104]
- [Source: src/agents/orchestrator.py#Line-249]
- [Source: config/prometheus.yml - Scrape configuration]

## Dev Agent Record

### Context Reference

<!-- Story context will be added by story-context workflow if invoked -->

### Agent Model Used

<!-- To be filled by dev agent -->

### Debug Log References

<!-- To be filled by dev agent during implementation -->

### Completion Notes List

<!-- To be filled by dev agent after implementation:
- Files created/modified
- Patterns established
- Warnings for next story
- Technical debt deferred
-->

## Senior Developer Review (AI)

<!-- To be filled during code review workflow -->

### Review Outcome

- [ ] Approve
- [ ] Changes Requested
- [ ] Blocked

### Key Findings

<!-- Review notes -->

### Action Items

<!-- Checkboxes for required changes -->

## Review Follow-ups (AI)

<!-- Post-review tasks -->
