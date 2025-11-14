# Load Test Reports Directory

This directory contains generated reports from Locust load testing scenarios.

## Files

- `warm_up_stats_history.csv` - Stats from warm-up scenario (5 users, 1 minute)
- `sustained_load_stats_history.csv` - Stats from sustained load scenario (30 users, 5 minutes)
- `spike_scenario_stats_history.csv` - Stats from spike scenario (60 users, 2 minutes)

## Viewing Results

After running load tests with:

```bash
pytest tests/load/test_load_scenarios.py -m slow -v
```

CSV files will be generated here with detailed request statistics by endpoint.

## Metrics Columns (from Locust CSV)

- **Type**: Request type (GET, POST, etc.)
- **Name**: Endpoint path
- **Requests**: Total number of requests to this endpoint
- **Failures**: Number of failed requests
- **Median**: Median response time in milliseconds
- **95%**: 95th percentile response time (P95)
- **99%**: 99th percentile response time (P99)
- **Max**: Maximum response time observed
- **Content Size**: Average response size
- **Requests/s**: Throughput (requests per second)
