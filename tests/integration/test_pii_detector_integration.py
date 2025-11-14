"""Integration tests for PII Detection with Orchestrator (Epic 9, Story 9.1).

Tests PII detection integration with the agent orchestrator.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.security.pii import PIIDetector


@pytest.fixture
def pii_detector():
    """Create PII detector instance."""
    return PIIDetector()


@pytest.fixture
def mock_logger():
    """Create mock logger."""
    return MagicMock()


@pytest.mark.asyncio
async def test_pii_detection_in_orchestrator_message(pii_detector, mock_logger):
    """Test PII detection is called for user messages in orchestrator flow.

    Simulates orchestrator receiving user message with PII and detecting it
    before passing to LLM provider.
    """
    # User sends message with email
    user_message = "My email is john@example.com for contact"

    # Detect PII
    report = pii_detector.detect(user_message)

    # Verify detection
    assert report.has_pii is True
    assert "email" in report.pii_types
    assert len(report.matches) == 1

    # Verify message is NOT blocked (still safe to send with warning)
    # This is the design: warn but continue
    assert "WARN" in report.recommendation


@pytest.mark.asyncio
async def test_pii_detection_multiple_sensitive_fields(pii_detector):
    """Test detection of multiple sensitive fields triggers appropriate warning.

    This simulates a complex user input with multiple PII types.
    """
    # User sends message with multiple PII types
    user_message = (
        "Hello, my name is John and my email is john@acme.com. "
        "You can reach me at (11) 99999-9999. My CPF is 123.456.789-00."
    )

    # Detect PII
    report = pii_detector.detect(user_message)

    # Verify all types detected
    assert report.has_pii is True
    assert len(report.pii_types) == 3
    assert "email" in report.pii_types
    assert "phone_br" in report.pii_types
    assert "cpf" in report.pii_types

    # Verify detailed matches
    assert len(report.matches) == 3

    # Verify recommendation warns about multiple types
    assert "3 PII detected" in report.recommendation
