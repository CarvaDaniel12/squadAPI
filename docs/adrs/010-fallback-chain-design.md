# ADR-010: Fallback Chain Design

**Status:** Accepted
**Date:** 2025-11-13
**Epic:** 4 - Intelligent Fallback
**Story:** 4.1 - Fallback Orchestrator

## Context

LLM providers occasionally fail due to:
- Rate limits (429 errors)
- Service outages (5xx errors)
- Timeouts
- Authentication issues

**Business requirement:** 99.9% uptime for Squad API even when individual providers are down.

**Challenges:**
1. How to handle provider failures gracefully?
2. Which provider to fall back to?
3. When to give up and return error?
4. How to verify fallback response quality?

## Decision

Implement a **3-tier fallback chain** with quality verification:

```yaml
# config/agent_chains.yaml
code:
  chains:
    - providers: ["groq", "cerebras", "gemini"]
      quality_check: true
      max_attempts: 3
```

**Fallback Flow:**

```
Request → Primary (Groq)
          ├─ Success → Return
          ├─ Rate Limit (429) → Fallback
          ├─ Timeout → Fallback
          ├─ Server Error (5xx) → Fallback
          └─ Auth Error (401/403) → Fail immediately
                    ↓
          Secondary (Cerebras)
          ├─ Success → Quality Check
          │           ├─ Pass → Return
          │           └─ Fail → Fallback
          └─ Failure → Fallback
                    ↓
          Tertiary (Gemini)
          ├─ Success → Quality Check
          │           ├─ Pass → Return
          │           └─ Fail → Error
          └─ Failure → Error (no more fallbacks)
```

**Implementation:**

```python
class FallbackOrchestrator:
    async def execute_with_fallback(
        self,
        prompt: str,
        chain: list[str]
    ) -> Response:
        last_error = None

        for provider_name in chain:
            try:
                provider = self.factory.get_provider(provider_name)
                response = await provider.generate(prompt)

                # Quality check
                if chain.quality_check:
                    if not self.quality.verify(response):
                        continue  # Try next provider

                return response

            except (RateLimitError, TimeoutError, ServerError) as e:
                logger.warning(f"Provider {provider_name} failed, falling back")
                last_error = e
                continue

            except AuthError as e:
                # Don't fallback on auth errors
                raise

        # All providers failed
        raise AllProvidersFailed(last_error)
```

## Consequences

### Positive

- ✅ **High availability:** 99.9%+ uptime (3 providers = 0.1% × 0.1% × 0.1% = 0.0001% failure rate)
- ✅ **Automatic recovery:** No manual intervention needed
- ✅ **Quality assurance:** Bad responses filtered out
- ✅ **Cost optimization:** Use cheaper providers first
- ✅ **Observable:** Metrics track fallback rate
- ✅ **Configurable:** Per-agent fallback chains
- ✅ **Fast fail:** Auth errors don't waste time

### Negative

- ❌ **Increased latency:** Fallback adds time (30s timeout × 3 = up to 90s)
- ❌ **Higher cost:** May use expensive fallback providers
- ❌ **Complexity:** More code paths to test
- ❌ **Retry storms:** All instances falling back simultaneously can overwhelm secondary providers

## Alternatives Considered

### 1. No Fallback (Fail Fast)

**Description:** Return error immediately on provider failure

**Pros:**
- Simple implementation
- Predictable latency
- No extra cost

**Cons:**
- Low availability (~95% if one provider)
- Poor user experience
- Can't meet 99.9% SLA

**Why Rejected:** Business requires high availability

### 2. Round-Robin Load Balancing

**Description:** Distribute requests evenly across all providers

**Pros:**
- Spreads load evenly
- No primary/secondary concept

**Cons:**
- Uses expensive providers unnecessarily
- Doesn't handle provider failures
- Higher overall cost

**Why Rejected:** Doesn't address failure handling, higher cost

### 3. Circuit Breaker Pattern

**Description:** Temporarily disable failing providers

**Pros:**
- Protects against cascading failures
- Prevents retry storms
- Fast fail for known-bad providers

**Cons:**
- Adds complexity
- May disable recovering providers too long
- Requires state management

**Why Rejected:** Can be added later, fallback chain sufficient for now

**Decision:** Implement circuit breaker in Epic 9 if needed

## Implementation Details

### Quality Verification

```python
class QualityChecker:
    def verify(self, response: str) -> bool:
        # Minimum length
        if len(response) < 50:
            return False

        # Not empty JSON
        if response.strip() in ["{}", "[]", "null"]:
            return False

        # Contains code for code agent
        if self.agent_type == "code":
            if "```" not in response:
                return False

        return True
```

### Fallback Chain Configuration

**Per-Agent Chains:**

```yaml
code:
  chains:
    - providers: ["groq", "cerebras", "gemini"]  # Fast inference
      quality_check: true

creative:
  chains:
    - providers: ["cerebras", "gemini", "groq"]  # Quality over speed
      quality_check: true

data:
  chains:
    - providers: ["groq", "openrouter", "gemini"]
      quality_check: true
```

### Metrics

```python
# Fallback metrics
fallback_triggered_total{agent="code", primary="groq", secondary="cerebras"}
fallback_success_total{agent="code", provider="cerebras"}
fallback_exhausted_total{agent="code"}

# Quality check metrics
quality_check_failed_total{provider="groq"}
quality_check_passed_total{provider="cerebras"}
```

## Error Handling Strategy

| Error Type | Fallback? | Reason |
|------------|-----------|--------|
| 429 Rate Limit | ✅ Yes | Temporary, other providers available |
| 5xx Server Error | ✅ Yes | Provider issue, try alternatives |
| Timeout | ✅ Yes | May be temporary network issue |
| 401/403 Auth | ❌ No | Configuration error, won't fix with fallback |
| 400 Bad Request | ❌ No | Our error, fallback won't help |
| Quality Check Fail | ✅ Yes | Provider returned low-quality response |

## Performance Impact

**Latency analysis:**

```
Best case (primary succeeds):
- Primary provider: 200ms
- Total: 200ms

Fallback case (primary fails, secondary succeeds):
- Primary timeout: 30s
- Secondary provider: 200ms
- Total: 30.2s

Worst case (all fail):
- Primary timeout: 30s
- Secondary timeout: 30s
- Tertiary timeout: 30s
- Total: 90s

Mitigation: Reduce timeout to 10s for faster fallback
```

## Monitoring

**Grafana Dashboard:**
- Fallback trigger rate (should be <5%)
- Fallback success rate (should be >95%)
- Provider health scores
- Fallback chain depth distribution

**Alerts:**
- Fallback rate >20% (provider degradation)
- All providers failing (major outage)
- Quality check failure >50% (prompt issue)

## Migration Path

If fallback chain becomes insufficient:

1. **Add Circuit Breaker:** Temporarily disable failing providers
2. **Add Retry Logic:** Retry on primary before fallback
3. **Add Hedged Requests:** Send to multiple providers simultaneously
4. **Use External Orchestrator:** Envoy, Istio for service mesh

## Testing

**Unit Tests:**
- Test each error type triggers fallback correctly
- Test quality check filters bad responses
- Test all providers failing returns error

**Integration Tests:**
- Simulate provider outages
- Verify fallback chain executes
- Measure end-to-end latency

**Chaos Engineering:**
- Randomly fail providers in production (1%)
- Verify fallback works
- Measure impact on SLA

## References

- [src/agents/fallback.py](../../src/agents/fallback.py)
- [config/agent_chains.yaml](../../config/agent_chains.yaml)
- [ADR-011: Quality Verification System](011-quality-verification.md)
- [Epic 4 Documentation](../../docs/epics.md#epic-4-intelligent-fallback)
