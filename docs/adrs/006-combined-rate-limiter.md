# ADR-006: Combined Rate Limiter Architecture

**Status:** Accepted
**Date:** 2025-11-13
**Epic:** 2 - Rate Limiting
**Story:** 2.1 - Combined Rate Limiter

## Context

Squad API integrates multiple LLM providers (Groq, Cerebras, Gemini, OpenRouter, Together AI), each with different rate limits:

**Provider Rate Limits (Free Tiers):**
- Groq: 60 req/min, 60,000 tokens/min
- Cerebras: 30 req/min, 900,000 tokens/min
- Gemini: 60 req/min, 32,000 tokens/min
- OpenRouter: Varies by model
- Together AI: 60 req/min

**Requirements:**
1. Enforce per-provider rate limits
2. Track both requests/min AND tokens/min
3. Handle concurrent requests safely
4. Support multiple rate limit strategies (sliding window, semaphore)
5. Persistent state (survive restarts)
6. Auto-throttle before hitting hard limits

**Problem:** How to enforce multi-dimensional rate limits (requests + tokens) across multiple providers?

## Decision

Implement a **Combined Rate Limiter** that orchestrates multiple rate limiting strategies:

```python
class CombinedRateLimiter:
    def __init__(self):
        self.sliding_window = SlidingWindowRateLimiter(redis)
        self.semaphore = SemaphoreRateLimiter(redis)
        self.auto_throttle = AutoThrottle()

    async def acquire(self, provider: str, tokens: int):
        # Check requests/min (sliding window)
        await self.sliding_window.acquire(f"{provider}:requests")

        # Check tokens/min (sliding window)
        await self.sliding_window.acquire(f"{provider}:tokens", tokens)

        # Check concurrency (semaphore)
        await self.semaphore.acquire(f"{provider}:concurrency")

        # Apply auto-throttle
        await self.auto_throttle.apply(provider)
```

**Architecture:**

```
┌─────────────────────────────────────────┐
│     CombinedRateLimiter                 │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  SlidingWindowRateLimiter         │  │
│  │  - Requests/min tracking          │  │
│  │  - Tokens/min tracking            │  │
│  │  - Redis sorted sets              │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  SemaphoreRateLimiter             │  │
│  │  - Concurrency limits             │  │
│  │  - Redis atomic counters          │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  AutoThrottle                     │  │
│  │  - Adaptive throttling            │  │
│  │  - 80% safety threshold           │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## Consequences

### Positive

- ✅ **Multi-dimensional limits:** Tracks requests AND tokens simultaneously
- ✅ **Composable:** Easy to add new rate limiting strategies
- ✅ **Provider-specific:** Each provider has independent limits
- ✅ **Persistent:** Redis backend survives restarts
- ✅ **Concurrent-safe:** Redis atomic operations prevent race conditions
- ✅ **Graceful degradation:** Auto-throttle prevents hard limit hits
- ✅ **Observable:** Metrics for each limiter component
- ✅ **Testable:** Each strategy unit-testable independently

### Negative

- ❌ **Complexity:** Multiple components to understand and maintain
- ❌ **Redis dependency:** Requires Redis for state storage
- ❌ **Network overhead:** Redis calls add ~1-2ms latency per request
- ❌ **Memory usage:** Sliding windows use Redis sorted sets (~500 bytes per request)

## Alternatives Considered

### 1. Single Strategy (Token Bucket)

**Description:** Use only token bucket algorithm for all limits

**Pros:**
- Simpler implementation
- Well-understood algorithm
- Lower memory usage

**Cons:**
- Doesn't track requests AND tokens separately
- Hard to visualize current usage
- Bursty behavior problematic

**Why Rejected:** Can't handle multi-dimensional limits (requests + tokens)

### 2. In-Memory Rate Limiting

**Description:** Store rate limit state in application memory

**Pros:**
- No Redis dependency
- Fastest possible (no network)
- Simpler deployment

**Cons:**
- Lost on restart
- Can't scale horizontally (state per instance)
- Race conditions with async code

**Why Rejected:** Need persistent state, horizontal scaling support

### 3. External Rate Limiter (Kong, Nginx)

**Description:** Use reverse proxy rate limiting

**Pros:**
- Offload rate limiting to dedicated service
- Battle-tested implementations
- No code changes

**Cons:**
- Can't enforce provider-specific limits
- Can't track token consumption
- Less flexible configuration

**Why Rejected:** Too coarse-grained, can't track tokens

## Implementation Details

### Sliding Window Rate Limiter

Uses Redis sorted sets to track requests in time windows:

```python
class SlidingWindowRateLimiter:
    async def acquire(self, key: str, cost: int = 1):
        now = time.time()
        window_start = now - 60  # 60 second window

        # Remove old entries
        await redis.zremrangebyscore(key, 0, window_start)

        # Count current window
        current = await redis.zcard(key)

        # Check limit
        if current + cost > limit:
            raise RateLimitExceeded()

        # Add new request
        await redis.zadd(key, {str(uuid4()): now})
```

**Why sorted sets:**
- Efficient range operations (remove old entries)
- Accurate sliding window (not fixed buckets)
- Built-in atomic operations

### Semaphore Rate Limiter

Uses Redis atomic counters for concurrency:

```python
class SemaphoreRateLimiter:
    async def acquire(self, key: str):
        current = await redis.incr(key)

        if current > max_concurrent:
            await redis.decr(key)
            raise ConcurrencyLimitExceeded()

        return lambda: redis.decr(key)  # Release function
```

**Why semaphore:**
- Simple concurrency control
- Prevents provider overload
- Fast acquire/release

### Auto-Throttle

Adaptive throttling before hitting hard limits:

```python
class AutoThrottle:
    async def apply(self, provider: str):
        usage = await self.get_usage_percentage(provider)

        if usage > 0.8:  # 80% threshold
            delay = (usage - 0.8) * 10  # 0-2 seconds
            await asyncio.sleep(delay)
```

**Why 80% threshold:**
- Provides safety margin
- Accounts for concurrent requests
- Prevents hard limit hits

## Configuration

**config/rate_limits.yaml:**

```yaml
groq:
  requests_per_minute: 60
  tokens_per_minute: 60000
  max_concurrent: 10
  auto_throttle_threshold: 0.8

cerebras:
  requests_per_minute: 30
  tokens_per_minute: 900000
  max_concurrent: 5
  auto_throttle_threshold: 0.8
```

## Monitoring

**Metrics exposed:**

```
# Requests rate limit
squad_api_rate_limit_usage{provider="groq",type="requests"} 45

# Tokens rate limit
squad_api_rate_limit_usage{provider="groq",type="tokens"} 35000

# Concurrency
squad_api_concurrent_requests{provider="groq"} 3

# Throttling events
squad_api_throttle_events_total{provider="groq"} 15
```

## Performance

**Benchmarks (local Docker):**

```
Rate limit check latency:
- P50: 1.5ms
- P95: 3.2ms
- P99: 8.1ms

Redis operations per check: 3-4
Overhead per request: ~5ms total
```

## Migration Path

If Combined Rate Limiter becomes insufficient:

1. **Redis Cluster:** Shard rate limit state
2. **Distributed Rate Limiter:** Use Envoy or custom service
3. **Provider SDK Rate Limiters:** Use provider's built-in limiting

## References

- [src/rate_limit/combined.py](../../src/rate_limit/combined.py)
- [src/rate_limit/sliding_window.py](../../src/rate_limit/sliding_window.py)
- [src/rate_limit/semaphore.py](../../src/rate_limit/semaphore.py)
- [ADR-007: Auto-Throttle Implementation](007-auto-throttle-implementation.md)
- [Epic 2 Documentation](../../docs/epics.md#epic-2-rate-limiting)
