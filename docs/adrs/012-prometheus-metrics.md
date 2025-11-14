# ADR-012: Prometheus for Metrics

**Status:** Accepted
**Date:** 2025-11-13
**Epic:** 5 - Observability
**Story:** 5.1 - Prometheus Integration

## Context

Squad API needs metrics for:
- Request volume and latency
- Provider health and performance
- Rate limit usage
- Fallback chain activity
- System resource utilization

**Requirements:**
1. Low overhead (<5ms per request)
2. Prometheus-compatible format
3. Multi-dimensional labels (provider, agent, status)
4. Historical data (30+ days retention)

## Decision

Use **Prometheus v2.48.0** with `prometheus-client` Python library:

```python
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
requests_total = Counter(
    'squad_api_requests_total',
    'Total requests',
    ['agent', 'provider', 'status']
)

# Latency metrics
request_duration = Histogram(
    'squad_api_request_duration_seconds',
    'Request duration',
    ['agent', 'provider']
)

# Rate limit metrics
rate_limit_usage = Gauge(
    'squad_api_rate_limit_usage',
    'Rate limit usage',
    ['provider', 'type']
)
```

## Consequences

### Positive

- ✅ **Industry standard:** Wide ecosystem support
- ✅ **Low overhead:** <2ms per metric update
- ✅ **Powerful queries:** PromQL for complex analysis
- ✅ **Alerting:** Built-in alert manager

### Negative

- ❌ **Pull-based:** Requires scrape configuration
- ❌ **Limited UI:** Need Grafana for visualization

## References

- [src/metrics/requests.py](../../src/metrics/requests.py)
- [config/prometheus.yml](../../config/prometheus.yml)
