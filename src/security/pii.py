"""PII Detection Engine."""

import re
from typing import List, Dict, Optional

from src.security.patterns import PII_PATTERNS
from src.models.pii_detection import PIIMatch, PIIDetectionReport


class PIIDetector:
    """Detect PII in text using regex patterns."""

    def __init__(self, patterns: Optional[Dict] = None):
        """
        Initialize detector with patterns.

        Args:
            patterns: Custom patterns dict, uses PII_PATTERNS if None
        """
        self.patterns = patterns or PII_PATTERNS
        # Compile patterns at init for performance
        self.compiled_patterns = {}
        for pii_type, config in self.patterns.items():
            self.compiled_patterns[pii_type] = {
                "regex": re.compile(config["pattern"], re.IGNORECASE),
                "risk_level": config["risk_level"],
                "description": config.get("description", "")
            }

    def detect(self, text: str) -> PIIDetectionReport:
        """
        Detect PII in text and return structured report.

        Args:
            text: Text to analyze

        Returns:
            PIIDetectionReport with findings
        """
        matches: List[PIIMatch] = []
        found_types: set = set()

        for pii_type, compiled_config in self.compiled_patterns.items():
            regex = compiled_config["regex"]
            risk_level = compiled_config["risk_level"]

            for match in regex.finditer(text):
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
        count: Dict[str, int] = {}
        for pii_type in found_types:
            count[pii_type] = sum(1 for m in matches if m.pii_type == pii_type)

        # Generate recommendation and confidence
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
            matches=matches,
            recommendation=recommendation,
            confidence=confidence
        )

    def detect_types(self, text: str) -> List[str]:
        """
        Quick check: return only PII types found.

        Args:
            text: Text to analyze

        Returns:
            List of PII types detected, sorted
        """
        report = self.detect(text)
        return report.pii_types

    def has_pii(self, text: str) -> bool:
        """
        Quick check: does text contain any PII?

        Args:
            text: Text to analyze

        Returns:
            True if PII detected, False otherwise
        """
        report = self.detect(text)
        return report.has_pii
