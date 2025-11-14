# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records documenting significant technical decisions made during Squad API development.

## ADR Format

Each ADR follows this structure:

- **Title:** Short descriptive title
- **Status:** Proposed | Accepted | Deprecated | Superseded
- **Context:** Background and problem statement
- **Decision:** What we decided
- **Consequences:** Positive and negative outcomes
- **Alternatives Considered:** Other options evaluated

## ADR Index

### Epic 0: Infrastructure Foundation

- [ADR-001: Docker Compose for Local Development](001-docker-compose-infrastructure.md)
- [ADR-002: Redis for Conversation Context Storage](002-redis-conversation-storage.md)
- [ADR-003: PostgreSQL for Rate Limit State Persistence](003-postgres-rate-limit-state.md)

### Epic 1: Agent Transformation

- [ADR-004: Agent Routing Strategy](004-agent-routing-strategy.md)
- [ADR-005: YAML-Based Agent Configuration](005-yaml-agent-configuration.md)

### Epic 2: Rate Limiting

- [ADR-006: Combined Rate Limiter Architecture](006-combined-rate-limiter.md)
- [ADR-007: Auto-Throttle Implementation](007-auto-throttle-implementation.md)

### Epic 3: Provider Distribution

- [ADR-008: Provider Factory Pattern](008-provider-factory-pattern.md)
- [ADR-009: Provider-Specific Rate Limits](009-provider-specific-rate-limits.md)

### Epic 4: Intelligent Fallback

- [ADR-010: Fallback Chain Design](010-fallback-chain-design.md)
- [ADR-011: Quality Verification System](011-quality-verification.md)

### Epic 5: Observability

- [ADR-012: Prometheus for Metrics](012-prometheus-metrics.md)

### Epic 6: Real-Time Monitoring

- [ADR-013: Grafana Dashboard Strategy](013-grafana-dashboards.md)

### Epic 7: Configuration System

- [ADR-014: Hot-Reload with Watchdog](014-hot-reload-watchdog.md)

### Epic 8: Deployment & Documentation

- [ADR-015: Documentation Structure](015-documentation-structure.md)

---

## How to Use ADRs

**When making a significant technical decision:**

1. Create new ADR file: `NNN-short-title.md`
2. Fill in ADR template (see below)
3. Discuss with team
4. Mark as "Accepted" when approved
5. Update this index

**ADR Template:**

```markdown
# ADR-NNN: Title

**Status:** Proposed
**Date:** YYYY-MM-DD
**Epic:** N - Epic Name
**Story:** N.N - Story Name

## Context

Describe the problem, background, and why a decision is needed.

## Decision

Describe what we decided to do.

## Consequences

### Positive

- List positive outcomes

### Negative

- List negative outcomes or trade-offs

## Alternatives Considered

1. **Alternative 1:** Description and why rejected
2. **Alternative 2:** Description and why rejected

## References

- Links to relevant docs, PRs, issues
```

---

**Last Updated:** 2025-11-13
**Epic:** 8 - Deployment & Documentation
