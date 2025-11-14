# ADR-002: Redis for Conversation Context Storage

**Status:** Accepted
**Date:** 2025-11-13
**Epic:** 0 - Infrastructure Foundation
**Story:** 0.3 - Redis Setup

## Context

Squad API supports multi-turn conversations where agents need access to previous messages in the conversation. Requirements:

1. **Fast read/write:** <10ms latency for context retrieval
2. **TTL support:** Conversations expire after inactivity
3. **Simple data model:** Key-value storage sufficient
4. **High throughput:** Handle 100+ conversations simultaneously
5. **Persistence:** Survive container restarts

**Data structure needed:**
```json
{
  "conversation_id": "uuid",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "metadata": {
    "created_at": "timestamp",
    "last_updated": "timestamp",
    "agent": "code"
  }
}
```

## Decision

Use **Redis 7-alpine** for conversation context storage with:

- **Data structure:** Hash with JSON-serialized messages
- **Key pattern:** `conversation:{conversation_id}`
- **TTL:** 1 hour of inactivity (configurable)
- **Persistence:** RDB + AOF for durability
- **Memory limit:** 256MB dev, 512MB+ prod
- **Eviction policy:** `allkeys-lru` when memory limit reached

**Configuration:**
```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
  volumes:
    - redis_data:/data
```

**Access pattern:**
```python
# Store conversation
redis.setex(
    f"conversation:{conversation_id}",
    3600,  # 1 hour TTL
    json.dumps(conversation_data)
)

# Retrieve conversation
data = redis.get(f"conversation:{conversation_id}")
conversation = json.loads(data) if data else None
```

## Consequences

### Positive

- ✅ **Blazing fast:** <1ms read/write latency
- ✅ **Simple API:** GET/SET/EXPIRE operations
- ✅ **Built-in TTL:** Automatic cleanup of old conversations
- ✅ **Memory efficient:** 256MB handles thousands of conversations
- ✅ **Persistence:** RDB + AOF prevents data loss
- ✅ **Proven reliability:** Battle-tested in production
- ✅ **Low overhead:** ~10MB memory footprint
- ✅ **Easy backup:** RDB snapshots for point-in-time recovery

### Negative

- ❌ **In-memory only:** Can't store unlimited conversations (use LRU eviction)
- ❌ **Single-threaded:** One CPU core only (sufficient for our scale)
- ❌ **No complex queries:** Can't search across conversations (not needed)
- ❌ **No transactions:** Across multiple keys (not needed for our use case)

## Alternatives Considered

### 1. PostgreSQL

**Description:** Store conversations in relational database

**Pros:**
- Unlimited storage (disk-based)
- Complex queries possible
- ACID transactions
- Already using for rate limits

**Cons:**
- Slower (~10-50ms latency vs <1ms)
- Over-engineered for key-value storage
- Requires schema management
- More resource-intensive

**Why Rejected:** PostgreSQL is overkill for simple key-value storage, Redis 100x faster

### 2. MongoDB

**Description:** Store conversations in document database

**Pros:**
- Flexible schema
- Good for nested documents
- Horizontal scaling

**Cons:**
- Additional dependency (increases complexity)
- Higher resource usage (~500MB minimum)
- Overkill for our simple data model
- Slower than Redis

**Why Rejected:** Don't need document database features, Redis simpler and faster

### 3. In-Memory (Application State)

**Description:** Store conversations in FastAPI application memory

**Pros:**
- No external dependency
- Fastest possible (no network hop)

**Cons:**
- Lost on restart
- Can't scale horizontally (sticky sessions required)
- Memory leaks risk
- No TTL mechanism

**Why Rejected:** Not durable, breaks horizontal scaling

### 4. Memcached

**Description:** Use Memcached instead of Redis

**Pros:**
- Simpler than Redis
- Slightly lower memory overhead
- Multi-threaded

**Cons:**
- No persistence (lost on restart)
- No built-in data structures (hash, list, set)
- Less feature-rich

**Why Rejected:** No persistence is dealbreaker, Redis minimal extra cost

## Implementation Details

**Redis configuration tuning:**

```bash
# Persistence
appendonly yes          # Enable AOF for durability
appendfsync everysec    # Fsync every second (balance perf/durability)

# Memory management
maxmemory 256mb              # Limit to prevent host exhaustion
maxmemory-policy allkeys-lru # Evict least recently used keys

# Performance
tcp-keepalive 300       # Detect dead connections
timeout 0               # No idle connection timeout
```

**Conversation context storage:**

```python
# src/agents/context.py
class ConversationContext:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 3600  # 1 hour

    def store(self, conversation_id: str, messages: list):
        key = f"conversation:{conversation_id}"
        data = json.dumps({
            "messages": messages,
            "updated_at": datetime.utcnow().isoformat()
        })
        self.redis.setex(key, self.ttl, data)

    def retrieve(self, conversation_id: str) -> list:
        key = f"conversation:{conversation_id}"
        data = self.redis.get(key)
        if data:
            return json.loads(data)["messages"]
        return []
```

**Monitoring:**

- Track Redis memory usage: `INFO memory`
- Monitor eviction rate: `INFO stats` → `evicted_keys`
- Alert if eviction rate >10% of keys

## Performance Characteristics

**Benchmarks (local Docker):**

```
SET operations: ~50,000 ops/sec
GET operations: ~80,000 ops/sec
Latency (p50):  <1ms
Latency (p99):  <5ms
```

**Capacity:**

```
Conversation size: ~5KB (10 messages @ 500 chars each)
256MB capacity:    ~50,000 conversations
512MB capacity:    ~100,000 conversations
```

## Migration Path

If Redis becomes insufficient:

1. **Redis Cluster:** Shard across multiple Redis instances
2. **Redis + PostgreSQL:** Hot data in Redis, archive to PostgreSQL after 24h
3. **DynamoDB/MongoDB:** For unlimited conversation history

## References

- [Redis 7 Documentation](https://redis.io/docs/)
- [src/agents/context.py](../../src/agents/context.py)
- [docker-compose.yaml](../../docker-compose.yaml) - Redis service definition
- [ADR-003: PostgreSQL for Rate Limit State](003-postgres-rate-limit-state.md) - Why not PostgreSQL
