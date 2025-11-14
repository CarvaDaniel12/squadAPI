# Troubleshooting Runbook

**Version:** 1.0
**Last Updated:** 2025-11-13
**Owner:** Squad API Team
**Epic:** 8 - Deployment & Documentation

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Diagnostics](#quick-diagnostics)
3. [Provider Issues](#provider-issues)
4. [Rate Limiting Issues](#rate-limiting-issues)
5. [Fallback Chain Issues](#fallback-chain-issues)
6. [Memory & Resource Issues](#memory--resource-issues)
7. [Network & Connectivity Issues](#network--connectivity-issues)
8. [Database Issues](#database-issues)
9. [Configuration Issues](#configuration-issues)
10. [Performance Issues](#performance-issues)
11. [Monitoring & Metrics Issues](#monitoring--metrics-issues)
12. [Emergency Procedures](#emergency-procedures)

---

## Overview

This runbook provides step-by-step troubleshooting procedures for common Squad API issues. Each section follows the format:

- **Symptom:** What you observe
- **Diagnosis:** How to confirm the issue
- **Root Cause:** Common causes
- **Fix:** Step-by-step resolution
- **Prevention:** How to avoid in future

**Before troubleshooting:**
1. Check [Health Status](#quick-diagnostics) first
2. Review recent changes (deployments, config updates)
3. Check logs for error patterns
4. Verify monitoring dashboards in Grafana

---

## Quick Diagnostics

### System Health Check

```bash
# Run automated health check
./scripts/health_check.sh

# Manual checks
curl http://localhost:8000/health
curl http://localhost:9090/-/healthy
curl http://localhost:3000/api/health

# Check all container status
docker-compose ps

# View recent errors
docker-compose logs --tail=100 squad-api | grep -i error
```

### Key Metrics Dashboard

Open Grafana: http://localhost:3000

**Quick checks:**
- Request success rate: Should be >95%
- Provider health: All providers should be green
- Rate limit usage: Should be <80% of limits
- Memory usage: Should be <80% of container limits
- Error rate: Should be <5%

### Common Log Locations

```bash
# Squad API logs
docker-compose logs -f squad-api

# Redis logs
docker-compose logs -f redis

# PostgreSQL logs
docker-compose logs -f postgres

# Prometheus logs
docker-compose logs -f prometheus

# Grafana logs
docker-compose logs -f grafana

# Application logs (if volume mounted)
tail -f logs/squad-api.log
```

---

## Provider Issues

### Issue 1: Provider Returns 429 (Rate Limited)

**Symptom:**
```json
{
  "error": "Rate limit exceeded",
  "provider": "groq",
  "status_code": 429
}
```

**Diagnosis:**
```bash
# Check provider metrics in Grafana
# Navigate to: Provider Performance Dashboard → Rate Limit Status

# Check rate limit configuration
cat config/rate_limits.yaml | grep -A 10 "groq"

# Check recent provider requests
docker-compose logs squad-api | grep "groq" | tail -50
```

**Root Cause:**
- Exceeded provider's rate limits (requests/min or tokens/min)
- Auto-throttle not working correctly
- Rate limit configuration too aggressive

**Fix:**

```bash
# Option 1: Reduce rate limits in config/rate_limits.yaml
# Edit rate_limits.yaml
nano config/rate_limits.yaml

# Find provider section:
groq:
  requests_per_minute: 30  # Reduce from 60
  tokens_per_minute: 30000  # Reduce from 60000

# Save and wait for hot-reload (watchdog detects changes)
# Verify reload in logs:
docker-compose logs squad-api | grep "Configuration reloaded"

# Option 2: Enable fallback to other providers
# Verify fallback chain in config/agent_chains.yaml
cat config/agent_chains.yaml

# Option 3: Increase provider limits (if on paid tier)
# Update .env with new API key tier
```

**Prevention:**
- Monitor rate limit usage in Grafana dashboard
- Set alerts for >80% rate limit usage
- Use auto-throttle feature (enabled by default)
- Configure multiple providers for redundancy

---

### Issue 2: Provider Returns 401/403 (Authentication Failed)

**Symptom:**
```json
{
  "error": "Authentication failed",
  "provider": "gemini",
  "status_code": 401
}
```

**Diagnosis:**
```bash
# Check if API key is set
docker-compose exec squad-api env | grep GEMINI_API_KEY

# Test API key manually
curl -H "Authorization: Bearer $GEMINI_API_KEY" \
  https://generativelanguage.googleapis.com/v1/models

# Check logs for auth errors
docker-compose logs squad-api | grep -i "auth\|401\|403"
```

**Root Cause:**
- Invalid or expired API key
- API key not loaded from .env
- Incorrect API key format
- Provider API key rotated

**Fix:**

```bash
# Step 1: Verify API key in .env file
cat .env | grep GEMINI_API_KEY

# Step 2: Test key with provider's API
# For Gemini:
curl "https://generativelanguage.googleapis.com/v1/models?key=YOUR_API_KEY"

# Step 3: Update .env with valid key
nano .env
# Update: GEMINI_API_KEY=your_new_valid_key

# Step 4: Restart Squad API to reload .env
docker-compose restart squad-api

# Step 5: Verify fix
curl -X POST http://localhost:8000/v1/agents/code \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test", "conversation_id": "test-001"}'
```

**Prevention:**
- Set up API key expiration alerts
- Document API key rotation procedure
- Use secrets management system (AWS Secrets Manager, Vault)
- Test API keys in CI/CD pipeline

---

### Issue 3: Provider Timeout

**Symptom:**
```
TimeoutError: Provider groq timed out after 30s
```

**Diagnosis:**
```bash
# Check provider latency in Grafana
# Navigate to: Provider Performance → Latency (P95)

# Check network connectivity
docker-compose exec squad-api ping -c 3 api.groq.com

# Check recent timeouts
docker-compose logs squad-api | grep -i timeout | tail -20
```

**Root Cause:**
- Provider service degradation
- Network issues
- Large prompt causing slow inference
- Timeout configuration too aggressive

**Fix:**

```bash
# Option 1: Increase timeout in provider configuration
# Edit src/providers/groq_provider.py
nano src/providers/groq_provider.py

# Find timeout setting:
timeout = 30  # Increase to 60

# Restart container
docker-compose restart squad-api

# Option 2: Use fallback provider
# Verify fallback chain working:
docker-compose logs squad-api | grep "Falling back"

# Option 3: Check provider status page
# Groq: https://status.groq.com
# Gemini: https://status.cloud.google.com
```

**Prevention:**
- Monitor provider latency with Prometheus alerts
- Configure multiple providers for fallback
- Set reasonable timeout (30-60s)
- Use smaller prompts or streaming

---

## Rate Limiting Issues

### Issue 4: Requests Getting Throttled Unexpectedly

**Symptom:**
```
HTTP 429: Too Many Requests (internal rate limiter)
```

**Diagnosis:**
```bash
# Check current rate limit usage
curl http://localhost:8000/metrics | grep rate_limit

# Check rate limit configuration
cat config/rate_limits.yaml

# View rate limit metrics in Grafana
# Navigate to: Rate Limiting Dashboard → Current Usage

# Check sliding window state in Redis
docker-compose exec redis redis-cli KEYS "rate_limit:*"
docker-compose exec redis redis-cli GET "rate_limit:groq:requests"
```

**Root Cause:**
- Rate limits configured too low
- Burst traffic exceeding limits
- Sliding window not clearing properly
- Multiple clients sharing limits

**Fix:**

```bash
# Option 1: Increase rate limits
nano config/rate_limits.yaml

# Update limits:
groq:
  requests_per_minute: 100  # Increased from 60
  tokens_per_minute: 100000  # Increased from 60000

# Save (hot-reload will apply changes)

# Option 2: Clear rate limit state in Redis
docker-compose exec redis redis-cli FLUSHDB
# Warning: This clears all Redis data including conversation context

# Option 3: Adjust auto-throttle settings
# Edit src/rate_limit/auto_throttle.py
# Reduce throttle_factor or increase recovery_rate

# Verify fix
curl -X POST http://localhost:8000/v1/agents/code \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test", "conversation_id": "test-002"}'
```

**Prevention:**
- Set rate limits to 70-80% of provider limits
- Monitor rate limit usage with alerts
- Use auto-throttle to prevent hard limits
- Implement request queuing for burst traffic

---

### Issue 5: Auto-Throttle Not Working

**Symptom:**
- Hitting rate limits despite auto-throttle enabled
- No throttling logs in output

**Diagnosis:**
```bash
# Check auto-throttle configuration
grep -r "auto_throttle" config/

# Check logs for throttle events
docker-compose logs squad-api | grep -i throttle

# Verify auto-throttle is enabled
docker-compose exec squad-api python -c "from src.rate_limit.auto_throttle import AutoThrottle; print('Enabled')"
```

**Root Cause:**
- Auto-throttle not initialized
- Rate limiter not using auto-throttle wrapper
- Configuration error

**Fix:**

```bash
# Verify auto-throttle code is correct
cat src/rate_limit/auto_throttle.py

# Check rate limiter initialization
cat src/rate_limit/combined.py | grep -A 10 "AutoThrottle"

# Restart with debug logging
nano .env
# Set: LOG_LEVEL=DEBUG

docker-compose restart squad-api

# Monitor logs for throttle events
docker-compose logs -f squad-api | grep -i throttle
```

**Prevention:**
- Add unit tests for auto-throttle
- Monitor throttle events in Grafana
- Document auto-throttle configuration

---

## Fallback Chain Issues

### Issue 6: Fallback Not Triggering

**Symptom:**
- Request fails without trying fallback providers
- Only primary provider attempted

**Diagnosis:**
```bash
# Check fallback configuration
cat config/agent_chains.yaml

# Verify fallback chain for agent
cat config/agent_chains.yaml | grep -A 15 "code:"

# Check fallback orchestrator logs
docker-compose logs squad-api | grep -i "fallback\|falling back"

# Check provider health
curl http://localhost:8000/metrics | grep provider_health
```

**Root Cause:**
- Fallback chain not configured for agent
- Primary provider succeeding (no fallback needed)
- Fallback conditions not met
- Orchestrator not invoking fallback

**Fix:**

```bash
# Step 1: Verify fallback chain exists
nano config/agent_chains.yaml

# Ensure agent has fallback chain:
code:
  chains:
    - providers: ["groq", "cerebras", "gemini"]
      quality_check: true

# Step 2: Test fallback manually
# Temporarily disable primary provider by removing API key
nano .env
# Comment out: # GROQ_API_KEY=...

docker-compose restart squad-api

# Make request (should fall back to cerebras)
curl -X POST http://localhost:8000/v1/agents/code \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test", "conversation_id": "fallback-test"}'

# Check logs for fallback
docker-compose logs squad-api | grep -i "falling back"

# Step 3: Re-enable primary provider
nano .env
# Uncomment: GROQ_API_KEY=...

docker-compose restart squad-api
```

**Prevention:**
- Configure fallback chains for all agents
- Test fallback regularly (chaos engineering)
- Monitor fallback trigger rate in Grafana
- Set alerts for high fallback rate (>20%)

---

### Issue 7: Quality Check Failing All Responses

**Symptom:**
```
Quality check failed for all providers, no valid response
```

**Diagnosis:**
```bash
# Check quality check configuration
cat src/agents/quality.py

# View quality check logs
docker-compose logs squad-api | grep -i "quality"

# Check response format
docker-compose logs squad-api | tail -100 | grep "response"
```

**Root Cause:**
- Quality check criteria too strict
- All providers returning invalid format
- Quality check logic error

**Fix:**

```bash
# Option 1: Adjust quality check criteria
nano src/agents/quality.py

# Find quality_check function:
def quality_check(response: str) -> bool:
    # Relax criteria:
    if len(response) < 10:  # Was 50
        return False
    return True

# Restart
docker-compose restart squad-api

# Option 2: Disable quality check temporarily
nano config/agent_chains.yaml

# Set quality_check: false
code:
  chains:
    - providers: ["groq", "cerebras", "gemini"]
      quality_check: false  # Changed from true

# Save and test
```

**Prevention:**
- Define clear quality criteria
- Log quality check failures with reason
- Monitor quality check failure rate
- Add quality check unit tests

---

## Memory & Resource Issues

### Issue 8: Squad API Container OOM (Out of Memory)

**Symptom:**
```
Container squad-api exited with code 137 (OOM killed)
```

**Diagnosis:**
```bash
# Check container memory usage
docker stats squad-api --no-stream

# Check memory limit
docker inspect squad-api | grep -i memory

# View OOM events in logs
docker-compose logs squad-api | grep -i "killed\|oom"

# Check system memory
free -h
```

**Root Cause:**
- Memory limit too low
- Memory leak in application
- Large conversation contexts in Redis
- Too many concurrent requests

**Fix:**

```bash
# Option 1: Increase memory limit
nano docker-compose.yaml

# Find squad-api service:
squad-api:
  deploy:
    resources:
      limits:
        memory: 2G  # Increased from 1G

# Restart
docker-compose up -d squad-api

# Option 2: Clear conversation context in Redis
docker-compose exec redis redis-cli FLUSHDB

# Option 3: Reduce concurrency
# Check and reduce worker count in Dockerfile or uvicorn command

# Monitor memory usage
watch -n 5 'docker stats squad-api --no-stream'
```

**Prevention:**
- Set appropriate memory limits (2G+ for production)
- Monitor memory usage with Prometheus alerts
- Implement conversation context TTL in Redis
- Use memory profiling to detect leaks
- Limit max concurrent requests

---

### Issue 9: Redis Memory Limit Exceeded

**Symptom:**
```
Redis OOM error: maxmemory limit reached
```

**Diagnosis:**
```bash
# Check Redis memory usage
docker-compose exec redis redis-cli INFO memory

# Check maxmemory configuration
docker-compose exec redis redis-cli CONFIG GET maxmemory

# Count keys
docker-compose exec redis redis-cli DBSIZE
```

**Root Cause:**
- Too many conversation contexts stored
- No eviction policy set
- Memory limit too low

**Fix:**

```bash
# Option 1: Increase Redis memory limit
nano docker-compose.yaml

# Find redis service:
redis:
  command: redis-server --maxmemory 512mb  # Increased from 256mb

# Restart
docker-compose restart redis

# Option 2: Clear old conversation contexts
docker-compose exec redis redis-cli --scan --pattern "conversation:*" | \
  head -100 | xargs docker-compose exec redis redis-cli DEL

# Option 3: Set TTL on conversation keys
# Update conversation storage code to add TTL:
# redis.setex(f"conversation:{id}", 3600, data)  # 1 hour TTL
```

**Prevention:**
- Set appropriate maxmemory (512MB-1GB)
- Configure eviction policy (allkeys-lru)
- Implement TTL on conversation contexts (1-24 hours)
- Monitor Redis memory in Grafana

---

## Network & Connectivity Issues

### Issue 10: Squad API Can't Connect to Redis

**Symptom:**
```
ConnectionError: Error connecting to Redis at redis:6379
```

**Diagnosis:**
```bash
# Check Redis container status
docker-compose ps redis

# Check Redis health
docker-compose exec redis redis-cli PING

# Test network connectivity
docker-compose exec squad-api ping -c 3 redis

# Check network configuration
docker network inspect squad-api_backend
```

**Root Cause:**
- Redis container not running
- Network misconfiguration
- Redis port not exposed
- DNS resolution failure

**Fix:**

```bash
# Step 1: Verify Redis is running
docker-compose up -d redis

# Step 2: Check Redis health
docker-compose exec redis redis-cli PING
# Expected: PONG

# Step 3: Test connectivity from Squad API
docker-compose exec squad-api nc -zv redis 6379

# Step 4: Verify REDIS_URL environment variable
docker-compose exec squad-api env | grep REDIS_URL
# Expected: redis://redis:6379

# Step 5: Restart both services
docker-compose restart redis squad-api

# Step 6: Verify connection
curl http://localhost:8000/health
```

**Prevention:**
- Use Docker Compose healthcheck dependencies
- Monitor Redis connectivity with Prometheus
- Set connection retry logic in application
- Document network topology

---

### Issue 11: External Provider API Not Reachable

**Symptom:**
```
ConnectionError: Failed to connect to api.groq.com
```

**Diagnosis:**
```bash
# Test internet connectivity from container
docker-compose exec squad-api ping -c 3 8.8.8.8

# Test DNS resolution
docker-compose exec squad-api nslookup api.groq.com

# Test HTTPS connection
docker-compose exec squad-api curl -I https://api.groq.com

# Check firewall rules
sudo iptables -L -n | grep 443
```

**Root Cause:**
- Firewall blocking outbound HTTPS (port 443)
- DNS resolution failure
- Provider API down
- Proxy configuration required

**Fix:**

```bash
# Option 1: Check firewall rules
sudo ufw status
# Allow HTTPS if blocked:
sudo ufw allow out 443/tcp

# Option 2: Configure DNS
# Edit Docker daemon.json
sudo nano /etc/docker/daemon.json

# Add DNS servers:
{
  "dns": ["8.8.8.8", "8.8.4.4"]
}

# Restart Docker
sudo systemctl restart docker

# Option 3: Configure HTTP proxy (if required)
nano docker-compose.yaml

# Add to squad-api service:
environment:
  HTTP_PROXY: http://proxy.example.com:8080
  HTTPS_PROXY: http://proxy.example.com:8080

# Restart
docker-compose up -d squad-api
```

**Prevention:**
- Document network requirements in deployment guide
- Test external connectivity in health checks
- Set up network monitoring
- Use multiple DNS servers

---

## Database Issues

### Issue 12: PostgreSQL Connection Failed

**Symptom:**
```
OperationalError: could not connect to server: Connection refused
```

**Diagnosis:**
```bash
# Check PostgreSQL status
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres | tail -50

# Test connection from Squad API
docker-compose exec squad-api nc -zv postgres 5432

# Verify DATABASE_URL
docker-compose exec squad-api env | grep DATABASE_URL
```

**Root Cause:**
- PostgreSQL container not running
- Incorrect DATABASE_URL
- PostgreSQL not accepting connections
- Network issue

**Fix:**

```bash
# Step 1: Start PostgreSQL
docker-compose up -d postgres

# Step 2: Wait for healthy status
docker-compose ps postgres
# Wait until status shows "(healthy)"

# Step 3: Test connection manually
docker-compose exec postgres psql -U squad -d squad_api -c "SELECT 1;"

# Step 4: Verify DATABASE_URL format
cat .env | grep DATABASE_URL
# Expected: postgresql://squad:password@postgres:5432/squad_api

# Step 5: Restart Squad API
docker-compose restart squad-api

# Step 6: Verify
curl http://localhost:8000/health
```

**Prevention:**
- Use depends_on with health check in docker-compose
- Monitor PostgreSQL connectivity
- Implement connection retry logic
- Set connection timeout

---

### Issue 13: PostgreSQL Disk Full

**Symptom:**
```
ERROR: could not extend file: No space left on device
```

**Diagnosis:**
```bash
# Check disk usage
df -h

# Check PostgreSQL data directory size
docker-compose exec postgres du -sh /var/lib/postgresql/data

# Check largest tables
docker-compose exec postgres psql -U squad -d squad_api -c "
  SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
  FROM pg_tables
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
  LIMIT 10;
"
```

**Root Cause:**
- Rate limit logs growing unbounded
- No data retention policy
- Insufficient disk allocation

**Fix:**

```bash
# Option 1: Clean up old data
docker-compose exec postgres psql -U squad -d squad_api -c "
  DELETE FROM rate_limit_logs WHERE created_at < NOW() - INTERVAL '7 days';
  VACUUM FULL;
"

# Option 2: Increase disk allocation (VM level)
# Resize disk, then:
sudo resize2fs /dev/sda1

# Option 3: Implement data retention policy
# Add cron job to clean old data:
sudo crontab -e

# Add daily cleanup at 3 AM:
0 3 * * * docker-compose -f /opt/squad-api/docker-compose.yaml exec -T postgres psql -U squad -d squad_api -c "DELETE FROM rate_limit_logs WHERE created_at < NOW() - INTERVAL '30 days';" >> /var/log/db-cleanup.log 2>&1
```

**Prevention:**
- Implement data retention policy (30-90 days)
- Monitor disk usage with alerts (<80% full)
- Use PostgreSQL partitioning for large tables
- Schedule regular VACUUM operations

---

## Configuration Issues

### Issue 14: Configuration Hot-Reload Not Working

**Symptom:**
- Changes to config/*.yaml files not applied
- No "Configuration reloaded" logs

**Diagnosis:**
```bash
# Check watchdog is running
docker-compose logs squad-api | grep -i "watchdog\|watcher"

# Verify file changes detected
# Make a test change:
echo "# test" >> config/rate_limits.yaml

# Watch logs for reload
docker-compose logs -f squad-api | grep -i "reload"

# Check file permissions
ls -la config/
```

**Root Cause:**
- Watchdog not started
- File volume not mounted correctly
- File permissions issue
- Watchdog crashed

**Fix:**

```bash
# Step 1: Verify config volume mounted
docker inspect squad-api | grep -A 10 "Mounts"

# Step 2: Check watchdog initialization
docker-compose logs squad-api | grep -i "ConfigWatcher"

# Step 3: Restart Squad API
docker-compose restart squad-api

# Step 4: Test hot-reload
nano config/rate_limits.yaml
# Make a change, save

# Watch for reload
docker-compose logs -f squad-api | grep "Configuration reloaded"

# Step 5: If still not working, manual restart
docker-compose restart squad-api
```

**Prevention:**
- Add watchdog health monitoring
- Log watchdog events at INFO level
- Test hot-reload in CI/CD
- Document which files support hot-reload

---

### Issue 15: Invalid YAML Configuration

**Symptom:**
```
YAMLError: mapping values are not allowed here
```

**Diagnosis:**
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/rate_limits.yaml'))"

# Check for common YAML errors
cat config/rate_limits.yaml | grep -E "^\s*-\s+[a-z]"  # List vs dict confusion
```

**Root Cause:**
- YAML syntax error (indentation, missing colon, etc.)
- Invalid configuration values
- Schema validation failure

**Fix:**

```bash
# Step 1: Identify problematic file
docker-compose logs squad-api | grep -i "yaml"

# Step 2: Validate YAML syntax
python -c "
import yaml
try:
    with open('config/rate_limits.yaml') as f:
        yaml.safe_load(f)
    print('✓ Valid YAML')
except yaml.YAMLError as e:
    print(f'✗ Invalid YAML: {e}')
"

# Step 3: Fix syntax error
nano config/rate_limits.yaml
# Common fixes:
# - Check indentation (use 2 spaces, not tabs)
# - Ensure colons have space after them
# - Quote strings with special characters

# Step 4: Validate fix
python -c "import yaml; yaml.safe_load(open('config/rate_limits.yaml'))"

# Step 5: Restart or wait for hot-reload
docker-compose restart squad-api
```

**Prevention:**
- Use YAML linter in CI/CD
- Add schema validation for config files
- Provide config templates
- Document configuration format

---

## Performance Issues

### Issue 16: High Latency (>2s per request)

**Symptom:**
- API requests taking >2 seconds
- P95 latency high in Grafana

**Diagnosis:**
```bash
# Check latency metrics
curl http://localhost:8000/metrics | grep duration

# Check provider latency in Grafana
# Navigate to: Provider Performance → Latency Heatmap

# Profile a request
time curl -X POST http://localhost:8000/v1/agents/code \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test", "conversation_id": "perf-test"}'

# Check for slow queries
docker-compose logs postgres | grep "duration:"
```

**Root Cause:**
- Slow provider response
- Database query slow
- Large conversation context
- Resource contention

**Fix:**

```bash
# Option 1: Optimize provider selection
# Use faster providers (Groq, Cerebras) as primary
nano config/agent_routing.yaml

# Option 2: Add database indexes
docker-compose exec postgres psql -U squad -d squad_api -c "
  CREATE INDEX IF NOT EXISTS idx_rate_limit_logs_created_at ON rate_limit_logs(created_at);
  CREATE INDEX IF NOT EXISTS idx_rate_limit_logs_provider ON rate_limit_logs(provider);
"

# Option 3: Reduce conversation context size
# Limit to last 10 messages instead of full history

# Option 4: Increase resources
nano docker-compose.yaml
# Increase CPU/memory for squad-api

docker-compose up -d squad-api
```

**Prevention:**
- Monitor P95/P99 latency with alerts
- Use caching for frequent requests
- Optimize database queries
- Load test regularly

---

### Issue 17: High CPU Usage

**Symptom:**
- Container CPU at 90-100%
- Slow response times

**Diagnosis:**
```bash
# Check CPU usage
docker stats squad-api --no-stream

# Check top processes in container
docker-compose exec squad-api top

# Check request volume
curl http://localhost:8000/metrics | grep requests_total
```

**Root Cause:**
- Too many concurrent requests
- CPU-intensive operations (JSON parsing, regex)
- Insufficient CPU allocation
- Infinite loop or bug

**Fix:**

```bash
# Option 1: Increase CPU limit
nano docker-compose.yaml

squad-api:
  deploy:
    resources:
      limits:
        cpus: '4'  # Increased from 2

docker-compose up -d squad-api

# Option 2: Reduce concurrency
# Limit uvicorn workers or add rate limiting

# Option 3: Profile CPU usage
docker-compose exec squad-api pip install py-spy
docker-compose exec squad-api py-spy top --pid 1

# Identify hot code paths and optimize
```

**Prevention:**
- Set CPU limits appropriately
- Monitor CPU usage with alerts
- Profile code regularly
- Load test before production

---

## Monitoring & Metrics Issues

### Issue 18: Prometheus Not Scraping Metrics

**Symptom:**
- No data in Grafana dashboards
- Prometheus targets showing "DOWN"

**Diagnosis:**
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq

# Or open in browser:
# http://localhost:9090/targets

# Check Squad API metrics endpoint
curl http://localhost:8000/metrics

# Check Prometheus logs
docker-compose logs prometheus | grep -i error
```

**Root Cause:**
- Squad API not exposing metrics endpoint
- Prometheus config incorrect
- Network connectivity issue
- Metrics endpoint authentication required

**Fix:**

```bash
# Step 1: Verify metrics endpoint works
curl http://localhost:8000/metrics
# Should return Prometheus format metrics

# Step 2: Check Prometheus configuration
cat config/prometheus.yml

# Ensure scrape config exists:
scrape_configs:
  - job_name: 'squad-api'
    static_configs:
      - targets: ['squad-api:8000']

# Step 3: Reload Prometheus config
curl -X POST http://localhost:9090/-/reload

# Step 4: Verify target is UP
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[0].health'
# Expected: "up"

# Step 5: Restart Prometheus if needed
docker-compose restart prometheus
```

**Prevention:**
- Add health checks for Prometheus scraping
- Monitor Prometheus targets with alerts
- Test metrics endpoint in CI/CD
- Document metrics format

---

### Issue 19: Grafana Dashboards Not Loading

**Symptom:**
- Grafana shows "No data" or "N/A"
- Dashboard panels empty

**Diagnosis:**
```bash
# Check Grafana logs
docker-compose logs grafana | grep -i error

# Check Prometheus datasource
# Open: http://localhost:3000/datasources
# Test connection to Prometheus

# Query Prometheus directly
curl 'http://localhost:9090/api/v1/query?query=up'

# Check dashboard JSON
ls -la config/grafana/dashboards/
```

**Root Cause:**
- Prometheus datasource not configured
- Dashboard queries incorrect
- Time range issue
- No data in Prometheus yet

**Fix:**

```bash
# Step 1: Verify Prometheus datasource
# Login to Grafana: http://localhost:3000
# Navigate to: Configuration → Data Sources
# Click Prometheus
# Click "Test" button
# Should show: "Data source is working"

# Step 2: Check if Prometheus has data
curl 'http://localhost:9090/api/v1/query?query=squad_api_requests_total'

# Step 3: Verify dashboard provisioning
ls -la config/grafana/dashboards/

# Step 4: Re-import dashboard
# In Grafana: Dashboards → Import
# Upload: config/grafana/dashboards/provider-performance.json

# Step 5: Adjust time range
# In Grafana dashboard, set time range to "Last 1 hour"
```

**Prevention:**
- Use Grafana dashboard provisioning
- Test dashboards after deployment
- Document dashboard queries
- Add sample data for testing

---

## Emergency Procedures

### Emergency 1: Complete Service Outage

**Symptoms:**
- All requests failing
- Health endpoint down
- Multiple containers crashed

**Immediate Actions:**

```bash
# 1. Stop all services
docker-compose down

# 2. Check system resources
df -h  # Disk space
free -h  # Memory
top  # CPU

# 3. Review recent changes
git log -5 --oneline

# 4. Start services one by one
docker-compose up -d redis
sleep 5
docker-compose up -d postgres
sleep 10
docker-compose up -d prometheus
sleep 5
docker-compose up -d grafana
sleep 5
docker-compose up -d squad-api

# 5. Monitor health
watch -n 2 'docker-compose ps'

# 6. Check logs for errors
docker-compose logs --tail=100
```

**Rollback Procedure:**

```bash
# Rollback to last known good version
git log --oneline | head -10
git checkout <last-good-commit>

docker-compose down
docker-compose up -d

# Verify
./scripts/health_check.sh
```

---

### Emergency 2: Data Corruption

**Symptoms:**
- Database errors
- Redis command failures
- Inconsistent data

**Immediate Actions:**

```bash
# 1. Stop Squad API to prevent further writes
docker-compose stop squad-api

# 2. Backup current state
./scripts/backup.sh

# 3. Assess damage
# Check PostgreSQL
docker-compose exec postgres psql -U squad -d squad_api -c "SELECT COUNT(*) FROM rate_limit_logs;"

# Check Redis
docker-compose exec redis redis-cli DBSIZE

# 4. Restore from backup
# See deployment.md Backup & Recovery section

# 5. Restart services
docker-compose up -d

# 6. Verify
./scripts/health_check.sh
```

---

### Emergency 3: Security Breach

**Symptoms:**
- Unauthorized access attempts
- API keys compromised
- Unusual traffic patterns

**Immediate Actions:**

```bash
# 1. Isolate system
docker-compose down

# 2. Rotate all API keys
# Update .env with new keys:
nano .env

# Change all provider API keys
# Change GRAFANA_PASSWORD
# Change POSTGRES_PASSWORD

# 3. Review logs for breach timeline
docker-compose logs > breach-logs.txt

# 4. Notify security team

# 5. Restart with new keys
docker-compose up -d

# 6. Monitor for suspicious activity
docker-compose logs -f | grep -i "error\|401\|403"
```

---

## Common Error Codes

| Code | Meaning | Common Cause | Fix |
|------|---------|--------------|-----|
| 429 | Too Many Requests | Rate limit exceeded | Reduce request rate or increase limits |
| 401 | Unauthorized | Invalid API key | Check .env and provider keys |
| 403 | Forbidden | API key lacks permissions | Upgrade provider tier or change key |
| 500 | Internal Server Error | Application crash | Check logs, restart container |
| 502 | Bad Gateway | Reverse proxy issue | Check nginx/traefik config |
| 503 | Service Unavailable | Service down | Check container status |
| 504 | Gateway Timeout | Request timeout | Increase timeout or check provider |

---

## Support Escalation

If issue persists after following this runbook:

1. **Gather diagnostics:**
   ```bash
   # Collect logs
   docker-compose logs > squad-api-logs.txt

   # Collect metrics
   curl http://localhost:8000/metrics > metrics.txt

   # Collect system info
   docker-compose ps > containers.txt
   docker stats --no-stream > resources.txt
   ```

2. **Create GitHub issue:**
   - Title: `[BUG] Brief description`
   - Include: logs, metrics, steps to reproduce
   - Link to relevant documentation

3. **Contact support:**
   - Email: support@squad-api.example.com
   - Slack: #squad-api-support
   - On-call: PagerDuty escalation

---

## References

- [Deployment Runbook](deployment.md)
- [Architecture Documentation](../architecture.md)
- [API Documentation](http://localhost:8000/docs)
- [Grafana Dashboards](http://localhost:3000)
- [Prometheus Queries](http://localhost:9090)

---

**Last Updated:** 2025-11-13
**Version:** 1.0
**Maintainer:** Squad API Team
