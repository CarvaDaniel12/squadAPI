"""PII detection regex patterns and metadata."""

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
