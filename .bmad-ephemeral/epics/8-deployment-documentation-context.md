# Epic 8: Deployment & Documentation - Technical Context

**Epic:** Epic 8 - Deployment & Documentation
**Status:** In Progress
**Created:** 2025-11-13
**Dependencies:** Epics 0-7 (ALL COMPLETE)

---

## Epic Goal

Consolidate all Squad API components into a production-ready deployment system with comprehensive documentation, enabling one-command setup and professional-grade operational guides.

## Business Value

- **Reproducibility:** Deploy entire stack with `docker-compose up`
- **Onboarding:** New developers productive in <30 minutes
- **Operations:** Clear runbooks for deployment, troubleshooting, maintenance
- **Compliance:** Architecture decisions documented (ADRs)
- **API Discovery:** OpenAPI/Swagger for external integration
- **Quality Gate:** E2E tests validate full system before production

## Technical Context

### Current State (Post Epic 7)

**Infrastructure Ready:**
- ✅ Redis (Epic 0) - Conversation state, rate limiting
- ✅ PostgreSQL (Epic 0) - Future audit logs
- ✅ Prometheus (Epic 0) - Metrics collection
- ✅ Grafana (Epic 6) - 4 dashboards configured
- ✅ FastAPI (Epic 0) - Application server

**Application Complete:**
- ✅ Agent Transformation Engine (Epic 1) - 16 stories
- ✅ Rate Limiting Layer (Epic 2) - Multi-tier protection
- ✅ Provider Wrappers (Epic 3) - Groq, Cerebras, Gemini, OpenRouter
- ✅ Fallback & Resilience (Epic 4) - Auto-throttling, quality validation
- ✅ Observability (Epic 5) - Prometheus metrics, structured logging
- ✅ Monitoring (Epic 6) - Grafana dashboards, Slack alerts
- ✅ Configuration System (Epic 7) - YAML-driven, hot-reload

**Gaps for Epic 8:**
- ❌ Unified docker-compose.yaml (scattered across epics)
- ❌ README quick start guide
- ❌ Deployment runbook
- ❌ Troubleshooting runbook
- ❌ Architecture Decision Records (ADRs)
- ❌ OpenAPI/Swagger documentation
- ❌ End-to-end integration tests

### Target State (Post Epic 8)

**Single Command Deployment:**
```bash
git clone squad-api
cd squad-api
cp .env.example .env
# Edit .env with API keys
docker-compose up -d
# ✅ All services running, dashboards accessible
```

**Documentation Hierarchy:**
```
docs/
├── README.md                    # Quick start (5 min to running system)
├── configuration.md             # ✅ Already exists (Epic 7)
├── runbooks/
│   ├── deployment.md           # Deploy to dev/staging/prod
│   ├── troubleshooting.md      # Common issues + solutions
│   └── operations.md           # Daily operations guide
├── adrs/
│   ├── 001-fastapi-framework.md
│   ├── 002-redis-state-management.md
│   ├── 003-multi-provider-architecture.md
│   ├── 004-rate-limiting-strategy.md
│   └── ...
└── api/
    └── openapi.yaml            # Auto-generated from FastAPI
```

**E2E Test Coverage:**
- User journey: Chat with Mary → Fallback to Cerebras → Response received
- Rate limiting: Trigger 429 → Auto-throttle → Recovery
- Monitoring: Request → Metrics emitted → Dashboard updated
- Configuration: YAML change → Hot reload → New config applied

## Architecture Decisions for Epic 8

### AD8.1: Consolidated Docker Compose

**Context:**
- Currently have separate docker-compose files from Epic 0
- Services added incrementally (Redis, Postgres, Prometheus, Grafana)
- Need single source of truth

**Decision:**
- Create master `docker-compose.yaml` at root
- All services in one file with clear service separation
- Separate networks: `backend` (internal) and `frontend` (exposed)
- Health checks for all critical services
- Volume mounts for persistence (Redis, Postgres, Prometheus, Grafana)

**Structure:**
```yaml
version: '3.8'

networks:
  backend:
    driver: bridge
  frontend:
    driver: bridge

volumes:
  redis_data:
  postgres_data:
  prometheus_data:
  grafana_data:

services:
  redis:           # Port 6379 (backend only)
  postgres:        # Port 5432 (backend only)
  prometheus:      # Port 9090 (frontend)
  grafana:         # Port 3000 (frontend)
  squad-api:       # Port 8000 (frontend)
    depends_on:
      - redis
      - postgres
      - prometheus
```

### AD8.2: Documentation Strategy

**Context:**
- Need balance between comprehensive and maintainable
- Multiple audiences: developers, operators, executives

**Decision:**
- **README.md:** Quick start only (max 200 lines)
  - Prerequisites, installation, first request, troubleshooting
- **docs/runbooks/:** Operational procedures
  - Step-by-step guides with commands
  - Screenshots for Grafana dashboards
- **docs/adrs/:** Technical decisions with context
  - Template: Context, Decision, Consequences
  - Numbered chronologically (001, 002, ...)
- **docs/api/:** OpenAPI auto-generated
  - FastAPI generates schema automatically
  - Swagger UI at `/docs`

### AD8.3: E2E Testing Strategy

**Context:**
- Unit tests: 250+ tests across epics
- Integration tests: Provider-specific scenarios
- Need full system validation

**Decision:**
- **E2E Test Scope:** Critical user journeys only
  - Happy path: Chat request → Response
  - Resilience: Provider failure → Fallback
  - Monitoring: Request → Metrics → Dashboard
- **Test Environment:** Docker Compose with test config
  - Separate `docker-compose.test.yaml`
  - Stubbed LLM providers (no real API calls)
  - Fast teardown/setup (<10s)
- **Test Framework:** pytest with docker-compose plugin
  - Fixture: `docker_compose_up()`
  - Teardown: `docker_compose_down()`
- **CI/CD Ready:** Tests run in GitHub Actions
  - Prerequisite for Epic 9 (Production Readiness)

### AD8.4: Environment Management

**Context:**
- Different configs for dev/staging/prod
- Secrets management (API keys)

**Decision:**
- **Base:** `.env.example` with placeholders
- **Override Pattern:**
  - Dev: `.env.dev` (committed, fake keys)
  - Staging: `.env.staging` (secret, real keys)
  - Prod: `.env.prod` (secret, real keys)
- **Docker Compose:** `env_file` directive
  ```yaml
  squad-api:
    env_file:
      - .env
      - .env.${ENVIRONMENT:-dev}
  ```
- **Secrets:** Never commit real API keys
  - Use environment variables in CI/CD
  - Document key acquisition in README

## Story Breakdown

### Story 8.1: Docker Compose Complete Stack ⭐ START HERE

**Goal:** Consolidate all services into single docker-compose.yaml
**Value:** One-command deployment
**Effort:** 3 SP

**Deliverables:**
- `docker-compose.yaml` with all 5 services
- Health checks for each service
- Volume persistence
- Network isolation (backend/frontend)
- Service dependencies (depends_on)
- `.env.example` updated with all required vars

**Acceptance Criteria:**
- `docker-compose up -d` starts all services
- `docker-compose ps` shows all healthy
- Squad API accessible at http://localhost:8000
- Grafana accessible at http://localhost:3000
- Prometheus accessible at http://localhost:9090
- All services persist data across restarts

---

### Story 8.2: README Quick Start Guide

**Goal:** Enable new developers to run system in <5 minutes
**Value:** Fast onboarding
**Effort:** 2 SP

**Deliverables:**
- `README.md` with:
  - Project overview (2 paragraphs)
  - Prerequisites (Docker, Docker Compose, API keys)
  - Quick start (5 steps)
  - First request example (curl)
  - Link to full documentation
- Screenshots of Grafana dashboards

**Acceptance Criteria:**
- Following README takes <5 minutes
- All commands copy-pasteable
- Links to detailed docs work
- Troubleshooting section covers top 3 issues

---

### Story 8.3: Deployment Runbook

**Goal:** Step-by-step deployment guide for all environments
**Value:** Repeatable deployments
**Effort:** 3 SP

**Deliverables:**
- `docs/runbooks/deployment.md` with:
  - Environment setup (dev/staging/prod)
  - Pre-deployment checklist
  - Deployment steps
  - Rollback procedure
  - Post-deployment validation
  - Common issues + solutions

**Acceptance Criteria:**
- Can deploy to staging following runbook
- Rollback procedure tested
- Screenshots for each step
- Validation commands provided

---

### Story 8.4: Troubleshooting Runbook

**Goal:** Common issues and solutions in one place
**Value:** Reduce MTTR (Mean Time To Resolution)
**Effort:** 2 SP

**Deliverables:**
- `docs/runbooks/troubleshooting.md` with:
  - Service won't start
  - 429 rate limit errors
  - Provider failures
  - Configuration issues
  - Monitoring gaps
  - Performance degradation
- Each issue: Symptoms → Diagnosis → Solution

**Acceptance Criteria:**
- Top 10 issues documented
- Diagnostic commands provided
- Solutions tested
- Links to relevant logs

---

### Story 8.5: Architecture Decision Records (ADRs)

**Goal:** Document all major technical decisions with context
**Value:** Knowledge preservation, onboarding
**Effort:** 3 SP

**Deliverables:**
- `docs/adrs/README.md` (ADR index)
- 10-15 ADRs covering:
  - 001: FastAPI framework choice
  - 002: Redis for state management
  - 003: Multi-provider architecture
  - 004: Rate limiting strategy
  - 005: Prometheus for metrics
  - 006: Grafana for visualization
  - 007: YAML configuration system
  - 008: Hot-reload implementation
  - 009: Slack alerting strategy
  - 010: Docker Compose deployment
  - (+ others as needed)

**Acceptance Criteria:**
- Each ADR follows template (Context, Decision, Consequences)
- ADRs numbered chronologically
- Index with summaries
- Cross-references between ADRs

---

### Story 8.6: API Documentation (OpenAPI/Swagger)

**Goal:** Auto-generated, interactive API documentation
**Value:** External integrations, developer experience
**Effort:** 2 SP

**Deliverables:**
- FastAPI OpenAPI schema enhancement
- Comprehensive endpoint descriptions
- Request/response examples
- Authentication documentation
- Rate limiting documentation
- Error codes documentation
- Swagger UI at `/docs`
- ReDoc UI at `/redoc`

**Acceptance Criteria:**
- All endpoints documented
- Examples for each endpoint
- Try-it-out works in Swagger
- Schema validates against OpenAPI 3.0
- Export to `docs/api/openapi.yaml`

---

### Story 8.7: End-to-End Integration Test

**Goal:** Full system validation with realistic scenarios
**Value:** Confidence in deployments
**Effort:** 5 SP

**Deliverables:**
- `tests/e2e/test_full_system.py`
- Test scenarios:
  - Happy path: Chat with Mary → Response
  - Fallback: Primary fails → Fallback succeeds
  - Rate limiting: 429 triggered → Auto-throttle
  - Monitoring: Request → Metrics emitted
  - Configuration: Hot reload works
- `docker-compose.test.yaml` for test environment
- Stub providers for fast testing
- CI/CD integration (GitHub Actions)

**Acceptance Criteria:**
- All 5 scenarios pass
- Tests run in <60 seconds
- No external API calls (stubbed)
- Can run locally and in CI
- Coverage report includes E2E

---

## Dependencies Graph

```
Story 8.1 (Docker Compose)
    ↓
Story 8.2 (README) ← Story 8.3 (Deployment Runbook)
    ↓                      ↓
Story 8.4 (Troubleshooting)
    ↓
Story 8.5 (ADRs)
    ↓
Story 8.6 (API Docs) → Story 8.7 (E2E Tests)
```

**Critical Path:** 8.1 → 8.2 → 8.7
**Parallel Work:** 8.3, 8.4, 8.5, 8.6 can be done concurrently after 8.1

## Success Metrics

### Quantitative
- ✅ New developer onboarding: <30 minutes (README + Quick Start)
- ✅ Deployment time: <5 minutes (docker-compose up)
- ✅ Documentation coverage: 100% of features documented
- ✅ E2E test coverage: 5 critical scenarios
- ✅ ADRs: 10+ decisions documented

### Qualitative
- ✅ README is self-service (no questions needed)
- ✅ Runbooks are actionable (commands, not theory)
- ✅ ADRs explain "why" (context preserved)
- ✅ API docs enable integration (external teams)
- ✅ E2E tests give deployment confidence

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Docker Compose complexity | High | Start simple, add features incrementally |
| Documentation drift | Medium | Auto-generate where possible (OpenAPI) |
| E2E tests flaky | High | Use stubs, avoid external dependencies |
| Over-documentation | Low | Focus on user journeys, not exhaustive |
| ADRs incomplete | Medium | Template with required sections |

## Out of Scope (Epic 9)

- PII sanitization (Epic 9.1-9.2)
- Audit logging (Epic 9.3)
- Load testing (Epic 9.6)
- Security review (Epic 9.7)
- Production deployment (Epic 9.8)

## References

- Epic 0: Project Foundation (Infrastructure setup)
- Epic 5: Observability (Metrics foundation)
- Epic 6: Monitoring (Dashboards)
- Epic 7: Configuration System (YAML config, hot-reload)
- PRD: docs/PRD.md
- Epics: docs/epics.md

---

**Next Action:** Start Story 8.1 - Docker Compose Complete Stack
