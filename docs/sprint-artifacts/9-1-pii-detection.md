# Story 9.1: PII Sanitization - Detection

**Epic:** 9 - Production Readiness
**Story ID:** 9.1
**Sprint:** 8 (Production Readiness)
**Status:** Drafted
**Date Created:** 2025-11-13
**Assignee:** DEV Agent

---

## Story Summary

**As a** system,
**I want** to detect PII (Personally Identifiable Information) in user prompts,
**So that** I can warn before sending sensitive data to LLM APIs and prevent data leaks.

**Story Points:** 5
**Priority:** MUST-HAVE (Security)
**Complexity:** Medium

---

## Acceptance Criteria

### AC1: Detect Email Addresses
**Given** a user prompt contains email addresses
**When** the system validates the input
**Then** the system must detect:
- Standard email format: `user@example.com`
- Complex formats: `first.last+tag@sub.domain.co.uk`
- Multiple emails in single message

**Example:**
```
Input:  "Contact me at john@acme.com or mary@corp.org"
Output: ['email', 'email']
Alert:  "PII detected: 2 email(s). Sanitize before sending?"
```

### AC2: Detect Phone Numbers (Brazil Format)
**Given** a user prompt contains phone numbers
**When** the system validates the input
**Then** the system must detect:
- Format with parentheses: `(11) 99999-9999`
- Format without parentheses: `11 99999-9999`
- Format with dots: `11.99999.9999`
- Both mobile (9-digit) and landline (8-digit) in Brazil

**Example:**
```
Input:  "Call me at (11) 99999-9999 or (21) 3333-4444"
Output: ['phone_br', 'phone_br']
Alert:  "PII detected: 2 phone(s). Sanitize before sending?"
```

### AC3: Detect CPF (Brazilian ID)
**Given** a user prompt contains CPF
**When** the system validates the input
**Then** the system must detect:
- CPF format: `XXX.XXX.XXX-XX` (e.g., `123.456.789-00`)
- Handle with or without formatting

**Example:**
```
Input:  "My CPF is 123.456.789-00"
Output: ['cpf']
Alert:  "PII detected: CPF. Sanitize before sending?"
```

### AC4: Detect Credit Card Numbers (Basic)
**Given** a user prompt contains credit card numbers
**When** the system validates the input
**Then** the system must detect:
- 13-19 digit sequences (VISA, Mastercard, Amex, Discover)
- Grouped patterns: `1234-5678-9012-3456` or continuous

**Example:**
```
Input:  "Card: 4532-1234-5678-9010"
Output: ['credit_card']
Alert:  "PII detected: credit card. Sanitize before sending?"
```

### AC5: Detection Report Format
**When** PII is detected
**Then** system returns structured report:
```python
{
    "has_pii": True,
    "pii_types": ["email", "phone_br"],
    "count": {
        "email": 2,
        "phone_br": 1
    },
    "matches": [
        {"type": "email", "text": "john@acme.com", "position": 15},
        {"type": "phone_br", "text": "(11) 99999-9999", "position": 45}
    ],
    "recommendation": "WARN: 2 PII types detected. Sanitize before sending?"
}
```

### AC6: No False Positives on Clean Input
**Given** a user prompt with no PII
**When** the system validates the input
**Then** the system returns:
```python
{
    "has_pii": False,
    "pii_types": [],
    "count": {},
    "matches": [],
    "recommendation": "OK: No PII detected. Safe to send."
}
```

---

## Technical Design

### Module Structure

```
src/
├── security/
│   ├── __init__.py
│   ├── pii.py                 # PIIDetector class
│   └── patterns.py            # Regex patterns for PII
├── models/
│   └── pii_detection.py       # Pydantic models for PII report
```

### Core Implementation

#### 1. **PII Patterns** (`src/security/patterns.py`)

```python
"""PII detection regex patterns."""

PII_PATTERNS = {
    "email": {
        "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "description": "Email addresses",
        "risk_level": "medium"
    },
    "phone_br": {
        "pattern": r"\(?\d{2}\)?\s?9?\d{4}-?\d{4}",
        "description": "Brazilian phone numbers (landline + mobile)",
        "risk_level": "medium"
    },
    "cpf": {
        "pattern": r"\d{3}\.\d{3}\.\d{3}-\d{2}",
        "description": "Brazilian CPF (ID number)",
        "risk_level": "high"
    },
    "credit_card": {
        "pattern": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        "description": "Credit card numbers (13-19 digits)",
        "risk_level": "critical"
    }
}
```

#### 2. **PII Detector** (`src/security/pii.py`)

```python
"""PII Detection Engine."""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class PIIMatch:
    """Single PII match result."""
    pii_type: str
    text: str
    position: int
    risk_level: str

@dataclass
class PIIDetectionReport:
    """Complete PII detection report."""
    has_pii: bool
    pii_types: List[str]
    count: Dict[str, int]
    matches: List[Dict]
    recommendation: str
    confidence: float  # Overall confidence score

class PIIDetector:
    """Detect PII in text using regex patterns."""

    def __init__(self, patterns: Optional[Dict] = None):
        """Initialize detector with patterns."""
        from .patterns import PII_PATTERNS
        self.patterns = patterns or PII_PATTERNS

    def detect(self, text: str) -> PIIDetectionReport:
        """
        Detect PII in text and return structured report.

        Args:
            text: Text to analyze

        Returns:
            PIIDetectionReport with findings
        """
        matches = []
        found_types = set()

        for pii_type, config in self.patterns.items():
            pattern = config["pattern"]
            risk_level = config["risk_level"]

            for match in re.finditer(pattern, text, re.IGNORECASE):
                pii_match = PIIMatch(
                    pii_type=pii_type,
                    text=match.group(),
                    position=match.start(),
                    risk_level=risk_level
                )
                matches.append(pii_match)
                found_types.add(pii_type)

        # Generate report
        has_pii = len(matches) > 0
        count = {}
        for pii_type in found_types:
            count[pii_type] = sum(1 for m in matches if m.pii_type == pii_type)

        # Generate recommendation
        if not has_pii:
            recommendation = "OK: No PII detected. Safe to send."
            confidence = 1.0
        else:
            types_str = ", ".join(sorted(found_types))
            recommendation = f"WARN: {len(matches)} PII detected ({types_str}). Sanitize before sending?"
            # Confidence inversely proportional to number of matches
            confidence = max(0.5, 1.0 - (len(matches) * 0.1))

        return PIIDetectionReport(
            has_pii=has_pii,
            pii_types=sorted(list(found_types)),
            count=count,
            matches=[asdict(m) for m in matches],
            recommendation=recommendation,
            confidence=confidence
        )

    def detect_types(self, text: str) -> List[str]:
        """Quick check: return only PII types found."""
        report = self.detect(text)
        return report.pii_types

    def has_pii(self, text: str) -> bool:
        """Quick check: does text contain any PII?"""
        report = self.detect(text)
        return report.has_pii
```

#### 3. **Integration Point** (`src/agents/orchestrator.py`)

Add PII detection before sending to LLM:

```python
# In execute() method, before calling provider
from src.security.pii import PIIDetector

pii_detector = PIIDetector()
pii_report = pii_detector.detect(user_message)

if pii_report.has_pii:
    logger.warning(
        f"PII detected in message: {pii_report.pii_types}",
        extra={"pii_count": len(pii_report.matches)}
    )
    # Can either:
    # 1. Warn and continue (current design - Story 9.1)
    # 2. Auto-redact (Story 9.2)
    # 3. Block and return error (configurable)
```

---

## Testing Strategy

### Unit Tests (8 tests)

1. **test_detect_single_email**
   - Input: "Contact john@acme.com"
   - Assert: `has_pii=True, pii_types=['email']`

2. **test_detect_multiple_emails**
   - Input: "john@acme.com and mary@corp.org"
   - Assert: `count['email']=2`

3. **test_detect_phone_br**
   - Input: "Call (11) 99999-9999"
   - Assert: `has_pii=True, pii_types=['phone_br']`

4. **test_detect_cpf**
   - Input: "CPF: 123.456.789-00"
   - Assert: `has_pii=True, pii_types=['cpf']`

5. **test_detect_credit_card**
   - Input: "4532-1234-5678-9010"
   - Assert: `has_pii=True, pii_types=['credit_card']`

6. **test_detect_multiple_pii_types**
   - Input: "john@acme.com (11) 99999-9999 CPF: 123.456.789-00"
   - Assert: `pii_types=['cpf', 'email', 'phone_br']` (sorted), `count=3`

7. **test_clean_text**
   - Input: "Hello, how can I help you today?"
   - Assert: `has_pii=False, pii_types=[], count={}`

8. **test_confidence_score**
   - Input: "email (phone) cpf"
   - Assert: `confidence < 1.0` (because PII found)
   - Input: "clean text"
   - Assert: `confidence == 1.0` (clean)

### Integration Tests (2 tests)

1. **test_pii_detection_in_orchestrator**
   - Mock user sends message with email
   - Assert: Orchestrator logs PII warning before calling provider
   - Assert: Message is NOT blocked (still sent)

2. **test_orchestrator_pii_report_logged**
   - User message: "My email is john@acme.com"
   - Assert: Audit log captures `pii_detected: true`
   - Assert: Audit log captures `pii_types: ['email']`

---

## Dependencies

### External Libraries
- `re` (standard library) - Regex pattern matching

### Internal Dependencies
- `src/models/` - Pydantic models
- `src/agents/orchestrator.py` - Integration point
- `src/utils/logging.py` - Logging

### No New External Dependencies Required ✅

---

## Acceptance Criteria Mapping

| AC | Implementation | Testing |
|----|---|---|
| AC1 - Email Detection | `PIIDetector.detect()` + email regex | test_detect_*_email |
| AC2 - Phone Detection | `PIIDetector.detect()` + phone_br regex | test_detect_phone_br |
| AC3 - CPF Detection | `PIIDetector.detect()` + cpf regex | test_detect_cpf |
| AC4 - Credit Card | `PIIDetector.detect()` + credit_card regex | test_detect_credit_card |
| AC5 - Report Format | `PIIDetectionReport` dataclass | test_detect_multiple_pii_types |
| AC6 - No False Positives | Clean text handling | test_clean_text |

---

## Success Metrics

- ✅ All PII types detected with 95%+ accuracy
- ✅ No false positives on clean text
- ✅ Detection latency < 5ms per message
- ✅ 10/10 unit + integration tests passing
- ✅ 100% code coverage for PIIDetector
- ✅ Zero external dependencies (uses stdlib only)

---

## Risks & Mitigation

| Risk | Mitigation |
|------|-----------|
| **Regex false positives** | Use well-tested patterns, test against real data samples |
| **Performance degradation** | Regex compiled at init, not per-call; benchmarks < 5ms |
| **UTF-8/Unicode issues** | Use Python `re` module with proper encoding handling |
| **Regional variations** | Start with Brazil format; easy to extend to other countries |

---

## Definition of Done

- [ ] `src/security/pii.py` created with `PIIDetector` class (100% coverage)
- [ ] `src/security/patterns.py` created with regex patterns
- [ ] `src/models/pii_detection.py` created with Pydantic models
- [ ] 8 unit tests written and passing
- [ ] 2 integration tests written and passing
- [ ] Orchestrator integrated to call `PIIDetector` before LLM call
- [ ] No external dependency additions
- [ ] Documentation complete (this file)
- [ ] Code review passed
- [ ] Sprint artifact ready for Story 9.2 (auto-redact)

---

## Next Steps (Story 9.2)

Once 9.1 is complete, Story 9.2 (PII Sanitization - Auto-Redact) will:
1. Use `PIIDetectionReport` from 9.1
2. Replace detected PII with redacted versions: `[EMAIL_REDACTED]`, `[PHONE_REDACTED]`, etc.
3. Provide option to auto-redact instead of warning
4. Log redaction actions to audit trail

**Story 9.2 Dependency:** ✅ This story (9.1)

---

## References

- **Epic 9:** `docs/epics.md` (line 3244+)
- **Security Requirements:** `docs/PRD.md` (section: Data Protection)
- **Similar Implementations:** PII detection libraries (but avoiding external deps for MVP)
- **Related Stories:** 9.2 (Auto-Redact), 9.3 (Audit Logging)

