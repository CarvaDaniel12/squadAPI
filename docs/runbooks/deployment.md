# Deployment Runbook

**Version:** 1.0
**Last Updated:** 2025-11-13
**Owner:** Squad API Team
**Epic:** 8 - Deployment & Documentation

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Production Deployment](#production-deployment)
5. [Health Verification](#health-verification)
6. [Rollback Procedures](#rollback-procedures)
7. [Scaling](#scaling)
8. [Backup & Recovery](#backup--recovery)
9. [Security Checklist](#security-checklist)
10. [Monitoring Setup](#monitoring-setup)

---

## Overview

This runbook covers deploying Squad API to production environments. Squad API is a stateful service requiring:
- **Redis:** Conversation context storage
- **PostgreSQL:** Rate limit state persistence
- **Prometheus:** Metrics collection
- **Grafana:** Metrics visualization

Deployment target: Docker Compose on single VM or Docker Swarm for multi-node.

**Deployment Modes:**
- **Development:** `docker-compose.yaml` with debug settings
- **Production:** `docker-compose.prod.yaml` with resource limits, secrets management

---

## Prerequisites

### Infrastructure Requirements

- [ ] **Compute:**
  - VM: 4 vCPU, 8GB RAM minimum (16GB recommended)
  - OS: Ubuntu 22.04 LTS, Debian 11+, or RHEL 8+
  - Disk: 50GB SSD (100GB recommended for logs/metrics retention)

- [ ] **Network:**
  - Static IP or DNS A record for Squad API
  - Ports open: 8000 (API), 3000 (Grafana), 9090 (Prometheus - internal only)
  - Firewall rules configured
  - SSL/TLS certificate (Let's Encrypt recommended)

- [ ] **Software:**
  - Docker Engine 20.10+ ([Install Guide](https://docs.docker.com/engine/install/))
  - Docker Compose 2.x+ (included with Docker Desktop)
  - Git 2.30+
  - (Optional) Nginx or Traefik for reverse proxy

### API Keys

- [ ] **LLM Providers:** At least 2 providers configured for fallback
  - Groq API key ([Get key](https://console.groq.com/keys))
  - Cerebras API key ([Get key](https://cloud.cerebras.ai/))
  - Gemini API key ([Get key](https://aistudio.google.com/apikey))
  - OpenRouter API key ([Get key](https://openrouter.ai/keys))
  - Together AI API key (optional) ([Get key](https://api.together.xyz/settings/api-keys))

- [ ] **Observability (Optional):**
  - Slack webhook URL for alerts ([Create webhook](https://api.slack.com/messaging/webhooks))

### Access Requirements

- [ ] SSH access to production VM
- [ ] Sudo/root privileges for Docker installation
- [ ] Git repository access (if private)
- [ ] Secrets management system (AWS Secrets Manager, HashiCorp Vault, etc.)

---

## Environment Setup

### Step 1: Clone Repository

```bash
# SSH to production VM
ssh user@production-vm.example.com

# Clone repository
cd /opt
sudo git clone https://github.com/your-org/squad-api.git
cd squad-api

# Checkout stable release (tag)
git checkout v1.0.0  # Replace with latest stable tag
```

### Step 2: Configure Environment Variables

**Production .env File:**

```bash
# Copy template
sudo cp .env.example .env.production

# Edit with production values
sudo nano .env.production
```

**Required Variables:**

```bash
# === Database Configuration ===
POSTGRES_PASSWORD=<STRONG_PASSWORD_HERE>  # Generate: openssl rand -base64 32

# === Grafana Configuration ===
GRAFANA_PASSWORD=<STRONG_PASSWORD_HERE>  # Change from default 'admin'

# === LLM Provider API Keys ===
GROQ_API_KEY=gsk_<your_production_key>
CEREBRAS_API_KEY=<your_production_key>
GEMINI_API_KEY=<your_production_key>
OPENROUTER_API_KEY=<your_production_key>
TOGETHER_API_KEY=<your_production_key>  # Optional

# === Slack Alerts ===
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/<your_webhook>
SLACK_ALERTS_ENABLED=true

# === Application Configuration ===
LOG_LEVEL=INFO  # Use INFO or WARNING in production (not DEBUG)
ENVIRONMENT=production

# === Internal URLs (auto-configured by docker-compose) ===
REDIS_URL=redis://redis:6379
DATABASE_URL=postgresql://squad:${POSTGRES_PASSWORD}@postgres:5432/squad_api
```

**Security Best Practices:**

```bash
# Set restrictive permissions on .env.production
sudo chmod 600 .env.production
sudo chown root:root .env.production

# Verify no secrets in git history
git log --all -- .env.production  # Should be empty
```

### Step 3: Production Docker Compose Configuration

**Create `docker-compose.prod.yaml`:**

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: squad-redis-prod
    restart: unless-stopped
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    networks:
      - backend
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 5s
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

  postgres:
    image: postgres:15-alpine
    container_name: squad-postgres-prod
    restart: unless-stopped
    environment:
      POSTGRES_DB: squad_api
      POSTGRES_USER: squad
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=C"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U squad -d squad_api"]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 10s
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '1'
          memory: 512M

  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: squad-prometheus-prod
    restart: unless-stopped
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=90d'  # 90 days retention in production
      - '--web.enable-lifecycle'
    networks:
      - backend
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:9090/-/healthy"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  grafana:
    image: grafana/grafana:10.2.2
    container_name: squad-grafana-prod
    restart: unless-stopped
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
      GF_SECURITY_ADMIN_USER: admin
      GF_USERS_ALLOW_SIGN_UP: "false"
      GF_ANALYTICS_REPORTING_ENABLED: "false"
      GF_ANALYTICS_CHECK_FOR_UPDATES: "false"
      GF_SERVER_ROOT_URL: https://grafana.example.com  # Change to your domain
      GF_INSTALL_PLUGINS: ""  # Add plugins if needed
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./config/grafana/datasources:/etc/grafana/provisioning/datasources:ro
    networks:
      - frontend
    ports:
      - "3000:3000"  # Use reverse proxy in production
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  squad-api:
    build:
      context: .
      dockerfile: Dockerfile
    image: squad-api:${VERSION:-latest}
    container_name: squad-api-prod
    restart: unless-stopped
    environment:
      GROQ_API_KEY: ${GROQ_API_KEY}
      CEREBRAS_API_KEY: ${CEREBRAS_API_KEY}
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
      TOGETHER_API_KEY: ${TOGETHER_API_KEY}
      SLACK_WEBHOOK_URL: ${SLACK_WEBHOOK_URL}
      SLACK_ALERTS_ENABLED: ${SLACK_ALERTS_ENABLED}
      REDIS_URL: ${REDIS_URL}
      DATABASE_URL: ${DATABASE_URL}
      LOG_LEVEL: ${LOG_LEVEL}
      ENVIRONMENT: ${ENVIRONMENT}
    volumes:
      - ./config/providers.yaml:/app/config/providers.yaml:ro
      - ./config/rate_limits.yaml:/app/config/rate_limits.yaml:ro
      - ./config/agent_routing.yaml:/app/config/agent_routing.yaml:ro
      - ./config/agent_chains.yaml:/app/config/agent_chains.yaml:ro
      - ./src/config/.bmad:/app/src/config/.bmad:ro
      - logs:/app/logs
    networks:
      - backend
      - frontend
    ports:
      - "8000:8000"  # Use reverse proxy in production
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s  # Longer start period for production
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 2G
        reservations:
          cpus: '2'
          memory: 1G

networks:
  backend:
    driver: bridge
    internal: true  # Isolate backend in production
  frontend:
    driver: bridge

volumes:
  redis_data:
    driver: local
  postgres_data:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local
  logs:
    driver: local
```

**Key Production Changes:**
- `restart: unless-stopped` for all services
- Increased resource limits (4 CPU, 2G RAM for Squad API)
- Prometheus retention: 90 days (vs 30 days dev)
- Longer health check intervals (30s vs 10s)
- Backend network set to `internal: true` (isolated)
- Grafana root URL configured for reverse proxy
- Environment set to `production`

---

## Production Deployment

### Step 1: Build Docker Image

```bash
# Build Squad API image with version tag
sudo docker build -t squad-api:1.0.0 -t squad-api:latest .

# Verify image
sudo docker images | grep squad-api
```

### Step 2: Start Services

```bash
# Start all services in background
sudo docker-compose -f docker-compose.prod.yaml --env-file .env.production up -d

# Expected output:
# Creating network "squad-api_backend" with driver "bridge"
# Creating network "squad-api_frontend" with driver "bridge"
# Creating volume "squad-api_redis_data" with local driver
# Creating volume "squad-api_postgres_data" with local driver
# Creating volume "squad-api_prometheus_data" with local driver
# Creating volume "squad-api_grafana_data" with local driver
# Creating volume "squad-api_logs" with local driver
# Creating squad-redis-prod ... done
# Creating squad-postgres-prod ... done
# Creating squad-prometheus-prod ... done
# Creating squad-grafana-prod ... done
# Creating squad-api-prod ... done
```

### Step 3: View Logs

```bash
# Tail all logs
sudo docker-compose -f docker-compose.prod.yaml logs -f

# Tail specific service
sudo docker-compose -f docker-compose.prod.yaml logs -f squad-api

# Check for errors
sudo docker-compose -f docker-compose.prod.yaml logs --tail=100 | grep ERROR
```

### Step 4: Verify All Services Running

```bash
# Check container status
sudo docker-compose -f docker-compose.prod.yaml ps

# Expected output (all should show "Up" or "Up (healthy)"):
#      Name                    Command                  State           Ports
# -----------------------------------------------------------------------------------
# squad-api-prod         uvicorn src.main:app ...   Up (healthy)   0.0.0.0:8000->8000/tcp
# squad-grafana-prod     /run.sh                    Up (healthy)   0.0.0.0:3000->3000/tcp
# squad-postgres-prod    docker-entrypoint.sh ...   Up (healthy)   5432/tcp
# squad-prometheus-prod  /bin/prometheus ...        Up (healthy)   9090/tcp
# squad-redis-prod       docker-entrypoint.sh ...   Up (healthy)   6379/tcp
```

---

## Health Verification

### Automated Health Checks

**Script: `scripts/health_check.sh`**

```bash
#!/bin/bash

set -e

echo "=== Squad API Health Check ==="

# Check Squad API health endpoint
echo "1. Checking Squad API..."
curl -f http://localhost:8000/health || { echo "❌ Squad API health check failed"; exit 1; }
echo "✅ Squad API healthy"

# Check Prometheus
echo "2. Checking Prometheus..."
curl -f http://localhost:9090/-/healthy || { echo "❌ Prometheus health check failed"; exit 1; }
echo "✅ Prometheus healthy"

# Check Grafana
echo "3. Checking Grafana..."
curl -f http://localhost:3000/api/health || { echo "❌ Grafana health check failed"; exit 1; }
echo "✅ Grafana healthy"

# Check Redis
echo "4. Checking Redis..."
sudo docker exec squad-redis-prod redis-cli ping | grep -q PONG || { echo "❌ Redis health check failed"; exit 1; }
echo "✅ Redis healthy"

# Check PostgreSQL
echo "5. Checking PostgreSQL..."
sudo docker exec squad-postgres-prod pg_isready -U squad -d squad_api || { echo "❌ PostgreSQL health check failed"; exit 1; }
echo "✅ PostgreSQL healthy"

echo ""
echo "=== All services healthy! ==="
```

Run health check:

```bash
chmod +x scripts/health_check.sh
./scripts/health_check.sh
```

### Manual Verification

**1. API Health:**
```bash
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "redis": "connected",
    "postgres": "connected"
  }
}
```

**2. API Metrics:**
```bash
curl http://localhost:8000/metrics

# Should return Prometheus metrics (200+ lines)
```

**3. Test Agent Endpoint:**
```bash
curl -X POST http://localhost:8000/v1/agents/code \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a hello world function",
    "conversation_id": "health-check-001"
  }'

# Expected: Valid JSON response with "response" field
```

**4. Grafana Dashboards:**
```bash
# Open browser
http://localhost:3000

# Login: admin / <GRAFANA_PASSWORD from .env.production>
# Navigate to Dashboards → Verify 4 dashboards visible
```

**5. Prometheus Targets:**
```bash
# Open browser
http://localhost:9090/targets

# Verify "squad-api" target shows "UP" status
```

---

## Rollback Procedures

### Scenario 1: Rollback to Previous Version

```bash
# Stop current version
sudo docker-compose -f docker-compose.prod.yaml down

# Checkout previous stable tag
git checkout v0.9.0  # Replace with previous version

# Rebuild image
sudo docker build -t squad-api:0.9.0 -t squad-api:latest .

# Restart services
sudo docker-compose -f docker-compose.prod.yaml --env-file .env.production up -d

# Verify health
./scripts/health_check.sh
```

### Scenario 2: Rollback Configuration Only

```bash
# Revert configuration files
git checkout HEAD~1 config/

# Reload Squad API (hot-reload for config files)
sudo docker-compose -f docker-compose.prod.yaml restart squad-api

# Verify health
./scripts/health_check.sh
```

### Scenario 3: Emergency Shutdown

```bash
# Stop all services immediately
sudo docker-compose -f docker-compose.prod.yaml down

# Preserve data (volumes remain intact)

# Restart when ready
sudo docker-compose -f docker-compose.prod.yaml --env-file .env.production up -d
```

---

## Scaling

### Horizontal Scaling (Multiple Instances)

**Using Docker Swarm:**

```bash
# Initialize swarm
sudo docker swarm init

# Deploy stack
sudo docker stack deploy -c docker-compose.prod.yaml squad-api

# Scale Squad API to 3 replicas
sudo docker service scale squad-api_squad-api=3

# Verify replicas
sudo docker service ls
```

### Vertical Scaling (Increase Resources)

**Update `docker-compose.prod.yaml`:**

```yaml
squad-api:
  deploy:
    resources:
      limits:
        cpus: '8'     # Increased from 4
        memory: 4G    # Increased from 2G
      reservations:
        cpus: '4'     # Increased from 2
        memory: 2G    # Increased from 1G
```

**Apply changes:**

```bash
sudo docker-compose -f docker-compose.prod.yaml up -d --force-recreate squad-api
```

---

## Backup & Recovery

### Backup Procedure

**Script: `scripts/backup.sh`**

```bash
#!/bin/bash

BACKUP_DIR="/opt/backups/squad-api"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

echo "=== Backing up Squad API ==="

# 1. Backup PostgreSQL database
echo "1. Backing up PostgreSQL..."
sudo docker exec squad-postgres-prod pg_dump -U squad squad_api | gzip > $BACKUP_DIR/postgres_$DATE.sql.gz

# 2. Backup Redis data
echo "2. Backing up Redis..."
sudo docker exec squad-redis-prod redis-cli SAVE
sudo cp /var/lib/docker/volumes/squad-api_redis_data/_data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# 3. Backup Grafana dashboards
echo "3. Backing up Grafana..."
sudo tar -czf $BACKUP_DIR/grafana_$DATE.tar.gz -C /var/lib/docker/volumes/squad-api_grafana_data/_data .

# 4. Backup Prometheus data (optional - large)
# sudo tar -czf $BACKUP_DIR/prometheus_$DATE.tar.gz -C /var/lib/docker/volumes/squad-api_prometheus_data/_data .

# 5. Backup configuration files
echo "4. Backing up configuration..."
sudo tar -czf $BACKUP_DIR/config_$DATE.tar.gz config/ .env.production

echo "=== Backup complete ==="
ls -lh $BACKUP_DIR/*$DATE*
```

**Schedule Backups (Crontab):**

```bash
# Edit crontab
sudo crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/squad-api/scripts/backup.sh >> /var/log/squad-api-backup.log 2>&1
```

### Recovery Procedure

```bash
# 1. Restore PostgreSQL
gunzip < /opt/backups/squad-api/postgres_20251113_020000.sql.gz | \
  sudo docker exec -i squad-postgres-prod psql -U squad squad_api

# 2. Restore Redis
sudo docker cp /opt/backups/squad-api/redis_20251113_020000.rdb squad-redis-prod:/data/dump.rdb
sudo docker-compose -f docker-compose.prod.yaml restart redis

# 3. Restore Grafana
sudo tar -xzf /opt/backups/squad-api/grafana_20251113_020000.tar.gz \
  -C /var/lib/docker/volumes/squad-api_grafana_data/_data
sudo docker-compose -f docker-compose.prod.yaml restart grafana

# 4. Verify health
./scripts/health_check.sh
```

---

## Security Checklist

### Pre-Deployment Security

- [ ] **Secrets Management:**
  - [ ] All API keys stored securely (Vault, AWS Secrets Manager)
  - [ ] `.env.production` has 600 permissions
  - [ ] No secrets in git history (`git log --all -- .env`)

- [ ] **Network Security:**
  - [ ] Backend network set to `internal: true`
  - [ ] Firewall rules configured (allow 8000, 3000; block 5432, 6379, 9090)
  - [ ] SSL/TLS certificate installed (reverse proxy)

- [ ] **Container Security:**
  - [ ] Images pulled from trusted registries
  - [ ] No containers running as root (check Dockerfile)
  - [ ] Resource limits configured (prevent DoS)

- [ ] **Access Control:**
  - [ ] SSH keys only (no password auth)
  - [ ] Grafana default password changed
  - [ ] PostgreSQL default password changed
  - [ ] Sudo access limited

### Post-Deployment Security

- [ ] **Monitoring:**
  - [ ] Prometheus alerts configured
  - [ ] Slack alerts enabled (`SLACK_ALERTS_ENABLED=true`)
  - [ ] Log aggregation setup (ELK, Datadog)

- [ ] **Updates:**
  - [ ] Subscribe to security advisories (Docker, FastAPI, dependencies)
  - [ ] Schedule monthly dependency updates
  - [ ] Test updates in staging before production

- [ ] **Audit:**
  - [ ] Review logs weekly for anomalies
  - [ ] Check for unauthorized access attempts
  - [ ] Verify backup restoration quarterly

---

## Monitoring Setup

### Prometheus Alerts

**Create `config/prometheus-alerts.yml`:**

```yaml
groups:
  - name: squad_api_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(squad_api_requests_total{status="error"}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"

      - alert: ProviderDown
        expr: squad_api_provider_health == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Provider {{ $labels.provider }} is down"
          description: "Provider health check failed"

      - alert: HighLatency
        expr: histogram_quantile(0.95, squad_api_request_duration_seconds) > 2.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "P95 latency is {{ $value }} seconds"
```

**Update `config/prometheus.yml`:**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - /etc/prometheus/prometheus-alerts.yml

scrape_configs:
  - job_name: 'squad-api'
    static_configs:
      - targets: ['squad-api:8000']
```

### Grafana Alert Notifications

**Configure Slack Notifications:**

1. Open Grafana → Alerting → Contact Points
2. Add new contact point:
   - Name: Slack Alerts
   - Type: Slack
   - Webhook URL: `${SLACK_WEBHOOK_URL}`
3. Create notification policy linking to Slack Alerts

---

## Troubleshooting

For common deployment issues, see [Troubleshooting Runbook](troubleshooting.md).

**Quick Diagnostics:**

```bash
# Check all container logs
sudo docker-compose -f docker-compose.prod.yaml logs --tail=50

# Check resource usage
sudo docker stats

# Check disk space
df -h

# Check network connectivity
sudo docker network inspect squad-api_backend
sudo docker network inspect squad-api_frontend
```

---

## Deployment Checklist

Use this checklist for each production deployment:

- [ ] **Pre-Deployment:**
  - [ ] Git tag created (e.g., `v1.0.0`)
  - [ ] Changelog updated
  - [ ] Staging deployment tested
  - [ ] All tests passing (`pytest`)
  - [ ] Security scan complete (`docker scan`)

- [ ] **Deployment:**
  - [ ] `.env.production` updated
  - [ ] Docker images built
  - [ ] Services started with `docker-compose up -d`
  - [ ] Health checks passing

- [ ] **Post-Deployment:**
  - [ ] Manual verification complete (API, Grafana, Prometheus)
  - [ ] Smoke test passed (test agent endpoints)
  - [ ] Logs reviewed (no critical errors)
  - [ ] Backup created
  - [ ] Monitoring dashboards checked
  - [ ] Team notified (Slack, email)

---

## References

- [Troubleshooting Runbook](troubleshooting.md)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Swarm Documentation](https://docs.docker.com/engine/swarm/)
- [Prometheus Configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)
- [Grafana Provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/)

---

**Last Deployment:** 2025-11-13
**Deployed By:** Squad API Team
**Version:** 1.0.0
**Status:** ✅ Healthy
