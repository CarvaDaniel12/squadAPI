# Story 9.2: PII Sanitization - Auto-Redact

**Epic:** 9 - Production Readiness
**Story ID:** 9.2
**Sprint:** 8 (Production Readiness)
**Status:** Drafted
**Date Created:** 2025-11-13
**Assignee:** DEV Agent
**Dependency:** Story 9.1 (PII Detection) ✅ DONE

---

## Story Summary

**As a** system,
**I want** to automatically redact/sanitize detected PII from user prompts,
**So that** sensitive data never gets sent to LLM APIs, preventing data leaks.

**Story Points:** 5
**Priority:** MUST-HAVE (Security)
**Complexity:** Medium

---

## Acceptance Criteria

### AC1: Redact Email Addresses
**Given** PII is detected (from Story 9.1)
**When** auto-redact is enabled
**Then** emails must be replaced with `[EMAIL_REDACTED]`:

**Example:**
```
Input:  "Contact me at john@acme.com or mary@corp.org"
Output: "Contact me at [EMAIL_REDACTED] or [EMAIL_REDACTED]"
```

### AC2: Redact Phone Numbers (Brazil Format)
**Given** phone numbers detected in text
**When** auto-redact is enabled
**Then** phones must be replaced with `[PHONE_REDACTED]`:

**Example:**
```
Input:  "Call me at (11) 99999-9999"
Output: "Call me at [PHONE_REDACTED]"
```

### AC3: Redact CPF (Brazilian ID)
**Given** CPF detected in text
**When** auto-redact is enabled
**Then** CPF must be replaced with `[CPF_REDACTED]`:

**Example:**
```
Input:  "My CPF is 123.456.789-00"
Output: "My CPF is [CPF_REDACTED]"
```

### AC4: Redact Credit Card Numbers
**Given** credit card numbers detected
**When** auto-redact is enabled
**Then** cards must be replaced with `[CARD_REDACTED]`:

**Example:**
```
Input:  "Card: 4532-1234-5678-9010"
Output: "Card: [CARD_REDACTED]"
```

### AC5: Maintain Message Structure
**Given** a message with multiple PII types
**When** auto-redact is enabled
**Then** sanitization must:
- Preserve word boundaries
- Not break sentence structure
- Replace only PII, keep context intact

**Example:**
```
Input:  "Hello John, my email is john@acme.com and phone is (11) 99999-9999"
Output: "Hello John, my email is [EMAIL_REDACTED] and phone is [PHONE_REDACTED]"
Note: "John" kept (name without full context is not PII)
```

### AC6: Sanitization Report
**When** auto-redact is applied
**Then** system returns report:
```python
{
    "sanitized_text": "...",
    "redactions": [
        {"pii_type": "email", "original_snippet": "john@...", "replaced_with": "[EMAIL_REDACTED]"},
        {"pii_type": "phone_br", "original_snippet": "(11) 99...", "replaced_with": "[PHONE_REDACTED]"}
    ],
    "redaction_count": 2,
    "confidence": 0.95
}
```

### AC7: Configuration Option
**When** system starts
**Then** auto-redact must be configurable:
```python
# Environment variable or config
PII_AUTO_REDACT_ENABLED=true  # or false
# Default: false (Story 9.1 only warns, doesn't redact)
```

### AC8: Audit Trail
**When** PII is redacted
**Then** system logs:
```
INFO: PII redacted in message
  redaction_count: 2
  pii_types: ["email", "phone_br"]
  user_id: "user_123"
  timestamp: "2025-11-13T10:30:45Z"
```

---

## Technical Design

### Module Structure

```
src/security/
├── __init__.py          # Exports (updated)
├── pii.py              # PIIDetector class (from 9.1)
├── patterns.py         # PII_PATTERNS (from 9.1)
├── sanitizer.py        # NEW: PIISanitizer class
│
src/models/
├── pii_detection.py    # PIIDetectionReport (from 9.1)
├── pii_sanitization.py  # NEW: PIISanitizationReport
```

### Core Implementation

#### 1. **Sanitization Report Model** (`src/models/pii_sanitization.py`)

```python
"""Pydantic models for PII sanitization."""

from typing import List, Dict
from pydantic import BaseModel, Field


class PIIRedaction(BaseModel):
    """Record of a single PII redaction."""
    pii_type: str = Field(..., description="Type of PII redacted")
    original_text: str = Field(..., description="Original PII text")
    replaced_with: str = Field(..., description="Replacement text (e.g., [EMAIL_REDACTED])")


class PIISanitizationReport(BaseModel):
    """Report of PII sanitization applied to text."""
    sanitized_text: str = Field(..., description="Text after redactions applied")
    redactions: List[PIIRedaction] = Field(default_factory=list, description="List of redactions made")
    redaction_count: int = Field(default=0, description="Total redactions applied")
    confidence: float = Field(default=1.0, description="Confidence score 0.0-1.0")
```

#### 2. **PII Sanitizer** (`src/security/sanitizer.py`)

```python
"""PII Sanitization Engine - Auto-redact detected PII."""

import re
from typing import Dict

from src.security.pii import PIIDetector
from src.models.pii_detection import PIIDetectionReport
from src.models.pii_sanitization import PIISanitizationReport, PIIRedaction


class PIISanitizer:
    """Auto-redact PII in text based on detection."""

    # Redaction templates
    REDACTION_TEMPLATES = {
        "email": "[EMAIL_REDACTED]",
        "phone_br": "[PHONE_REDACTED]",
        "cpf": "[CPF_REDACTED]",
        "credit_card": "[CARD_REDACTED]"
    }

    def __init__(self):
        """Initialize sanitizer with PII detector."""
        self.detector = PIIDetector()

    def sanitize(self, text: str) -> PIISanitizationReport:
        """
        Detect PII and redact it from text.

        Args:
            text: Text to sanitize

        Returns:
            PIISanitizationReport with sanitized text and redaction details
        """
        # Step 1: Detect PII using detector from 9.1
        detection_report = self.detector.detect(text)

        if not detection_report.has_pii:
            # No PII found, return original text
            return PIISanitizationReport(
                sanitized_text=text,
                redactions=[],
                redaction_count=0,
                confidence=1.0
            )

        # Step 2: Build redaction records and sanitize text
        sanitized_text = text
        redactions: list = []

        # Sort matches by position (reverse order to preserve indices)
        sorted_matches = sorted(
            detection_report.matches,
            key=lambda m: m.position,
            reverse=True
        )

        for match in sorted_matches:
            pii_type = match.pii_type
            original_text = match.text
            replacement = self.REDACTION_TEMPLATES.get(
                pii_type,
                f"[{pii_type.upper()}_REDACTED]"
            )

            # Replace in text using exact match position
            start = match.position
            end = start + len(original_text)
            sanitized_text = sanitized_text[:start] + replacement + sanitized_text[end:]

            # Record redaction
            redactions.insert(0, PIIRedaction(
                pii_type=pii_type,
                original_text=original_text,
                replaced_with=replacement
            ))

        # Step 3: Build report
        return PIISanitizationReport(
            sanitized_text=sanitized_text,
            redactions=redactions,
            redaction_count=len(redactions),
            confidence=detection_report.confidence
        )
```

#### 3. **Orchestrator Integration** (`src/agents/orchestrator.py`)

Add configuration option and call sanitizer:

```python
# In __init__:
self.pii_auto_redact_enabled = os.getenv("PII_AUTO_REDACT_ENABLED", "false").lower() == "true"
self.pii_sanitizer = None
if self.pii_auto_redact_enabled:
    from src.security.sanitizer import PIISanitizer
    self.pii_sanitizer = PIISanitizer()

# In execute() after PII detection:
if self.pii_auto_redact_enabled and self.pii_sanitizer:
    sanitization_report = self.pii_sanitizer.sanitize(request.task)

    if sanitization_report.redaction_count > 0:
        logger.info(
            f"[{request_id}] PII redacted from user message",
            extra={
                "redaction_count": sanitization_report.redaction_count,
                "redaction_types": [r.pii_type for r in sanitization_report.redactions]
            }
        )
        # Use sanitized text instead of original
        messages[-1]["content"] = sanitization_report.sanitized_text
    else:
        logger.debug(f"[{request_id}] PII detection passed, no redactions needed")
```

---

## Testing Strategy

### Unit Tests (8 tests)

1. **test_redact_single_email**
   - Input: "john@acme.com"
   - Assert: "[EMAIL_REDACTED]"

2. **test_redact_multiple_emails**
   - Input: "john@acme.com and mary@corp.org"
   - Assert: 2 redactions

3. **test_redact_phone_br**
   - Input: "Call (11) 99999-9999"
   - Assert: "[PHONE_REDACTED]"

4. **test_redact_cpf**
   - Input: "CPF: 123.456.789-00"
   - Assert: "[CPF_REDACTED]"

5. **test_redact_credit_card**
   - Input: "4532-1234-5678-9010"
   - Assert: "[CARD_REDACTED]"

6. **test_sanitize_multiple_types**
   - Input: "john@acme.com (11) 99999-9999 CPF: 123.456.789-00"
   - Assert: 3 redactions, text structure preserved

7. **test_clean_text_unchanged**
   - Input: "No PII here"
   - Assert: text unchanged, 0 redactions

8. **test_redaction_report_format**
   - Assert: report contains sanitized_text, redactions list, count, confidence

### Integration Tests (2 tests)

1. **test_sanitizer_with_orchestrator_enabled**
   - Config: PII_AUTO_REDACT_ENABLED=true
   - User sends: "john@acme.com"
   - Assert: Message sent to LLM is sanitized

2. **test_sanitizer_disabled_by_default**
   - Config: PII_AUTO_REDACT_ENABLED=false (default)
   - User sends: "john@acme.com"
   - Assert: Message sent as-is (only warned in 9.1)

---

## Dependencies

### From Story 9.1
- ✅ PIIDetector class
- ✅ PII_PATTERNS
- ✅ PIIDetectionReport

### New External Libraries
- None! Uses only stdlib `re` module

### Internal Dependencies
- `src/security/pii.py` - PIIDetector
- `src/agents/orchestrator.py` - Integration point
- `src/utils/logging.py` - Logging

---

## Acceptance Criteria Mapping

| AC | Implementation | Testing |
|----|---|---|
| AC1 - Email Redact | PIISanitizer + email template | test_redact_single_email |
| AC2 - Phone Redact | PIISanitizer + phone_br template | test_redact_phone_br |
| AC3 - CPF Redact | PIISanitizer + cpf template | test_redact_cpf |
| AC4 - Card Redact | PIISanitizer + credit_card template | test_redact_credit_card |
| AC5 - Structure Preserved | Replace by position, not regex | test_sanitize_multiple_types |
| AC6 - Report Format | PIISanitizationReport dataclass | test_redaction_report_format |
| AC7 - Configuration | PII_AUTO_REDACT_ENABLED env var | test_sanitizer_disabled_by_default |
| AC8 - Audit Trail | Logger.info with redaction details | Integration test logging |

---

## Success Metrics

- ✅ All PII types redacted correctly
- ✅ Message structure preserved
- ✅ 10/10 unit + integration tests passing
- ✅ 100% code coverage for PIISanitizer
- ✅ Zero external dependencies
- ✅ Auto-redact configurable (on/off)
- ✅ Audit trail logged for each redaction

---

## Configuration

### Default: Warning Only (Story 9.1)
```bash
PII_AUTO_REDACT_ENABLED=false  # Or omitted
# Behavior: Detect PII, warn in logs, send message as-is
```

### Optional: Auto-Redact (Story 9.2)
```bash
PII_AUTO_REDACT_ENABLED=true
# Behavior: Detect PII, redact, send sanitized message
```

---

## Risks & Mitigation

| Risk | Mitigation |
|------|-----------|
| **Position-based redaction fails** | Sort matches reverse by position before replacing |
| **Regex overlapping matches** | Detector already handles (uses regex.finditer) |
| **Performance with large text** | Sanitizer only processes if PII detected |
| **Redaction too aggressive** | Start with false, users can opt-in |

---

## Definition of Done

- [ ] `src/security/sanitizer.py` created with `PIISanitizer` class (100% coverage)
- [ ] `src/models/pii_sanitization.py` created with Pydantic models
- [ ] 8 unit tests written and passing
- [ ] 2 integration tests written and passing
- [ ] Orchestrator integrated with PII_AUTO_REDACT_ENABLED config
- [ ] Default behavior: false (Story 9.1 only, no redaction)
- [ ] Audit logging implemented for redactions
- [ ] No new external dependencies
- [ ] Documentation complete (this file)
- [ ] Code review passed
- [ ] Mark Story 9.2 as DONE
- [ ] Ready for Sprint 9.3 (Audit Logging - already done ✅)

---

## Next Steps

After 9.2 is complete:
- ✅ Story 9.3: Audit Logging - ALREADY DONE (12/12 tests passing)
- Story 9.4: Health Check Enhancement
- Story 9.6: Load Testing
- Story 9.7: Security Review
- Story 9.8: Production Go-Live

**Production Ready Checklist:**
- ✅ Audit Logging (9.3 DONE)
- ✅ PII Detection (9.1 DONE)
- ⏳ PII Redaction (9.2 - THIS STORY)
- ⏳ Health Checks (9.4)
- ⏳ Load Testing (9.6)
- ⏳ Security Review (9.7)
- ⏳ Go-Live Procedure (9.8)

---

## References

- **Story 9.1:** PII Detection (Dependency) ✅ DONE
- **Epic 9:** `docs/epics.md` (line 3290+)
- **Security:** `docs/PRD.md` (Data Protection section)

