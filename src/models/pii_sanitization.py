"""Pydantic models for PII sanitization."""

from typing import List
from pydantic import BaseModel, Field


class PIIRedaction(BaseModel):
    """Record of a single PII redaction."""
    pii_type: str = Field(..., description="Type of PII redacted (email, phone_br, cpf, credit_card)")
    original_text: str = Field(..., description="Original PII text before redaction")
    replaced_with: str = Field(..., description="Replacement text (e.g., [EMAIL_REDACTED])")


class PIISanitizationReport(BaseModel):
    """Report of PII sanitization applied to text."""
    sanitized_text: str = Field(..., description="Text after redactions applied")
    redactions: List[PIIRedaction] = Field(default_factory=list, description="List of redactions made")
    redaction_count: int = Field(default=0, description="Total number of redactions applied")
    confidence: float = Field(default=1.0, description="Confidence score 0.0-1.0")
