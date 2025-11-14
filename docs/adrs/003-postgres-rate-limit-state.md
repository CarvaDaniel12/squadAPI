# ADR-003: PostgreSQL for Rate Limit State Persistence

**Status:** Accepted
**Date:** 2025-11-13
**Epic:** 0 - Infrastructure Foundation
**Story:** 0.4 - PostgreSQL Setup

## Context

Rate limiting requires persistent state to track:
- Request counts per provider per time window
- Token consumption per provider
- Historical usage patterns
- Audit trail for debugging

**Requirements:**
1. **Durability:** Survive container restarts
2. **Transactions:** Atomic increments/decrements
3. **Query capability:** Analyze usage patterns
4. **Long-term storage:** 30+ days retention

**Why not Redis alone:** Redis is ephemeral (data loss acceptable for conversations, not for rate limit state)

## Decision

Use **PostgreSQL 15-alpine** for rate limit state persistence:

```sql
CREATE TABLE rate_limit_logs (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    requests INTEGER NOT NULL,
    tokens INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_provider_created (provider, created_at)
);
```

**Why PostgreSQL:**
- ACID transactions prevent race conditions
- Robust query engine for analytics
- Proven reliability (30+ years)
- Low resource overhead (512MB RAM sufficient)

## Consequences

### Positive

- ✅ **Durable:** Rate limit state survives restarts
- ✅ **Queryable:** Analyze usage patterns with SQL
- ✅ **Scalable:** Handles millions of records
- ✅ **ACID:** Transaction guarantees prevent race conditions

### Negative

- ❌ **Slower than Redis:** ~10ms vs <1ms latency
- ❌ **More resource intensive:** 512MB RAM vs 256MB for Redis

## Alternatives Considered

### 1. Redis Only

**Why Rejected:** Redis is in-memory, not durable enough for rate limit state

### 2. SQLite

**Why Rejected:** File-based, hard to scale horizontally

## References

- [docker-compose.yaml](../../docker-compose.yaml)
- [ADR-002: Redis for Conversation Storage](002-redis-conversation-storage.md)
