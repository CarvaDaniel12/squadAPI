"""Pydantic models for PII detection."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class PIIMatch(BaseModel):
    """Single PII match result."""
    pii_type: str = Field(..., description="Type of PII detected (email, phone_br, cpf, credit_card)")
    text: str = Field(..., description="Matched text")
    position: int = Field(..., description="Starting position in original text")
    risk_level: str = Field(..., description="Risk level: low, medium, high, critical")


class PIIDetectionReport(BaseModel):
    """Complete PII detection report."""
    has_pii: bool = Field(..., description="Whether any PII was detected")
    pii_types: List[str] = Field(default_factory=list, description="Sorted list of PII types found")
    count: Dict[str, int] = Field(default_factory=dict, description="Count of each PII type")
    matches: List[PIIMatch] = Field(default_factory=list, description="List of all matches")
    recommendation: str = Field(..., description="Recommendation: WARN or OK")
    confidence: float = Field(default=1.0, description="Confidence score 0.0-1.0")
