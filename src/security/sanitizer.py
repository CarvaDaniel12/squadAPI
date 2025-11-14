"""PII Sanitization Engine - Auto-redact detected PII."""

from src.security.pii import PIIDetector
from src.models.pii_sanitization import PIISanitizationReport, PIIRedaction


class PIISanitizer:
    """Auto-redact PII in text based on detection (Story 9.2)."""

    # Redaction templates for each PII type
    REDACTION_TEMPLATES = {
        "email": "[EMAIL_REDACTED]",
        "phone_br": "[PHONE_REDACTED]",
        "cpf": "[CPF_REDACTED]",
        "credit_card": "[CARD_REDACTED]"
    }

    def __init__(self):
        """Initialize sanitizer with PII detector (from Story 9.1)."""
        self.detector = PIIDetector()

    def sanitize(self, text: str) -> PIISanitizationReport:
        """
        Detect PII and redact it from text.

        Args:
            text: Text to sanitize

        Returns:
            PIISanitizationReport with sanitized text and redaction details
        """
        # Step 1: Detect PII using detector from Story 9.1
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

        # Sort matches by position (reverse order to preserve indices when replacing)
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

            # Record redaction (insert at beginning since we're iterating in reverse)
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
