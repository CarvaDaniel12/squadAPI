# Epic 9: Production Readiness - Technical Context

**Epic:** Epic 9 - Production Readiness
**Created:** 2025-11-13
**Status:** Contexted
**Dependencies:** Epics 0-8 (complete system)

---

## Overview

Epic 9 foca em preparar o Squad API para produção através de segurança, compliance, auditoria e validação de performance. Este épico garante que o sistema não é apenas funcional, mas também **seguro, rastreável e testado sob carga real**.

**Key Outcomes:**
- ✅ PII detection e sanitization automática
- ✅ Audit logging completo (rastreabilidade 100%)
- ✅ Health checks detalhados (componente-level)
- ✅ Load testing validado (120+ RPM alcançável)
- ✅ Security review completo
- ✅ Go-live procedure documentado

---

## Business Context

### Why Epic 9 Matters

**Scenario:** Sem Epic 9, Squad API funciona mas não está pronto para produção real:
- ❌ User pode enviar CPF/email para LLM APIs (privacy risk)
- ❌ Sem audit trail = impossível rastrear "quem fez o quê"
- ❌ Health check básico não mostra status de componentes críticos
- ❌ Sem load testing = não sabemos se aguenta 130 RPM real
- ❌ Sem security review = vulnerabilidades desconhecidas

**With Epic 9:**
- ✅ PII automaticamente detectado e sanitizado (LGPD compliance)
- ✅ Audit logs em PostgreSQL (rastreabilidade completa)
- ✅ Health checks mostram Redis, Postgres, todos providers
- ✅ Load testing valida 120+ RPM com <1% 429 errors
- ✅ Security checklist completo validado
- ✅ Go-live procedure claro e testado

---

## Technical Architecture

### Current State (After Epic 8)

```
Squad API Stack:
├── FastAPI Application (Epic 1)
├── Agent Transformation Engine (Epic 1)
├── Rate Limiting Layer (Epic 2)
├── Provider Wrappers (Epic 3) - Groq, Cerebras, Gemini, OpenRouter
├── Fallback & Resilience (Epic 4)
├── Observability (Epic 5) - Prometheus metrics, JSON logging
├── Monitoring (Epic 6) - Grafana dashboards, Slack alerts
├── Configuration System (Epic 7) - Hot-reload, validation
└── Deployment & Docs (Epic 8) - Docker Compose, runbooks, OpenAPI
```

**Epic 9 adds:**
```
Production Readiness Layer:
├── src/security/
│   ├── pii_detector.py      # Story 9.1 - PII detection
│   ├── pii_sanitizer.py     # Story 9.2 - Auto-redaction
│   └── security_checklist.md # Story 9.7
├── src/audit/
│   ├── audit_logger.py      # Story 9.3 - PostgreSQL logging
│   └── migrations/
│       └── 001_audit_logs_table.sql
├── src/api/
│   ├── health.py            # Story 9.4 - Enhanced health checks
│   └── providers.py         # Story 9.5 - Provider status endpoint
├── tests/load/
│   ├── locustfile.py        # Story 9.6 - Load testing
│   └── reports/
└── docs/runbooks/
    └── go-live.md           # Story 9.8 - Production procedure
```

---

## Technical Decisions

### 1. PII Detection Strategy (Stories 9.1, 9.2)

**Decision:** Regex-based detection com auto-sanitization opcional

**Alternatives Considered:**
- ❌ ML-based PII detection (overkill para MVP, latency concerns)
- ❌ External PII service (dependency, cost)
- ✅ Regex patterns (simple, fast, no dependencies)

**Implementation:**
```python
# src/security/pii_detector.py
import re
from typing import List, Dict

class PIIDetector:
    """Detect PII in text using regex patterns"""

    PATTERNS = {
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'phone_br': r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}',
        'cpf': r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}',
        'cnpj': r'\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}',
        'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
    }

    def detect(self, text: str) -> Dict[str, List[str]]:
        """Returns dict of {pii_type: [matches]}"""
        found = {}
        for pii_type, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                found[pii_type] = matches
        return found

    def has_pii(self, text: str) -> bool:
        """Quick check if any PII exists"""
        return bool(self.detect(text))

class PIISanitizer:
    """Auto-redact PII from text"""

    def __init__(self, detector: PIIDetector):
        self.detector = detector

    def sanitize(self, text: str) -> tuple[str, Dict[str, int]]:
        """
        Returns (sanitized_text, redaction_counts)

        Example:
        >>> sanitize("Contact: john@example.com or (11) 99999-9999")
        ("Contact: [EMAIL_REDACTED] or [PHONE_REDACTED]", {'email': 1, 'phone_br': 1})
        """
        sanitized = text
        redactions = {}

        for pii_type, pattern in self.detector.PATTERNS.items():
            replacement = f"[{pii_type.upper()}_REDACTED]"
            count = len(re.findall(pattern, sanitized))
            if count > 0:
                sanitized = re.sub(pattern, replacement, sanitized)
                redactions[pii_type] = count

        return sanitized, redactions
```

**Integration Points:**
- `src/agents/orchestrator.py` - Check PII before sending to LLM
- `src/api/agents.py` - Warn user if PII detected
- Configuration: `settings.PII_AUTO_SANITIZE = True/False`

---

### 2. Audit Logging Architecture (Story 9.3)

**Decision:** PostgreSQL table com retention policy

**Why PostgreSQL:**
- ✅ Already in stack (Epic 0)
- ✅ Structured queries fáceis
- ✅ Retention policies com partitioning
- ✅ No extra infra needed

**Schema:**
```sql
-- migrations/001_audit_logs_table.sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id VARCHAR(100),
    conversation_id VARCHAR(100),
    agent VARCHAR(50) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100),
    prompt_length INTEGER,
    response_length INTEGER,
    tokens_in INTEGER,
    tokens_out INTEGER,
    latency_ms INTEGER,
    status VARCHAR(20) NOT NULL,  -- 'success', 'error', 'rate_limited', 'fallback'
    error_message TEXT,
    pii_detected BOOLEAN DEFAULT FALSE,
    pii_sanitized BOOLEAN DEFAULT FALSE,
    metadata JSONB
);

CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_agent ON audit_logs(agent);
CREATE INDEX idx_audit_status ON audit_logs(status);

-- Retention policy (opcional, para otimização futura)
-- Particionar por mês, deletar partições > 90 dias
```

**Implementation:**
```python
# src/audit/audit_logger.py
import asyncpg
from datetime import datetime
from typing import Optional, Dict

class AuditLogger:
    """PostgreSQL audit logging"""

    def __init__(self, pg_pool: asyncpg.Pool):
        self.pool = pg_pool

    async def log_execution(
        self,
        user_id: Optional[str],
        conversation_id: Optional[str],
        agent: str,
        provider: str,
        model: str,
        prompt_length: int,
        response_length: int,
        tokens_in: int,
        tokens_out: int,
        latency_ms: int,
        status: str,
        error_message: Optional[str] = None,
        pii_detected: bool = False,
        pii_sanitized: bool = False,
        metadata: Optional[Dict] = None
    ):
        """Log agent execution to audit_logs table"""
        query = """
            INSERT INTO audit_logs (
                timestamp, user_id, conversation_id, agent, provider, model,
                prompt_length, response_length, tokens_in, tokens_out,
                latency_ms, status, error_message, pii_detected, pii_sanitized, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
        """

        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                datetime.utcnow(), user_id, conversation_id, agent, provider, model,
                prompt_length, response_length, tokens_in, tokens_out,
                latency_ms, status, error_message, pii_detected, pii_sanitized, metadata
            )

    async def query_by_user(self, user_id: str, limit: int = 100):
        """Get audit logs for specific user"""
        query = """
            SELECT * FROM audit_logs
            WHERE user_id = $1
            ORDER BY timestamp DESC
            LIMIT $2
        """
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, user_id, limit)
```

---

### 3. Enhanced Health Checks (Story 9.4)

**Decision:** Component-level health checks com status aggregation

**Structure:**
```python
# src/api/health.py (enhanced)
from fastapi import APIRouter, Depends
from typing import Dict
import asyncpg
import redis.asyncio as redis

router = APIRouter()

async def check_redis(redis_client: redis.Redis) -> Dict:
    """Check Redis health"""
    try:
        start = time.time()
        await redis_client.ping()
        latency_ms = int((time.time() - start) * 1000)
        return {"status": "healthy", "latency_ms": latency_ms}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def check_postgres(pg_pool: asyncpg.Pool) -> Dict:
    """Check PostgreSQL health"""
    try:
        start = time.time()
        async with pg_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        latency_ms = int((time.time() - start) * 1000)
        return {"status": "healthy", "latency_ms": latency_ms}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def check_providers(orchestrator) -> Dict:
    """Check all provider statuses"""
    # Get from rate limiters + last 429 tracking
    providers = {}
    for provider_name in ["groq", "cerebras", "gemini", "openrouter"]:
        limiter = orchestrator.get_rate_limiter(provider_name)
        providers[provider_name] = {
            "status": "healthy" if limiter.available() else "degraded",
            "rpm_available": limiter.tokens_available,
            "last_429": limiter.last_429_timestamp
        }
    return providers

@router.get("/health")
async def health_check(
    redis_client = Depends(get_redis),
    pg_pool = Depends(get_postgres),
    orchestrator = Depends(get_orchestrator)
):
    """Enhanced health check with component-level status"""

    components = {
        "redis": await check_redis(redis_client),
        "postgres": await check_postgres(pg_pool),
        "prometheus": {"status": "healthy"},  # Prometheus is passive
        "providers": await check_providers(orchestrator)
    }

    # Aggregate status
    overall_status = "healthy"
    if any(c["status"] == "unhealthy" for c in components.values() if isinstance(c, dict)):
        overall_status = "unhealthy"
    elif any(c["status"] == "degraded" for c in components.values() if isinstance(c, dict)):
        overall_status = "degraded"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": int(time.time() - app_start_time),
        "components": components
    }
```

---

### 4. Load Testing Strategy (Story 9.6)

**Decision:** Locust para simulation de 120-130 RPM distribuídos

**Why Locust:**
- ✅ Python-based (familiar stack)
- ✅ Distributed load generation
- ✅ Web UI para monitoring real-time
- ✅ HTML reports automáticos

**Test Scenarios:**
```python
# tests/load/locustfile.py
from locust import HttpUser, task, between
import random

class SquadAPIUser(HttpUser):
    wait_time = between(1, 3)  # 1-3s entre requests

    def on_start(self):
        """Setup user session"""
        self.headers = {"Content-Type": "application/json"}
        self.conversation_id = f"load-test-{random.randint(1000, 9999)}"

    @task(5)  # 50% analyst (mais frequente)
    def execute_analyst(self):
        self.client.post("/v1/agents/analyst", json={
            "prompt": "Analyze market trends for Q4 2025",
            "conversation_id": self.conversation_id
        }, headers=self.headers)

    @task(3)  # 30% code
    def execute_code(self):
        self.client.post("/v1/agents/code", json={
            "prompt": "Write a Python function to validate email",
        }, headers=self.headers)

    @task(2)  # 20% creative
    def execute_creative(self):
        self.client.post("/v1/agents/creative", json={
            "prompt": "Write a product description for smart watch",
        }, headers=self.headers)

    @task(1)  # 10% health checks
    def check_health(self):
        self.client.get("/health")
```

**Run Command:**
```bash
# 30 concurrent users, spawn 5/sec, run 5 minutes
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users=30 \
    --spawn-rate=5 \
    --run-time=5m \
    --html=reports/load-test-$(date +%Y%m%d-%H%M%S).html
```

**Success Criteria:**
- ✅ Total requests: 9000+ (30 req/s * 300s)
- ✅ Success rate: >99%
- ✅ 429 errors: <1% (auto-throttling working)
- ✅ Latency P50: <1s
- ✅ Latency P95: <3s
- ✅ No crashes/errors

---

## Story Prioritization

### Must-Have (Launch Blockers)

**Story 9.3: Audit Logging** - CRITICAL
- **Why:** Compliance, rastreabilidade legal
- **Risk:** Sem audit = não pode produção (compliance fail)
- **Effort:** 2-3 dias (migration + logger + integration)

**Story 9.4: Enhanced Health Checks** - CRITICAL
- **Why:** Ops precisa saber status de componentes
- **Risk:** Sem health = blind deployments
- **Effort:** 1 dia (extend existing endpoint)

**Story 9.6: Load Testing** - CRITICAL
- **Why:** Validar que 120 RPM real funciona
- **Risk:** Sem load test = não sabemos se aguenta produção
- **Effort:** 2 dias (Locust setup + scenarios + validate)

**Story 9.7: Security Review** - CRITICAL
- **Why:** Não pode produção sem security validation
- **Risk:** Vulnerabilidades desconhecidas
- **Effort:** 1 dia (checklist + pip-audit + review)

**Story 9.8: Go-Live Procedure** - CRITICAL
- **Why:** Sem procedure = lançamento caótico
- **Risk:** Esquecemos passos críticos no launch
- **Effort:** 1 dia (documentação)

### Nice-to-Have (Post-Launch OK)

**Story 9.1: PII Detection** - NICE
- **Why:** LGPD compliance, mas pode ser manual MVP
- **Risk:** Privacy concerns, mas mitigável com user education
- **Effort:** 1 dia (regex patterns + tests)
- **Defer:** Pode launch sem PII detection se users treinados

**Story 9.2: Auto-Sanitization** - NICE
- **Why:** Automation, mas manual OK para MVP
- **Risk:** Baixo se 9.1 não implementado
- **Effort:** 1 dia (extends 9.1)
- **Defer:** Sim, pode adicionar post-launch

**Story 9.5: Provider Status Endpoint** - NICE
- **Why:** Useful, mas não blocker (health check já mostra)
- **Risk:** Nenhum (nice-to-have feature)
- **Effort:** 1 dia (extend rate limiters)
- **Defer:** Sim, pode adicionar quando tiver bandwidth

---

## Recommended Execution Plan

### Phase 1: Foundation (Dias 1-3)
```
Day 1: Story 9.3 - Audit Logging
  - Migration script audit_logs table
  - AuditLogger class
  - Integration com orchestrator
  - 10 tests

Day 2: Story 9.4 - Enhanced Health Checks
  - Component checks (Redis, Postgres, providers)
  - Status aggregation
  - 8 tests

Day 3: Story 9.6 - Load Testing (Parte 1)
  - Locust setup
  - Basic scenarios
  - Initial test run
```

### Phase 2: Validation (Dias 4-5)
```
Day 4: Story 9.6 - Load Testing (Parte 2)
  - Complex scenarios (multi-turn, fallback)
  - Full 5min test
  - Report analysis
  - 5 tests

Day 5: Story 9.7 + 9.8 - Security & Go-Live
  - Security checklist validation
  - pip-audit
  - Go-live procedure doc
```

### Phase 3: Optional (Post-Launch or Parallel)
```
Optional Day 6-7: Stories 9.1, 9.2, 9.5 (se tiver bandwidth)
  - PII detection + sanitization
  - Provider status endpoint
```

---

## Testing Strategy

### Unit Tests (Per Story)
- **9.1:** 8 tests (regex patterns, detection accuracy)
- **9.2:** 6 tests (sanitization correctness, edge cases)
- **9.3:** 10 tests (audit log creation, queries, retention)
- **9.4:** 8 tests (component checks, status aggregation)
- **9.5:** 6 tests (provider status accuracy)
- **9.6:** 5 tests (Locust scenarios validate)
- **9.7:** N/A (manual checklist)
- **9.8:** N/A (documentation)

**Total:** ~40-45 unit tests

### Integration Tests
- Audit logging end-to-end (orchestrator → PostgreSQL)
- Health check com real components
- Load test full stack

### Load Testing Metrics
- RPS: 30 sustained
- Duration: 5 minutes
- Total requests: 9000+
- Success rate: >99%
- P95 latency: <3s

---

## Risk Assessment

### High Risk
❗ **Load testing fails (doesn't hit 120 RPM)**
- **Mitigation:** Tune rate limits, optimize orchestrator, add caching
- **Fallback:** Launch com lower RPM target (80-100), scale later

❗ **Security vulnerabilities found**
- **Mitigation:** Fix before launch (blocker)
- **Fallback:** None - must fix

### Medium Risk
⚠️ **Audit logging overhead impacts latency**
- **Mitigation:** Async logging, connection pooling
- **Fallback:** Reduce audit verbosity

⚠️ **Health checks too slow**
- **Mitigation:** Parallel component checks, timeout limits
- **Fallback:** Simplified health check

### Low Risk
ℹ️ **PII detection false positives**
- **Mitigation:** Refine regex patterns, add whitelist
- **Impact:** Low (nice-to-have feature)

---

## Dependencies

### External Dependencies
- **Locust:** `pip install locust` (Story 9.6)
- **pip-audit:** `pip install pip-audit` (Story 9.7)

### Internal Dependencies
- Epic 0: PostgreSQL (Story 9.3)
- Epic 1: Orchestrator (all stories)
- Epic 2: Rate limiters (Story 9.5, 9.6)
- Epic 3: Providers (Story 9.4, 9.5)
- Epic 5: Metrics (Story 9.6 validation)

---

## Success Metrics

**Epic 9 is DONE when:**
- ✅ Audit logs capturing 100% of executions
- ✅ Health check shows all component statuses
- ✅ Load test validates 120+ RPM com >99% success
- ✅ Security checklist 100% validated
- ✅ Go-live procedure documented e reviewed
- ✅ All must-have tests passing (40+ tests)

**Optional Success:**
- ✅ PII detection working (nice-to-have)
- ✅ Provider status endpoint (nice-to-have)

---

## Next Steps

1. **Review & Approve Context** (você)
2. **Draft Story 9.3** (Audit Logging) - primeiro must-have
3. **Implement Story 9.3** (2-3 dias)
4. **Draft Story 9.4** (Health Checks)
5. **Continue sequence...**

---

**Context Status:** ✅ CONTEXTED - Ready for story drafting
**Estimated Epic Duration:** 5-7 days (must-haves only) or 7-9 days (all stories)
