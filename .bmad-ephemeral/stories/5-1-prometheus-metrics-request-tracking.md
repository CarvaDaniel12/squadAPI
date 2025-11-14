# Story 5.1: Prometheus Metrics - Request Tracking

**Epic:** Epic 5 - Observability Foundation  
**Story ID:** 5.1  
**Status:** drafted  
**Drafted:** 2025-11-13  
**Assigned To:** Dev (Amelia)  
**Estimated Effort:** 2-3 hours

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## User Story

**As a** operador,  
**I want** métricas completas de requests,  
**So that** posso monitorar throughput e success rate.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Acceptance Criteria

**Given** Prometheus configurado  
**When** requests sendo executados  
**Then** deve expor:
- ✅ `llm_requests_total{provider, agent, status}` - Total requests
- ✅ `llm_requests_success{provider, agent}` - Successful requests  
- ✅ `llm_requests_failure{provider, agent, error_type}` - Failed requests
- ✅ `llm_requests_429_total{provider}` - Rate limit errors

**And** `/metrics` endpoint expõe em Prometheus format

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Technical Approach

**Files to Create:**
- `src/metrics/requests.py` - Request tracking metrics

**Metrics:**
1. `llm_requests_total` - Counter with labels [provider, agent, status]
2. `llm_requests_success` - Counter with labels [provider, agent]
3. `llm_requests_failure` - Counter with labels [provider, agent, error_type]
4. `llm_requests_429_total` - Counter with labels [provider]

**Integration Points:**
- Called from orchestrator.execute() (Story 5.5 will integrate)
- Exposed via `/metrics` endpoint (already exists from Epic 0)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Prerequisites

- ✅ Story 0.5 (Prometheus configured)
- ✅ Epic 2 (rate limiting metrics as reference)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Testing Strategy

**Unit Tests:**
- Test metric creation
- Test metric recording
- Test label combinations
- Test concurrent recording

**Integration Tests:**
- Test metrics exposed on /metrics endpoint
- Test Prometheus can scrape metrics

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Definition of Done

- [ ] Metrics file created and tested
- [ ] Unit tests passing
- [ ] Integration test with /metrics endpoint
- [ ] Code coverage >= 70%
- [ ] Documentation updated
- [ ] sprint-status.yaml updated (done)




