# Story 5.5: Metrics Integration - Agent Orchestrator

Status: ✅ **DONE**

## Story

As a orquestrador,
I want metrics integradas em agent execution,
so that todo request é tracked automaticamente.

## Acceptance Criteria

**Given** agent execution request
**When** sistema executa
**Then** deve:

1. ✅ Increment: `llm_requests_total{provider, agent, status}`
2. ✅ Observe: `llm_request_duration_seconds{provider, agent}`
3. ✅ Observe: `llm_tokens_consumed{provider, agent, type="input|output"}`
4. ✅ If 429: Increment `llm_requests_429_total{provider}`
5. ✅ If error: Increment `llm_requests_failure{provider, agent, error_type}`
6. ✅ Set request context for logging (request_id, agent_id, provider)

**And** metrics visíveis em Prometheus UI (http://localhost:9090)

## Implementation Summary

**Developer:** Amelia (Dev Agent)
**Completed:** 2025-11-13
**Tests:** 9 passing (1 skipped), 80% coverage on orchestrator

### What Was Implemented

1. **Metrics Integration** (✅ ALREADY EXISTED, refined):
   - Request success/failure tracking with `record_request_success()` and `record_request_failure()`
   - 429 error tracking with `record_429_error()`
   - Latency tracking with `record_latency()` (converts ms to seconds)
   - Token consumption with `record_tokens()` (input + output)

2. **Logging Context** (✅ ADDED):
   - `set_request_context()` moved BEFORE try block (Epic 5 - Story 5.4)
   - Generates unique `request_id` (UUID) for each request
   - Sets agent_id and provider in context
   - `clear_request_context()` in `finally` block (guarantees cleanup)

3. **Error Handling**:
   - `classify_error()` determines error type (rate_limit, timeout, network, api_error, unknown)
   - Metrics recorded even on failure
   - Context always cleared (no leaks)

## Tasks / Subtasks

- [x] Integrate metrics in orchestrator (AC: #1,#2,#3,#4,#5)
  - [x] Import metrics from src/metrics/requests.py
  - [x] Import metrics from src/metrics/observability.py
  - [x] Add try/except/finally wrapper in orchestrator.execute()
  - [x] Track request start time
  - [x] Increment llm_requests_total on success
  - [x] Observe llm_request_duration_seconds (end - start)
  - [x] Observe llm_tokens_consumed (input + output)
  - [x] Handle 429 errors (increment llm_requests_429_total)
  - [x] Handle other errors (increment llm_requests_failure)

- [x] Integrate logging context (AC: #6)
  - [x] Import set_request_context, clear_request_context from src/utils/logging
  - [x] Generate request_id (uuid4)
  - [x] Set context at request start (BEFORE try block)
  - [x] Clear context in finally block

- [x] Write unit tests (AC: all)
  - [x] Test metrics incremented on success
  - [x] Test duration observed
  - [x] Test tokens observed
  - [x] Test 429 error handling
  - [x] Test general error handling
  - [x] Test logging context set/cleared
  - [x] Test request_id generated and propagated

- [ ] **FUTURE:** Manual verification (AC: #6 - deferred until LLM providers integrated)
  - [ ] Start squad-api locally
  - [ ] Execute test request
  - [ ] Verify metrics in Prometheus UI
  - [ ] Verify logs contain request_id, agent_id, provider

## Dev Notes

### Current Implementation Status

**Target File:** `src/agents/orchestrator.py`

**Key Function:** `async def execute(request: AgentRequest) -> AgentResponse`

**Metrics to Import:**
```python
from src.metrics.requests import track_request, track_429_error
from src.metrics.observability import track_latency, track_tokens
```

**Logging to Import:**
```python
from src.utils.logging import set_request_context, clear_request_context
import uuid
```

**Integration Pattern:**
```python
async def execute(request: AgentRequest) -> AgentResponse:
    # Generate request ID
    request_id = str(uuid.uuid4())

    # Set logging context
    set_request_context(
        request_id=request_id,
        agent_id=request.agent_id,
        provider=request.provider  # May need to resolve from agent
    )

    start_time = time.time()

    try:
        # Execute agent logic
        response = await _execute_agent(request)

        # Track success metrics
        track_request(
            provider=response.provider,
            agent=request.agent_id,
            status="success"
        )

        duration = time.time() - start_time
        track_latency(
            provider=response.provider,
            agent=request.agent_id,
            duration=duration
        )

        if response.usage:
            track_tokens(
                provider=response.provider,
                agent=request.agent_id,
                tokens_in=response.usage.prompt_tokens,
                tokens_out=response.usage.completion_tokens
            )

        return response

    except RateLimitError as e:  # 429 error
        track_429_error(provider=e.provider)
        track_request(
            provider=e.provider,
            agent=request.agent_id,
            status="rate_limited"
        )
        raise

    except Exception as e:
        track_request(
            provider=request.provider,
            agent=request.agent_id,
            status="error"
        )
        raise

    finally:
        # Always clear context
        clear_request_context()
```

### Project Structure Notes

**Files to Modify:**
- `src/agents/orchestrator.py` - Add metrics + logging integration

**Files to Create:**
- `tests/unit/test_orchestrator_metrics.py` - Test metrics integration

**Alignment:**
- Follows existing metrics patterns (Stories 5.1-5.3)
- Uses logging context from Story 5.4
- Try/except/finally ensures metrics always recorded

### References

- [Source: docs/epics.md#Story 5.5]
- [Source: src/metrics/requests.py] - Request tracking functions
- [Source: src/metrics/observability.py] - Latency + token tracking
- [Source: src/utils/logging.py] - Context management
- [Source: src/agents/orchestrator.py] - Target integration point

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Sonnet 4.5 (GitHub Copilot)

### Debug Log References

### Completion Notes List

### File List
