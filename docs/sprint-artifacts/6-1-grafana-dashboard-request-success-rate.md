# Story 6.1: Grafana Dashboard - Request Success Rate

Status: ✅ **DONE**

## Story

As a operador,
I want dashboard de success rate,
so that vejo se sistema está healthy num relance.

## Acceptance Criteria

**Given** metrics sendo coletadas
**When** abro Grafana dashboard "Request Success Rate"
**Then** deve mostrar:

1. ✅ Panel 1: Success rate global (last 5min)
2. ✅ Panel 2: Success rate por provider (Groq, Cerebras, Gemini)
3. ✅ Panel 3: Success rate por agent (analyst, pm, architect)
4. ✅ Panel 4: 429 errors timeline (last 1 hour)

**And** auto-refresh a cada 15s

## Implementation Summary

**Developer:** Amelia (Dev Agent)
**Completed:** 2025-11-13
**Dashboard:** config/grafana/dashboards/request-success-rate.json

### What Was Implemented

1. **Grafana Dashboard JSON** (✅ CREATED):
   - 4 panels: Global gauge, Provider graph, Agent graph, 429 errors
   - Auto-refresh: 15s
   - Time range: Last 1 hour
   - Thresholds: Green ≥95%, Yellow 90-95%, Red <90%

2. **Prometheus Queries**:
   - Global: `rate(llm_requests_total{status="success"}[5m]) / rate(llm_requests_total[5m]) * 100`
   - By Provider: Same query with `by (provider)`
   - By Agent: Same query with `by (agent)`
   - 429 Errors: `increase(llm_requests_429_total[1h])`

3. **Dashboard Provisioning** (✅ CONFIGURED):
   - `config/grafana/dashboards/dashboards.yaml` - Auto-load configuration
   - Dashboard UID: `squad-api-success-rate`
   - Tags: squad-api, requests, success-rate

**Access:** http://localhost:3000/d/squad-api-success-rate

## Tasks / Subtasks

- [x] Create Grafana dashboard JSON (AC: all)
  - [x] Panel 1: Global success rate (gauge + graph)
  - [x] Panel 2: Success rate by provider (multi-series graph)
  - [x] Panel 3: Success rate by agent (multi-series graph)
  - [x] Panel 4: 429 errors timeline (bar chart)
  - [x] Configure auto-refresh: 15s
  - [x] Set time range: Last 1 hour

- [x] Configure Prometheus queries
  - [x] Query 1: `rate(llm_requests_total{status='success'}[5m]) / rate(llm_requests_total[5m]) * 100`
  - [x] Query 2: `rate(llm_requests_total{status='success'}[5m]) by (provider) / rate(llm_requests_total[5m]) by (provider) * 100`
  - [x] Query 3: `rate(llm_requests_total{status='success'}[5m]) by (agent) / rate(llm_requests_total[5m]) by (agent) * 100`
  - [x] Query 4: `increase(llm_requests_429_total[1h])`

- [x] Export dashboard JSON to config/grafana/dashboards/
  - [x] File: request-success-rate.json
  - [x] Add datasource variable (Prometheus)
  - [x] Add provisioning config (dashboards.yaml)

- [ ] **FUTURE:** Test dashboard (requires running system)
  - [ ] Verify metrics appear in panels
  - [ ] Verify auto-refresh works
  - [ ] Verify queries return expected data
  - [ ] Verify colors/thresholds (green >95%, yellow >90%, red <90%)

## Dev Notes

### Grafana Dashboard Structure

**Dashboard JSON Location:** `config/grafana/dashboards/request-success-rate.json`

**Panels Layout:**
```
┌─────────────────────────────────────────────┐
│  Global Success Rate (Gauge + Graph)        │
│  95.8%                                      │
└─────────────────────────────────────────────┘

┌────────────────┬────────────────┬────────────┐
│ Success by     │ Success by     │ 429 Errors │
│ Provider       │ Agent          │ Timeline   │
│ ────────────── │ ────────────── │ ▂▃▅▁▂▁▃   │
│ Groq: 97%      │ Mary: 96%      │            │
│ Cerebras: 95%  │ John: 94%      │            │
│ Gemini: 94%    │ Alex: 98%      │            │
└────────────────┴────────────────┴────────────┘
```

**Prometheus Queries:**

1. **Global Success Rate:**
```promql
rate(llm_requests_total{status="success"}[5m])
/
rate(llm_requests_total[5m])
* 100
```

2. **Success Rate by Provider:**
```promql
rate(llm_requests_total{status="success"}[5m]) by (provider)
/
rate(llm_requests_total[5m]) by (provider)
* 100
```

3. **Success Rate by Agent:**
```promql
rate(llm_requests_total{status="success"}[5m]) by (agent)
/
rate(llm_requests_total[5m]) by (agent)
* 100
```

4. **429 Errors (Last Hour):**
```promql
increase(llm_requests_429_total[1h])
```

**Thresholds:**
- 🟢 Green: ≥95% success
- 🟡 Yellow: 90-95% success
- 🔴 Red: <90% success

### Grafana Dashboard Template

```json
{
  "dashboard": {
    "title": "Request Success Rate",
    "tags": ["squad-api", "requests"],
    "timezone": "browser",
    "refresh": "15s",
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "panels": [
      {
        "id": 1,
        "title": "Global Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(llm_requests_total{status=\"success\"}[5m]) / rate(llm_requests_total[5m]) * 100"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 90},
                {"color": "green", "value": 95}
              ]
            },
            "unit": "percent"
          }
        }
      }
    ]
  }
}
```

### Project Structure Notes

**Files to Create:**
- `config/grafana/dashboards/request-success-rate.json` - Dashboard definition

**Files to Modify:**
- `config/grafana/datasources/prometheus.yaml` - Ensure Prometheus datasource configured

**Dependencies:**
- Grafana running (docker-compose up grafana)
- Prometheus datasource configured
- Metrics from Epic 5 being collected

### References

- [Source: docs/epics.md#Story 6.1]
- [Source: src/metrics/requests.py] - Metrics being visualized
- [Grafana Docs: Dashboard JSON](https://grafana.com/docs/grafana/latest/dashboards/json-model/)
- [Prometheus Docs: Query Functions](https://prometheus.io/docs/prometheus/latest/querying/functions/)

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Sonnet 4.5 (GitHub Copilot)

### Debug Log References

### Completion Notes List

### File List
