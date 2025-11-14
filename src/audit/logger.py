"""Audit logger for PostgreSQL-based audit trail."""

from typing import Optional
import asyncpg
from datetime import datetime, timezone


class AuditLogger:
    """Async audit logger writing to PostgreSQL."""

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize AuditLogger with database connection pool.

        Args:
            db_pool: asyncpg connection pool
        """
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
        metadata: Optional[dict] = None,
    ) -> int:
        """
        Log an agent execution to audit_logs table.

        Args:
            agent: Agent name (e.g., "mary", "bob")
            provider: Provider name (e.g., "groq", "cerebras")
            action: Action performed (e.g., "execute", "fallback")
            status: Execution status (e.g., "success", "failed")
            latency_ms: Execution latency in milliseconds
            user_id: Optional user identifier
            conversation_id: Optional conversation identifier
            tokens_in: Optional input token count
            tokens_out: Optional output token count
            error_message: Optional error message for failed executions
            request_id: Optional request identifier for tracing
            metadata: Optional JSONB metadata

        Returns:
            int: ID of inserted audit_logs row

        Raises:
            asyncpg.PostgresError: If database operation fails
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
                datetime.now(timezone.utc),
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
                metadata,
            )
            return row["id"]

    async def query_by_user(self, user_id: str, limit: int = 100) -> list[dict]:
        """
        Query audit logs by user_id, most recent first.

        Args:
            user_id: User identifier to filter by
            limit: Maximum number of rows to return (default: 100)

        Returns:
            List of audit log dictionaries
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM audit_logs
                WHERE user_id = $1
                ORDER BY timestamp DESC
                LIMIT $2
                """,
                user_id,
                limit,
            )
            return [dict(row) for row in rows]

    async def query_by_agent(self, agent: str, limit: int = 100) -> list[dict]:
        """
        Query audit logs by agent, most recent first.

        Args:
            agent: Agent name to filter by
            limit: Maximum number of rows to return (default: 100)

        Returns:
            List of audit log dictionaries
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM audit_logs
                WHERE agent = $1
                ORDER BY timestamp DESC
                LIMIT $2
                """,
                agent,
                limit,
            )
            return [dict(row) for row in rows]
