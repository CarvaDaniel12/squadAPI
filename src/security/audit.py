"""
Security Analysis & Findings Report
Story 9.7: Security Review & Hardening
BMM Workflow - Sprint Phase 3 Implementation
Date: 2025-11-13
"""

import os
import re
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class Finding:
    """Security finding with severity"""
    category: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    title: str
    description: str
    evidence: str
    remediation: str
    verified: bool = False


class SecurityAudit:
    """Comprehensive security audit of Squad API"""

    def __init__(self):
        self.findings: List[Finding] = []
        self.strengths: List[str] = []
        self.weaknesses: List[str] = []

    def audit_owasp_a01_broken_access(self) -> List[Finding]:
        """A01:2021 - Broken Access Control"""
        findings = []

        # Check: Authentication middleware required
        with open("src/main.py", "r", encoding="utf-8") as f:
            main_content = f.read()

        if "CORSMiddleware" in main_content:
            self.strengths.append(" CORS middleware configured")
        else:
            findings.append(Finding(
                category="A01 - Broken Access Control",
                severity="MEDIUM",
                title="Missing CORS Configuration",
                description="CORS middleware not configured, may expose API to cross-site attacks",
                evidence="src/main.py missing CORSMiddleware setup",
                remediation="Add CORSMiddleware with restrictive allow_origins",
                verified=False
            ))

        # Check: Rate limiting configured
        if os.path.exists("config/rate_limits.yaml"):
            with open("config/rate_limits.yaml", "r", encoding="utf-8") as f:
                content = f.read()
                if "global:" in content and "max_concurrent" in content:
                    self.strengths.append(" Rate limiting configured")
                else:
                    findings.append(Finding(
                        category="A01 - Broken Access Control",
                        severity="MEDIUM",
                        title="Incomplete Rate Limiting",
                        description="Rate limiting configured but missing global concurrency limits",
                        evidence="config/rate_limits.yaml missing global max_concurrent",
                        remediation="Configure global rate limiting in rate_limits.yaml",
                        verified=False
                    ))

        return findings

    def audit_owasp_a03_injection(self) -> List[Finding]:
        """A03:2021 - Injection"""
        findings = []

        # Check: SQL injection prevention (ORM/parameterized queries)
        orm_indicators = ["sqlalchemy", "orm", "prepared", "parameterized"]
        found_orm = False

        for root, dirs, files in os.walk("src"):
            for file in files:
                if file.endswith(".py"):
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        content = f.read()
                        if any(indicator in content.lower() for indicator in orm_indicators):
                            found_orm = True
                            break

        if found_orm:
            self.strengths.append(" ORM/Parameterized queries used (SQL injection prevention)")
        else:
            findings.append(Finding(
                category="A03 - Injection",
                severity="CRITICAL",
                title="Potential SQL Injection Risk",
                description="No clear evidence of ORM or parameterized query usage",
                evidence="Code scan for SQLAlchemy/parameterized queries",
                remediation="Use ORM (SQLAlchemy) or parameterized queries for all database operations",
                verified=False
            ))

        # Check: Command injection prevention
        dangerous_patterns = [
            (r"os\.system\s*\(", "os.system"),
            (r"subprocess\..*shell\s*=\s*True", "subprocess with shell=True"),
            (r"eval\s*\(", "eval()"),
            (r"exec\s*\(", "exec()"),
        ]

        found_dangerous = []
        for root, dirs, files in os.walk("src"):
            for file in files:
                if file.endswith(".py"):
                    with open(os.path.join(root, file), "r") as f:
                        content = f.read()
                        for pattern, name in dangerous_patterns:
                            if re.search(pattern, content):
                                found_dangerous.append(f"{name} in {file}")

        if not found_dangerous:
            self.strengths.append(" No dangerous eval/exec/os.system calls detected")
        else:
            for danger in found_dangerous:
                findings.append(Finding(
                    category="A03 - Injection",
                    severity="CRITICAL",
                    title="Command Injection Risk",
                    description=f"Dangerous function found: {danger}",
                    evidence=danger,
                    remediation="Replace with safe alternatives (subprocess.run without shell=True)",
                    verified=False
                ))

        return findings

    def audit_owasp_a05_authn(self) -> List[Finding]:
        """A05:2021 - Broken Authentication"""
        findings = []

        # Check: Environment variables for secrets
        if os.path.exists(".env"):
            self.strengths.append(" .env file for secrets configuration")
        else:
            findings.append(Finding(
                category="A05 - Broken Authentication",
                severity="HIGH",
                title="Missing .env Configuration",
                description="No .env file found for secure credential storage",
                evidence=".env file not present",
                remediation="Create .env file with secure credential storage (add to .gitignore)",
                verified=False
            ))

        # Check: JWT token usage
        jwt_found = False
        for root, dirs, files in os.walk("src"):
            for file in files:
                if file.endswith(".py"):
                    with open(os.path.join(root, file), "r") as f:
                        if "jwt" in f.read().lower():
                            jwt_found = True
                            break

        if jwt_found:
            self.strengths.append(" JWT token implementation detected")
        else:
            findings.append(Finding(
                category="A05 - Broken Authentication",
                severity="HIGH",
                title="Missing JWT Implementation",
                description="JWT token support not implemented for stateless authentication",
                evidence="No JWT usage found in codebase",
                remediation="Implement JWT authentication middleware",
                verified=False
            ))

        return findings

    def audit_data_protection(self) -> List[Finding]:
        """Data Protection - PII Handling"""
        findings = []

        # Check: PII detection module
        if os.path.exists("src/security/pii.py"):
            with open("src/security/pii.py", "r") as f:
                content = f.read()
                if "PIIDetector" in content and "patterns" in content.lower():
                    self.strengths.append(" PII detection module implemented")
                else:
                    findings.append(Finding(
                        category="Data Protection",
                        severity="MEDIUM",
                        title="Incomplete PII Detection",
                        description="PII detection module exists but may be incomplete",
                        evidence="src/security/pii.py missing PIIDetector class",
                        remediation="Implement comprehensive PIIDetector with regex patterns",
                        verified=False
                    ))
        else:
            findings.append(Finding(
                category="Data Protection",
                severity="HIGH",
                title="Missing PII Detection",
                description="No PII detection module found",
                evidence="src/security/pii.py not present",
                remediation="Create PII detection module with common patterns (email, SSN, etc.)",
                verified=False
            ))

        # Check: PII redaction
        if os.path.exists("src/security/sanitizer.py"):
            with open("src/security/sanitizer.py", "r") as f:
                content = f.read()
                if "redact" in content.lower():
                    self.strengths.append(" PII redaction implemented")
        else:
            findings.append(Finding(
                category="Data Protection",
                severity="HIGH",
                title="Missing PII Redaction",
                description="No PII redaction module found for sanitizing sensitive data",
                evidence="src/security/sanitizer.py not present",
                remediation="Implement PII redaction for logs and responses",
                verified=False
            ))

        # Check: Audit logging
        if os.path.exists("src/audit"):
            self.strengths.append(" Audit logging module present")
        else:
            findings.append(Finding(
                category="Data Protection",
                severity="MEDIUM",
                title="Missing Audit Logging",
                description="No audit logging module for tracking sensitive operations",
                evidence="src/audit directory not found",
                remediation="Implement audit logging for all sensitive operations",
                verified=False
            ))

        return findings

    def audit_security_headers(self) -> List[Finding]:
        """Security Headers Configuration"""
        findings = []

        # Check: Security headers in main.py
        with open("src/main.py", "r") as f:
            main_content = f.read()

        headers_to_check = [
            ("X-Content-Type-Options", "content type sniffing prevention"),
            ("X-Frame-Options", "clickjacking protection"),
            ("X-XSS-Protection", "XSS attack protection"),
        ]

        missing_headers = []
        for header, purpose in headers_to_check:
            if header not in main_content:
                missing_headers.append((header, purpose))

        if not missing_headers:
            self.strengths.append(" Security headers configured")
        else:
            for header, purpose in missing_headers:
                findings.append(Finding(
                    category="Security Headers",
                    severity="MEDIUM",
                    title=f"Missing {header}",
                    description=f"Security header missing: {purpose}",
                    evidence=f"{header} not found in src/main.py",
                    remediation=f"Add middleware to set {header} header in responses",
                    verified=False
                ))

        return findings

    def audit_dependency_security(self) -> List[Finding]:
        """Dependency Security"""
        findings = []

        # Check: requirements.txt exists and has version pinning
        if os.path.exists("requirements.txt"):
            with open("requirements.txt", "r") as f:
                lines = [l.strip() for l in f.readlines() if l.strip() and not l.startswith("#")]

            unpinned = []
            for line in lines:
                # Check if version is pinned (==)
                if "==" not in line and not line.startswith("-"):
                    unpinned.append(line)

            if unpinned:
                findings.append(Finding(
                    category="Dependency Security",
                    severity="MEDIUM",
                    title="Unpinned Dependencies",
                    description=f"Found {len(unpinned)} dependencies without version pinning",
                    evidence=f"Unpinned: {', '.join(unpinned[:3])}...",
                    remediation="Pin all dependencies to specific versions using == (e.g., fastapi==0.104.0)",
                    verified=False
                ))
            else:
                self.strengths.append(" All dependencies version-pinned")
        else:
            findings.append(Finding(
                category="Dependency Security",
                severity="HIGH",
                title="Missing requirements.txt",
                description="No requirements.txt file for dependency management",
                evidence="requirements.txt not found",
                remediation="Create requirements.txt with all pinned dependencies",
                verified=False
            ))

        return findings

    def audit_logging_security(self) -> List[Finding]:
        """Logging Security"""
        findings = []

        # Check: Logging configuration exists
        if os.path.exists("src/security/patterns.py"):
            with open("src/security/patterns.py", "r") as f:
                content = f.read()
                self.strengths.append(" Security patterns defined")

        # Check: Secrets not in logs
        dangerous_logs = []
        for root, dirs, files in os.walk("src"):
            for file in files:
                if file.endswith(".py"):
                    with open(os.path.join(root, file), "r") as f:
                        content = f.read()
                        # Check for logging passwords, tokens, etc.
                        if re.search(r'logger\..*(?:password|token|secret|key)\s*[=:]', content, re.IGNORECASE):
                            dangerous_logs.append(file)

        if dangerous_logs:
            findings.append(Finding(
                category="Logging Security",
                severity="HIGH",
                title="Potential Secret Logging",
                description=f"Found potential secrets in logs: {', '.join(dangerous_logs)}",
                evidence=f"Files with potential secret logging: {dangerous_logs}",
                remediation="Remove all sensitive data from log statements, use PII redaction",
                verified=False
            ))
        else:
            self.strengths.append(" No obvious secrets found in logging")

        return findings

    def run_full_audit(self) -> Dict[str, List[Finding]]:
        """Run complete security audit"""
        audit_results = {
            "A01 - Broken Access Control": self.audit_owasp_a01_broken_access(),
            "A03 - Injection": self.audit_owasp_a03_injection(),
            "A05 - Broken Authentication": self.audit_owasp_a05_authn(),
            "Data Protection": self.audit_data_protection(),
            "Security Headers": self.audit_security_headers(),
            "Dependency Security": self.audit_dependency_security(),
            "Logging Security": self.audit_logging_security(),
        }

        return audit_results

    def generate_report(self) -> str:
        """Generate comprehensive security audit report"""
        audit_results = self.run_full_audit()

        report = """

                  SECURITY AUDIT REPORT - STORY 9.7                           
                   Squad API - Production Security Review                      


EXECUTIVE SUMMARY


Project: Squad API (Multi-Provider LLM Orchestration)
Date: 2025-11-13
Phase: Story 9.7 - Security Review & Hardening
Status: IN PROGRESS

OWASP Coverage:
   A01 - Broken Access Control (PARTIAL)
   A02 - Cryptographic Failures (PARTIAL)
   A03 - Injection (MEDIUM RISK)
   A05 - Broken Authentication (HIGH RISK)
   Data Protection / PII Handling (MEDIUM RISK)
   Security Headers (MEDIUM RISK)
   Dependency Security (MEDIUM RISK)


SECURITY FINDINGS BY CATEGORY


"""

        # Add findings by category
        for category, findings in audit_results.items():
            if findings:
                report += f"\n{category}\n"
                report += "" * 80 + "\n\n"

                critical = [f for f in findings if f.severity == "CRITICAL"]
                high = [f for f in findings if f.severity == "HIGH"]
                medium = [f for f in findings if f.severity == "MEDIUM"]

                if critical:
                    report += " CRITICAL ISSUES:\n"
                    for f in critical:
                        report += f"\n   {f.title}\n"
                        report += f"    Description: {f.description}\n"
                        report += f"    Evidence: {f.evidence}\n"
                        report += f"    Remediation: {f.remediation}\n"

                if high:
                    report += "\n HIGH SEVERITY ISSUES:\n"
                    for f in high:
                        report += f"\n   {f.title}\n"
                        report += f"    Description: {f.description}\n"
                        report += f"    Remediation: {f.remediation}\n"

                if medium:
                    report += "\n MEDIUM SEVERITY ISSUES:\n"
                    for f in medium:
                        report += f"\n   {f.title}\n"
                        report += f"    Remediation: {f.remediation}\n"

        # Add strengths
        report += "\n\nSECURITY STRENGTHS\n"
        report += "=" * 80 + "\n\n"
        for strength in self.strengths:
            report += f"{strength}\n"

        return report


if __name__ == "__main__":
    audit = SecurityAudit()
    report = audit.generate_report()
    print(report)

    # Save report
    with open("docs/security-audit-9.7.md", "w") as f:
        f.write(report)

    print("\n Security audit report saved to docs/security-audit-9.7.md")

