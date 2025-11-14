"""Unit tests for PII Sanitization (Epic 9, Story 9.2).

Tests the PIISanitizer class with various PII redaction patterns.
"""

import pytest
from src.security.sanitizer import PIISanitizer


@pytest.fixture
def sanitizer():
    """Create PII sanitizer instance."""
    return PIISanitizer()


class TestEmailRedaction:
    """Test email address redaction."""

    def test_redact_single_email(self, sanitizer):
        """Redact single email address."""
        text = "Contact john@acme.com"
        report = sanitizer.sanitize(text)

        assert report.redaction_count == 1
        assert "[EMAIL_REDACTED]" in report.sanitized_text
        assert "john@acme.com" not in report.sanitized_text
        assert report.redactions[0].pii_type == "email"
        assert report.redactions[0].replaced_with == "[EMAIL_REDACTED]"

    def test_redact_multiple_emails(self, sanitizer):
        """Redact multiple email addresses."""
        text = "john@acme.com and mary@corp.org"
        report = sanitizer.sanitize(text)

        assert report.redaction_count == 2
        assert report.sanitized_text.count("[EMAIL_REDACTED]") == 2


class TestPhoneRedaction:
    """Test phone number redaction."""

    def test_redact_phone_br(self, sanitizer):
        """Redact Brazilian phone number."""
        text = "Call me at (11) 99999-9999"
        report = sanitizer.sanitize(text)

        assert report.redaction_count == 1
        assert "[PHONE_REDACTED]" in report.sanitized_text
        assert "(11) 99999-9999" not in report.sanitized_text


class TestCPFRedaction:
    """Test CPF redaction."""

    def test_redact_cpf(self, sanitizer):
        """Redact Brazilian CPF."""
        text = "My CPF is 123.456.789-00"
        report = sanitizer.sanitize(text)

        assert report.redaction_count == 1
        assert "[CPF_REDACTED]" in report.sanitized_text
        assert "123.456.789-00" not in report.sanitized_text


class TestCreditCardRedaction:
    """Test credit card redaction."""

    def test_redact_credit_card(self, sanitizer):
        """Redact credit card number."""
        text = "Card: 4532-1234-5678-9010"
        report = sanitizer.sanitize(text)

        assert report.redaction_count == 1
        assert "[CARD_REDACTED]" in report.sanitized_text


class TestMultipleTypeRedaction:
    """Test redaction of multiple PII types."""

    def test_sanitize_multiple_types(self, sanitizer):
        """Redact multiple PII types in single text."""
        text = "john@acme.com (11) 99999-9999 CPF: 123.456.789-00"
        report = sanitizer.sanitize(text)

        assert report.redaction_count == 3
        assert report.sanitized_text.count("[EMAIL_REDACTED]") == 1
        assert report.sanitized_text.count("[PHONE_REDACTED]") == 1
        assert report.sanitized_text.count("[CPF_REDACTED]") == 1


class TestStructurePreservation:
    """Test that message structure is preserved after redaction."""

    def test_preserve_surrounding_text(self, sanitizer):
        """Surrounding text should be preserved."""
        text = "Hello John, my email is john@acme.com and phone is (11) 99999-9999. Contact me!"
        report = sanitizer.sanitize(text)

        assert "Hello John" in report.sanitized_text
        assert "Contact me" in report.sanitized_text
        assert report.sanitized_text.startswith("Hello John")
        assert report.sanitized_text.endswith("Contact me!")


class TestCleanText:
    """Test clean text without PII."""

    def test_clean_text_unchanged(self, sanitizer):
        """Clean text should remain unchanged."""
        text = "No PII here, just regular text"
        report = sanitizer.sanitize(text)

        assert report.sanitized_text == text
        assert report.redaction_count == 0
        assert len(report.redactions) == 0


class TestRedactionReport:
    """Test redaction report format."""

    def test_redaction_report_format(self, sanitizer):
        """Report should have correct structure."""
        text = "john@acme.com and (11) 99999-9999"
        report = sanitizer.sanitize(text)

        assert hasattr(report, "sanitized_text")
        assert hasattr(report, "redactions")
        assert hasattr(report, "redaction_count")
        assert hasattr(report, "confidence")

        assert isinstance(report.sanitized_text, str)
        assert isinstance(report.redactions, list)
        assert isinstance(report.redaction_count, int)
        assert isinstance(report.confidence, float)

        # Check redaction details
        for redaction in report.redactions:
            assert hasattr(redaction, "pii_type")
            assert hasattr(redaction, "original_text")
            assert hasattr(redaction, "replaced_with")
