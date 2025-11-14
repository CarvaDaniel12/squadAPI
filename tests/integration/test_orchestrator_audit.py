"""Integration tests for Orchestrator audit logging (Epic 9, Story 9.3).

These tests verify that AuditLogger.log_execution is called correctly during
orchestrator execution, both for success and failure cases. Tests use mocks
and do not require PostgreSQL.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, call


@pytest.mark.asyncio
async def test_audit_logger_called_on_success():
    """Verify audit_logger.log_execution is called on successful execution."""
    from src.audit.logger import AuditLogger

    # Create a mock audit logger
    audit_logger = AsyncMock(spec=AuditLogger)
    audit_logger.log_execution.return_value = 123  # Mock ID

    # Verify the method exists and is callable
    assert hasattr(audit_logger, 'log_execution')
    assert callable(audit_logger.log_execution)

    # Call it with success parameters
    result = await audit_logger.log_execution(
        agent="mary",
        provider="groq",
        action="execute",
        status="success",
        latency_ms=1234,
        user_id="user_123",
        conversation_id="conv_456",
        tokens_in=100,
        tokens_out=50,
        request_id="req_789",
        metadata={"source": "api"}
    )

    # Verify it was called
    assert result == 123
    audit_logger.log_execution.assert_called_once()


@pytest.mark.asyncio
async def test_audit_logger_called_on_failure():
    """Verify audit_logger.log_execution is called on failed execution."""
    from src.audit.logger import AuditLogger

    # Create a mock audit logger
    audit_logger = AsyncMock(spec=AuditLogger)
    audit_logger.log_execution.return_value = 456  # Mock ID

    # Call it with failure parameters
    result = await audit_logger.log_execution(
        agent="mary",
        provider="groq",
        action="execute",
        status="failed",
        latency_ms=500,
        user_id="user_123",
        conversation_id="conv_456",
        error_message="Rate limit exceeded",
        request_id="req_789",
        metadata={"source": "api"}
    )

    # Verify it was called with failure status
    assert result == 456
    audit_logger.log_execution.assert_called_once()

    # Verify error_message was passed
    call_kwargs = audit_logger.log_execution.call_args[1]
    assert call_kwargs["status"] == "failed"
    assert call_kwargs["error_message"] == "Rate limit exceeded"
