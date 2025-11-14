"""Unit tests for PII Detection (Epic 9, Story 9.1).

Tests the PIIDetector class with various PII patterns.
"""

import pytest
from src.security.pii import PIIDetector


@pytest.fixture
def detector():
    """Create PII detector instance."""
    return PIIDetector()


class TestEmailDetection:
    """Test email detection."""

    def test_detect_single_email(self, detector):
        """Detect single email address."""
        text = "Contact john@acme.com"
        report = detector.detect(text)

        assert report.has_pii is True
        assert "email" in report.pii_types
        assert report.count["email"] == 1
        assert "WARN" in report.recommendation

    def test_detect_multiple_emails(self, detector):
        """Detect multiple email addresses."""
        text = "john@acme.com and mary@corp.org"
        report = detector.detect(text)

        assert report.has_pii is True
        assert report.count["email"] == 2
        assert len(report.matches) == 2


class TestPhoneDetection:
    """Test phone number detection."""

    def test_detect_phone_br(self, detector):
        """Detect Brazilian phone number."""
        text = "Call me at (11) 99999-9999"
        report = detector.detect(text)

        assert report.has_pii is True
        assert "phone_br" in report.pii_types
        assert report.count["phone_br"] == 1

    def test_detect_phone_br_without_parentheses(self, detector):
        """Detect phone without parentheses."""
        text = "11 99999-9999"
        report = detector.detect(text)

        assert report.has_pii is True
        assert "phone_br" in report.pii_types


class TestCPFDetection:
    """Test CPF detection."""

    def test_detect_cpf(self, detector):
        """Detect Brazilian CPF."""
        text = "My CPF is 123.456.789-00"
        report = detector.detect(text)

        assert report.has_pii is True
        assert "cpf" in report.pii_types
        assert report.count["cpf"] == 1


class TestCreditCardDetection:
    """Test credit card detection."""

    def test_detect_credit_card(self, detector):
        """Detect credit card number."""
        text = "Card: 4532-1234-5678-9010"
        report = detector.detect(text)

        assert report.has_pii is True
        assert "credit_card" in report.pii_types
        assert report.count["credit_card"] == 1


class TestMultiplePII:
    """Test detection of multiple PII types."""

    def test_detect_multiple_pii_types(self, detector):
        """Detect multiple PII types in single text."""
        text = "john@acme.com (11) 99999-9999 CPF: 123.456.789-00"
        report = detector.detect(text)

        assert report.has_pii is True
        assert len(report.pii_types) == 3
        assert set(report.pii_types) == {"email", "phone_br", "cpf"}
        assert len(report.matches) == 3


class TestCleanText:
    """Test clean text without PII."""

    def test_clean_text_returns_no_pii(self, detector):
        """Clean text should return no PII."""
        text = "Hello, how can I help you today?"
        report = detector.detect(text)

        assert report.has_pii is False
        assert report.pii_types == []
        assert report.count == {}
        assert len(report.matches) == 0
        assert "OK" in report.recommendation


class TestConfidenceScore:
    """Test confidence scoring."""

    def test_confidence_high_when_clean(self, detector):
        """Confidence should be 1.0 for clean text."""
        text = "No sensitive data here"
        report = detector.detect(text)

        assert report.confidence == 1.0

    def test_confidence_lower_with_pii(self, detector):
        """Confidence should decrease with more PII found."""
        text = "Email: john@acme.com Phone: (11) 99999-9999"
        report = detector.detect(text)

        assert report.has_pii is True
        assert report.confidence < 1.0
        assert report.confidence >= 0.5


class TestQuickMethods:
    """Test convenience methods."""

    def test_detect_types_returns_list(self, detector):
        """detect_types should return sorted list of PII types."""
        text = "john@acme.com (11) 99999-9999"
        types = detector.detect_types(text)

        assert isinstance(types, list)
        assert "email" in types
        assert "phone_br" in types
        assert types == sorted(types)  # Verify sorting

    def test_has_pii_true_with_pii(self, detector):
        """has_pii should return True when PII present."""
        text = "Contact: john@acme.com"
        assert detector.has_pii(text) is True

    def test_has_pii_false_without_pii(self, detector):
        """has_pii should return False when no PII."""
        text = "Clean text without sensitive data"
        assert detector.has_pii(text) is False
