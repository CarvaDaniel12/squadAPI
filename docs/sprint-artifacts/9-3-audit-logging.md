# Story 9.3: Audit Logging - PostgreSQL Table

**Epic:** Epic 9 - Production Readiness
**Story Points:** 3
**Priority:** High (MUST-HAVE for Production)
**Status:** Ready for Dev

## Story Description

As an **operator/compliance officer**, I want **all agent executions logged to PostgreSQL** so that I can **have complete traceability of system actions for compliance, debugging, and audit requirements**.

## Business Value

- **Compliance:** LGPD/GDPR audit trail for data processing activities
- **Debugging:** Historical execution data for troubleshooting production issues
- **Analytics:** Query patterns to optimize provider distribution and costs
- **Accountability:** Track which users made what requests with which agents
- **Security:** Detect anomalous behavior patterns (rate abuse, unusual agents)

## Current State Analysis

**Existing Logging:**
✅ **Structured JSON logging** (Epic 5, Story 5.4):
- Logger outputs JSON to stdout/stderr
- Fields: timestamp, level, message, correlation_id, provider, agent
- Good for real-time debugging

❌ **Gaps:**
- No persistent storage (logs rotate/disappear)
- No queryable database for historical analysis
- Cannot answer: "What did user X do last week?"
- Cannot answer: "How many times did Mary use Groq provider today?"
- No retention policy enforcement

**PostgreSQL Setup:**
✅ **Database exists** (Epic 0, Story 0.4):
- PostgreSQL container in docker-compose.yaml
- Connection pool configured
- Used for future rate limit persistence

❌ **Missing:**
- No `audit_logs` table
- No AuditLogger class to write to database
- No integration with Orchestrator

## Acceptance Criteria

### AC1: PostgreSQL Table Schema

**Given** PostgreSQL database running
**When** migration is applied
**Then** `audit_logs` table must be created with:

```sql
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id VARCHAR(100),
    conversation_id VARCHAR(100),
    agent VARCHAR(50) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    latency_ms INTEGER,
    tokens_in INTEGER,
    tokens_out INTEGER,
    error_message TEXT,
    request_id VARCHAR(100),
    metadata JSONB
);

CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_agent ON audit_logs(agent);
CREATE INDEX idx_audit_status ON audit_logs(status);
CREATE INDEX idx_audit_provider ON audit_logs(provider);
```

**And** table supports:
- ✅ Fast queries by timestamp (most recent first)
- ✅ Filter by user_id ("show me all actions by user_123")
- ✅ Filter by agent ("show me all Mary executions")
- ✅ Filter by status ("show me all failed requests")
- ✅ Filter by provider ("show me all Groq usage")

### AC2: AuditLogger Class Implementation

**Given** audit logging requirement
**When** implementing AuditLogger
**Then** class must provide async interface:

```python
# src/audit/logger.py
from typing import Optional
import asyncpg
from datetime import datetime

class AuditLogger:
    """Async audit logger writing to PostgreSQL."""

    def __init__(self, db_pool: asyncpg.Pool):
        self.pool = db_pool

    async def log_execution(
        self,
        agent: str,
        provider: str,
        action: str,
        status: str,
        latency_ms: int,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        tokens_in: Optional[int] = None,
        tokens_out: Optional[int] = None,
        error_message: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> int:
        """
        Log an agent execution to audit_logs table.

        Returns: audit_logs.id of inserted row
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO audit_logs (
                    timestamp, user_id, conversation_id, agent, provider,
                    action, status, latency_ms, tokens_in, tokens_out,
                    error_message, request_id, metadata
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
                )
                RETURNING id
                """,
                datetime.utcnow(),
                user_id,
                conversation_id,
                agent,
                provider,
                action,
                status,
                latency_ms,
                tokens_in,
                tokens_out,
                error_message,
                request_id,
                metadata
            )
            return row['id']

    async def query_by_user(
        self,
        user_id: str,
        limit: int = 100
    ) -> list[dict]:
        """Query audit logs by user_id, most recent first."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM audit_logs
                WHERE user_id = $1
                ORDER BY timestamp DESC
                LIMIT $2
                """,
                user_id,
                limit
            )
            return [dict(row) for row in rows]

    async def query_by_agent(
        self,
        agent: str,
        limit: int = 100
    ) -> list[dict]:
        """Query audit logs by agent, most recent first."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM audit_logs
                WHERE agent = $1
                ORDER BY timestamp DESC
                LIMIT $2
                """,
                agent,
                limit
            )
            return [dict(row) for row in rows]
```

**And** class must:
- ✅ Use asyncpg for async PostgreSQL operations
- ✅ Use connection pool (no new connections per log)
- ✅ Return inserted row ID for reference
- ✅ Handle NULL values for optional fields
- ✅ Support JSONB metadata for extensibility

### AC3: Orchestrator Integration

**Given** Orchestrator executing agent requests
**When** request completes (success or failure)
**Then** must call AuditLogger:

```python
# src/agents/orchestrator.py (pseudo-code changes)

class Orchestrator:
    def __init__(self, ..., audit_logger: AuditLogger):
        self.audit_logger = audit_logger

    async def execute_agent_request(self, request: AgentExecutionRequest) -> AgentExecutionResponse:
        start_time = time.time()

        try:
            # ... existing logic ...
            response = await self._execute_with_provider(request)

            # Log successful execution
            await self.audit_logger.log_execution(
                agent=request.agent,
                provider=response.provider,
                action="execute",
                status="success",
                latency_ms=int((time.time() - start_time) * 1000),
                user_id=request.metadata.get("user_id") if request.metadata else None,
                conversation_id=request.conversation_id,
                tokens_in=response.tokens_in,
                tokens_out=response.tokens_out,
                request_id=request.metadata.get("request_id") if request.metadata else None,
                metadata=request.metadata
            )

            return response

        except Exception as e:
            # Log failed execution
            await self.audit_logger.log_execution(
                agent=request.agent,
                provider="unknown",
                action="execute",
                status="failed",
                latency_ms=int((time.time() - start_time) * 1000),
                user_id=request.metadata.get("user_id") if request.metadata else None,
                conversation_id=request.conversation_id,
                error_message=str(e),
                request_id=request.metadata.get("request_id") if request.metadata else None,
                metadata=request.metadata
            )
            raise
```

**And** integration must:
- ✅ Log on every execution (success or failure)
- ✅ Capture latency in milliseconds
- ✅ Extract user_id from request.metadata if present
- ✅ Store error messages for failed executions
- ✅ Not break execution if audit logging fails (log error, continue)

### AC4: Database Migration Script

**Given** production deployment requirement
**When** migrating database
**Then** migration script must exist:

```python
# scripts/migrate_audit_logs.py
import asyncio
import asyncpg
import os

async def migrate():
    """Create audit_logs table and indexes."""
    conn = await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "squad"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB", "squad_api")
    )

    try:
        # Create table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                user_id VARCHAR(100),
                conversation_id VARCHAR(100),
                agent VARCHAR(50) NOT NULL,
                provider VARCHAR(50) NOT NULL,
                action VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL,
                latency_ms INTEGER,
                tokens_in INTEGER,
                tokens_out INTEGER,
                error_message TEXT,
                request_id VARCHAR(100),
                metadata JSONB
            )
        """)

        # Create indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp DESC)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_agent ON audit_logs(agent)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_status ON audit_logs(status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_provider ON audit_logs(provider)")

        print("✅ Migration completed successfully")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())
```

**And** script must:
- ✅ Be idempotent (CREATE IF NOT EXISTS)
- ✅ Use environment variables for connection
- ✅ Create all indexes
- ✅ Provide clear success/failure output

### AC5: Retention Policy (90 Days)

**Given** long-term audit log storage
**When** logs exceed 90 days
**Then** cleanup script must exist:

```python
# scripts/cleanup_audit_logs.py
import asyncio
import asyncpg
import os
from datetime import datetime, timedelta

async def cleanup(retention_days: int = 90):
    """Delete audit logs older than retention_days."""
    conn = await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "squad"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB", "squad_api")
    )

    try:
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        result = await conn.execute(
            "DELETE FROM audit_logs WHERE timestamp < $1",
            cutoff_date
        )

        # Parse "DELETE N" to get count
        deleted_count = int(result.split()[-1]) if result else 0
        print(f"✅ Deleted {deleted_count} audit logs older than {retention_days} days")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(cleanup())
```

**And** cleanup must:
- ✅ Delete logs older than 90 days by default
- ✅ Be configurable via parameter
- ✅ Report number of deleted rows
- ✅ Be scheduled via cron (documented in runbook)

## Technical Implementation Notes

### File Structure

```
src/
  audit/
    __init__.py
    logger.py          # AuditLogger class
  agents/
    orchestrator.py    # Integration point
scripts/
  migrate_audit_logs.py     # Table creation
  cleanup_audit_logs.py     # Retention enforcement
tests/
  unit/
    test_audit_logger.py    # 10 unit tests
```

### PostgreSQL Connection Pool

Reuse existing pool from `src/main.py`:

```python
# src/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Existing pool creation
    app.state.db_pool = await asyncpg.create_pool(
        host=os.getenv("POSTGRES_HOST"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
        min_size=2,
        max_size=10
    )

    # Initialize AuditLogger
    from src.audit.logger import AuditLogger
    app.state.audit_logger = AuditLogger(app.state.db_pool)

    yield

    await app.state.db_pool.close()
```

### Query Examples

**Find all Mary executions today:**
```sql
SELECT * FROM audit_logs
WHERE agent = 'mary'
  AND timestamp >= CURRENT_DATE
ORDER BY timestamp DESC;
```

**Find failed requests in last hour:**
```sql
SELECT * FROM audit_logs
WHERE status = 'failed'
  AND timestamp >= NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;
```

**Provider usage breakdown today:**
```sql
SELECT provider, COUNT(*) as executions, AVG(latency_ms) as avg_latency
FROM audit_logs
WHERE timestamp >= CURRENT_DATE
GROUP BY provider
ORDER BY executions DESC;
```

## Test Plan

### Unit Tests (10 tests)

**File:** `tests/unit/test_audit_logger.py`

1. **test_log_execution_success** - Log successful execution with all fields
2. **test_log_execution_minimal** - Log with only required fields (agent, provider, action, status)
3. **test_log_execution_with_error** - Log failed execution with error_message
4. **test_log_execution_with_metadata** - Log with JSONB metadata
5. **test_log_execution_returns_id** - Verify returned ID is integer > 0
6. **test_query_by_user** - Query logs by user_id returns correct rows
7. **test_query_by_user_limit** - Query respects limit parameter
8. **test_query_by_agent** - Query logs by agent returns correct rows
9. **test_query_by_agent_empty** - Query non-existent agent returns empty list
10. **test_concurrent_logging** - Multiple async logs don't conflict

**Test Setup:**
```python
import pytest
import asyncpg
from src.audit.logger import AuditLogger

@pytest.fixture
async def db_pool():
    """Create test database pool."""
    pool = await asyncpg.create_pool(
        host="localhost",
        port=5432,
        user="squad",
        password="squad123",
        database="squad_api_test"
    )

    # Create table
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (...)
        """)

    yield pool

    # Cleanup
    async with pool.acquire() as conn:
        await conn.execute("TRUNCATE TABLE audit_logs")

    await pool.close()

@pytest.fixture
async def audit_logger(db_pool):
    return AuditLogger(db_pool)
```

### Integration Tests (2 tests)

**File:** `tests/integration/test_orchestrator_audit.py`

1. **test_orchestrator_logs_success** - Verify successful request logs to database
2. **test_orchestrator_logs_failure** - Verify failed request logs error_message

## Definition of Done

- ✅ PostgreSQL table `audit_logs` created with 5 indexes
- ✅ AuditLogger class implemented with async methods
- ✅ Orchestrator integration logs all executions
- ✅ Migration script `migrate_audit_logs.py` working
- ✅ Cleanup script `cleanup_audit_logs.py` working
- ✅ 10 unit tests passing
- ✅ 2 integration tests passing
- ✅ Documentation updated (README query examples)
- ✅ Runbook updated with retention policy cron job

## Dependencies

- **Prerequisite:** Story 0.4 (PostgreSQL setup)
- **Blocked By:** None
- **Blocks:** Story 9.7 (Security Review - audit logging is a checklist item)

## Estimated Effort

- **Development:** 2 days
  - Day 1: AuditLogger class + migration script + 10 unit tests
  - Day 2: Orchestrator integration + cleanup script + 2 integration tests
- **Testing:** 0.5 day
- **Documentation:** 0.5 day
- **Total:** 3 days

## Success Metrics

After implementation:
- ✅ Every agent execution logged to PostgreSQL (100% coverage)
- ✅ Query latency < 50ms for recent logs (indexed queries)
- ✅ Retention policy enforced (no logs > 90 days)
- ✅ Can answer audit questions:
  - "What did user X do last week?"
  - "How many times did Mary fail today?"
  - "Which provider has highest latency?"
  - "Show me all 429 errors from Groq"

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Audit logging adds latency | Medium | Low | Use async logging, connection pool, don't await if critical path |
| Database becomes large | High | Medium | Enforce 90-day retention, add table partitioning in future |
| PostgreSQL failure breaks system | High | Low | Catch exceptions, log to stderr if DB unavailable, continue execution |
| Missing user_id in requests | Low | High | Make user_id optional, track by conversation_id or request_id |

## Future Enhancements (Post-MVP)

- **Table Partitioning:** Partition by timestamp (monthly) for faster queries
- **Export to S3:** Archive old logs to object storage
- **Audit API Endpoint:** `GET /api/v1/audit?user_id=X` for self-service queries
- **Real-time Alerts:** Alert on suspicious patterns (100+ requests/min from single user)
- **Compliance Reports:** Auto-generate monthly audit reports for compliance team
