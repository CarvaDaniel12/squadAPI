"""Unit tests for AuditLogger (Epic 9, Story 9.3).

These tests use mocks to avoid requiring a live PostgreSQL connection.
For integration tests with real database, use Supabase or local PostgreSQL.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncpg
from src.audit.logger import AuditLogger


@pytest.fixture
def mock_db_pool():
    """Create a mock asyncpg pool."""
    pool = AsyncMock(spec=asyncpg.Pool)
    return pool


@pytest.fixture
def audit_logger(mock_db_pool):
    """Create AuditLogger instance with mock pool."""
    return AuditLogger(mock_db_pool)


@pytest.mark.asyncio
async def test_log_execution_success(audit_logger, mock_db_pool):
    """Test logging successful execution with all fields."""
    # Mock the connection and fetchrow
    mock_conn = AsyncMock()
    mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_conn.fetchrow.return_value = {"id": 123}

    # Call method
    audit_id = await audit_logger.log_execution(
        agent="mary",
        provider="groq",
        action="execute",
        status="success",
        latency_ms=1234,
        user_id="user_123",
        conversation_id="conv_456",
        tokens_in=100,
        tokens_out=200,
        request_id="req_789",
        metadata={"key": "value"},
    )

    # Verify
    assert audit_id == 123
    mock_conn.fetchrow.assert_called_once()
    mock_db_pool.acquire.assert_called_once()


@pytest.mark.asyncio
async def test_log_execution_minimal(audit_logger, mock_db_pool):
    """Test logging with only required fields (agent, provider, action, status)."""
    mock_conn = AsyncMock()
    mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_conn.fetchrow.return_value = {"id": 456}

    audit_id = await audit_logger.log_execution(
        agent="bob",
        provider="cerebras",
        action="execute",
        status="success",
        latency_ms=500,
    )

    assert audit_id == 456
    mock_conn.fetchrow.assert_called_once()


@pytest.mark.asyncio
async def test_log_execution_with_error(audit_logger, mock_db_pool):
    """Test logging failed execution with error_message."""
    mock_conn = AsyncMock()
    mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_conn.fetchrow.return_value = {"id": 789}

    audit_id = await audit_logger.log_execution(
        agent="mary",
        provider="groq",
        action="execute",
        status="failed",
        latency_ms=100,
        error_message="Rate limit exceeded",
        user_id="user_123",
    )

    assert audit_id == 789
    # Verify error_message was passed
    call_args = mock_conn.fetchrow.call_args
    assert "Rate limit exceeded" in str(call_args)


@pytest.mark.asyncio
async def test_log_execution_with_metadata(audit_logger, mock_db_pool):
    """Test logging with JSONB metadata."""
    mock_conn = AsyncMock()
    mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_conn.fetchrow.return_value = {"id": 999}

    metadata = {
        "source": "web_ui",
        "version": "1.0.0",
        "tags": ["test", "demo"],
    }

    audit_id = await audit_logger.log_execution(
        agent="code",
        provider="gemini",
        action="execute",
        status="success",
        latency_ms=2000,
        metadata=metadata,
    )

    assert audit_id == 999


@pytest.mark.asyncio
async def test_log_execution_returns_id(audit_logger, mock_db_pool):
    """Verify returned ID is integer > 0."""
    mock_conn = AsyncMock()
    mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_conn.fetchrow.return_value = {"id": 123}

    audit_id = await audit_logger.log_execution(
        agent="debug",
        provider="openrouter",
        action="execute",
        status="success",
        latency_ms=750,
    )

    assert isinstance(audit_id, int)
    assert audit_id > 0


@pytest.mark.asyncio
async def test_query_by_user(audit_logger, mock_db_pool):
    """Query logs by user_id returns correct rows."""
    mock_conn = AsyncMock()
    mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn

    # Mock database rows
    mock_rows = [
        {"id": 1, "user_id": "user_alice", "agent": "bob", "latency_ms": 200},
        {"id": 2, "user_id": "user_alice", "agent": "mary", "latency_ms": 100},
    ]
    mock_conn.fetch.return_value = mock_rows

    results = await audit_logger.query_by_user("user_alice")

    assert len(results) == 2
    assert all(row["user_id"] == "user_alice" for row in results)
    mock_conn.fetch.assert_called_once()


@pytest.mark.asyncio
async def test_query_by_user_limit(audit_logger, mock_db_pool):
    """Query respects limit parameter."""
    mock_conn = AsyncMock()
    mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn

    mock_rows = [
        {"id": 1, "user_id": "user_test", "agent": "mary", "latency_ms": 100},
        {"id": 2, "user_id": "user_test", "agent": "mary", "latency_ms": 101},
    ]
    mock_conn.fetch.return_value = mock_rows

    results = await audit_logger.query_by_user("user_test", limit=2)

    assert len(results) == 2
    # Verify limit was passed
    call_args = mock_conn.fetch.call_args
    assert 2 in call_args[0]  # limit parameter


@pytest.mark.asyncio
async def test_query_by_agent(audit_logger, mock_db_pool):
    """Query logs by agent returns correct rows."""
    mock_conn = AsyncMock()
    mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn

    mock_rows = [
        {"id": 1, "agent": "mary", "provider": "cerebras", "latency_ms": 200},
        {"id": 2, "agent": "mary", "provider": "groq", "latency_ms": 100},
    ]
    mock_conn.fetch.return_value = mock_rows

    results = await audit_logger.query_by_agent("mary")

    assert len(results) == 2
    assert all(row["agent"] == "mary" for row in results)
    mock_conn.fetch.assert_called_once()


@pytest.mark.asyncio
async def test_query_by_agent_empty(audit_logger, mock_db_pool):
    """Query non-existent agent returns empty list."""
    mock_conn = AsyncMock()
    mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_conn.fetch.return_value = []

    results = await audit_logger.query_by_agent("nonexistent")

    assert len(results) == 0
    assert results == []


@pytest.mark.asyncio
async def test_concurrent_logging(audit_logger, mock_db_pool):
    """Multiple async logs don't conflict."""
    import asyncio

    # Mock connection
    mock_conn = AsyncMock()
    mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn

    # Return unique IDs for each call
    mock_conn.fetchrow.side_effect = [{"id": i} for i in range(1, 11)]

    # Create 10 concurrent logs
    tasks = [
        audit_logger.log_execution(
            agent=f"agent_{i}",
            provider="groq",
            action="execute",
            status="success",
            latency_ms=100 + i,
        )
        for i in range(10)
    ]

    results = await asyncio.gather(*tasks)

    # All should return unique IDs
    assert len(results) == 10
    assert all(isinstance(id, int) for id in results)
    assert len(set(results)) == 10  # All unique
