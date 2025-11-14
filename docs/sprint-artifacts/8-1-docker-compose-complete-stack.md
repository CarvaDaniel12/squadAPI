# Story 8.1: Docker Compose Complete Stack

**Epic:** Epic 8 - Deployment & Documentation
**Story Points:** 3
**Priority:** High
**Status:** Ready for Dev

## Story Description

As a **developer/operator**, I want **all Squad API services consolidated in a single docker-compose.yaml** so that I can **deploy the entire stack with one command (`docker-compose up`)**.

## Business Value

- **One-Command Deployment:** Start all 5 services with `docker-compose up -d`
- **Reproducibility:** Identical setup across dev/staging/prod
- **Fast Onboarding:** New developers productive in <5 minutes
- **Simplified Operations:** Single file manages all infrastructure

## Current State Analysis

**Existing docker-compose.yaml (105 lines):**
✅ **Services Configured:**
- Redis (port 6379, health checks, persistence)
- PostgreSQL (port 5432, health checks, persistence)
- Prometheus (port 9090, config mounted)
- Grafana (port 3000, dashboards provisioned)
- Squad API (port 8000, all dependencies)

✅ **Good Practices Already Implemented:**
- Health checks on critical services
- Volume persistence for data
- Environment variable configuration
- Service dependencies (depends_on)
- Restart policies
- Single network (squad-network)

❌ **Gaps to Address:**
- No separate backend/frontend networks
- Missing health check on Prometheus/Grafana
- No resource limits (memory/CPU)
- .env.example needs update with all vars
- Missing service descriptions/labels
- No explicit volume declarations

## Acceptance Criteria

### AC1: Enhanced Network Isolation

**Given** security best practices
**When** services are deployed
**Then** network topology must be:

- ✅ **backend** network (internal only)
  - Redis (no external access)
  - PostgreSQL (no external access)
  - Squad API backend communication

- ✅ **frontend** network (exposed services)
  - Squad API (8000 → external)
  - Prometheus (9090 → external)
  - Grafana (3000 → external)

- ✅ Squad API connected to both networks
- ✅ Redis/Postgres not accessible from host (except for dev via ports)

### AC2: Comprehensive Health Checks

**Given** all services running
**When** health checks execute
**Then** must validate:

- ✅ Redis: `redis-cli ping` returns PONG
- ✅ PostgreSQL: `pg_isready -U squad` returns 0
- ✅ Prometheus: HTTP GET /-/healthy returns 200
- ✅ Grafana: HTTP GET /api/health returns 200
- ✅ Squad API: HTTP GET /health returns 200

**And** `docker-compose ps` shows all as "healthy"

### AC3: Resource Limits

**Given** production deployment
**When** services run under load
**Then** resource limits must prevent runaway processes:

- ✅ Redis: 256MB memory limit
- ✅ PostgreSQL: 512MB memory limit
- ✅ Prometheus: 1GB memory limit
- ✅ Grafana: 512MB memory limit
- ✅ Squad API: 1GB memory limit

**And** CPU limits: 1 CPU per service (reserve 0.5)

### AC4: Explicit Volume Management

**Given** data persistence requirements
**When** docker-compose.yaml is deployed
**Then** named volumes must be declared:

```yaml
volumes:
  redis_data:
    driver: local
  postgres_data:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local
```

**And** services use named volumes instead of bind mounts for data

### AC5: Complete .env.example

**Given** new developer setup
**When** copying .env.example to .env
**Then** must include all required variables:

```bash
# Database
POSTGRES_PASSWORD=dev_password_change_in_prod

# Grafana
GRAFANA_PASSWORD=admin

# LLM Provider API Keys
GROQ_API_KEY=your_groq_key_here
CEREBRAS_API_KEY=your_cerebras_key_here
GEMINI_API_KEY=your_gemini_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
TOGETHER_API_KEY=optional_together_key

# Slack Alerts (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_ALERTS_ENABLED=false

# Application
LOG_LEVEL=INFO
ENVIRONMENT=dev

# Internal (Auto-configured by docker-compose)
REDIS_URL=redis://redis:6379
DATABASE_URL=postgresql://squad:${POSTGRES_PASSWORD}@postgres:5432/squad_api
```

**And** comments explain where to get each API key

### AC6: Service Labels & Metadata

**Given** operational visibility
**When** inspecting services
**Then** labels must provide context:

```yaml
labels:
  - "com.squad.service=redis"
  - "com.squad.tier=backend"
  - "com.squad.description=Conversation state and rate limiting"
```

**And** all 5 services have descriptive labels

### AC7: Production-Ready Configurations

**Given** production deployment
**When** services start
**Then** configurations must support:

- ✅ **Logging:** JSON format, stdout/stderr
- ✅ **Monitoring:** Prometheus scrape endpoints
- ✅ **Backups:** Volume snapshots possible
- ✅ **Secrets:** Environment variables (not hardcoded)
- ✅ **Updates:** Rolling updates supported
- ✅ **Rollbacks:** Previous images tagged

## Implementation Design

### Enhanced docker-compose.yaml Structure

```yaml
version: '3.8'

# ==================================
# NETWORKS
# ==================================
networks:
  backend:
    driver: bridge
    internal: false  # Dev access via ports
  frontend:
    driver: bridge

# ==================================
# VOLUMES
# ==================================
volumes:
  redis_data:
    driver: local
  postgres_data:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local

# ==================================
# SERVICES
# ==================================
services:

  # ----------------------------------
  # Redis - Conversation State & Rate Limiting
  # ----------------------------------
  redis:
    image: redis:7-alpine
    container_name: squad-redis
    ports:
      - "6379:6379"  # Dev access only
    volumes:
      - redis_data:/data
    command: >
      redis-server
      --appendonly yes
      --save 900 1
      --save 300 10
      --save 60 10000
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 5s
    restart: unless-stopped
    networks:
      - backend
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 256M
        reservations:
          cpus: '0.5'
          memory: 128M
    labels:
      - "com.squad.service=redis"
      - "com.squad.tier=backend"
      - "com.squad.description=Conversation state and rate limiting"

  # ----------------------------------
  # PostgreSQL - Audit Logs (Future)
  # ----------------------------------
  postgres:
    image: postgres:15-alpine
    container_name: squad-postgres
    ports:
      - "5432:5432"  # Dev access only
    environment:
      POSTGRES_DB: squad_api
      POSTGRES_USER: squad
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-dev_password}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=en_US.utf8"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U squad -d squad_api"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 10s
    restart: unless-stopped
    networks:
      - backend
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    labels:
      - "com.squad.service=postgres"
      - "com.squad.tier=backend"
      - "com.squad.description=Audit logs and persistent storage"

  # ----------------------------------
  # Prometheus - Metrics Collection
  # ----------------------------------
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: squad-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
      - '--web.enable-lifecycle'
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:9090/-/healthy"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 10s
    restart: unless-stopped
    networks:
      - backend
      - frontend
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    labels:
      - "com.squad.service=prometheus"
      - "com.squad.tier=monitoring"
      - "com.squad.description=Metrics collection and storage"

  # ----------------------------------
  # Grafana - Visualization & Dashboards
  # ----------------------------------
  grafana:
    image: grafana/grafana:10.2.2
    container_name: squad-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      - GF_SECURITY_ADMIN_USER=admin
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SERVER_ROOT_URL=http://localhost:3000
      - GF_ANALYTICS_REPORTING_ENABLED=false
      - GF_ANALYTICS_CHECK_FOR_UPDATES=false
    volumes:
      - ./config/grafana/datasources:/etc/grafana/provisioning/datasources:ro
      - ./config/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - grafana_data:/var/lib/grafana
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:3000/api/health"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 10s
    depends_on:
      prometheus:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - frontend
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    labels:
      - "com.squad.service=grafana"
      - "com.squad.tier=monitoring"
      - "com.squad.description=Dashboards and visualization"

  # ----------------------------------
  # Squad API - Main Application
  # ----------------------------------
  squad-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: squad-api
    ports:
      - "8000:8000"
    environment:
      # Database
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://squad:${POSTGRES_PASSWORD:-dev_password}@postgres:5432/squad_api

      # LLM Providers
      - GROQ_API_KEY=${GROQ_API_KEY}
      - CEREBRAS_API_KEY=${CEREBRAS_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - TOGETHER_API_KEY=${TOGETHER_API_KEY:-}

      # Slack Alerts
      - SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL:-}
      - SLACK_ALERTS_ENABLED=${SLACK_ALERTS_ENABLED:-false}

      # Application
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - ENVIRONMENT=${ENVIRONMENT:-dev}
    volumes:
      - ./src:/app/src:ro
      - ./config:/app/config:ro
      - ./.bmad:/app/.bmad:ro
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8000/health"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 30s
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
      prometheus:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - backend
      - frontend
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '1'
          memory: 512M
    labels:
      - "com.squad.service=api"
      - "com.squad.tier=application"
      - "com.squad.description=Squad API main application"
```

### Updated .env.example

```bash
# ==================================
# Squad API - Environment Variables
# ==================================

# ----------------------------------
# Database Configuration
# ----------------------------------
POSTGRES_PASSWORD=dev_password_CHANGE_IN_PRODUCTION

# ----------------------------------
# Grafana Configuration
# ----------------------------------
GRAFANA_PASSWORD=admin

# ----------------------------------
# LLM Provider API Keys
# ----------------------------------
# Get your API keys from:
# - Groq: https://console.groq.com/keys
# - Cerebras: https://cloud.cerebras.ai/
# - Gemini: https://makersuite.google.com/app/apikey
# - OpenRouter: https://openrouter.ai/keys

GROQ_API_KEY=your_groq_api_key_here
CEREBRAS_API_KEY=your_cerebras_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional: Together AI
TOGETHER_API_KEY=optional_together_api_key

# ----------------------------------
# Slack Alerts (Optional)
# ----------------------------------
# Get webhook URL: https://api.slack.com/messaging/webhooks
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_ALERTS_ENABLED=false

# ----------------------------------
# Application Configuration
# ----------------------------------
LOG_LEVEL=INFO
ENVIRONMENT=dev

# ----------------------------------
# Internal URLs (Auto-configured)
# ----------------------------------
# These are set automatically by docker-compose
# REDIS_URL=redis://redis:6379
# DATABASE_URL=postgresql://squad:${POSTGRES_PASSWORD}@postgres:5432/squad_api
```

## Testing Checklist

### Local Testing

- [x] `docker-compose config` validates without errors ✅ YAML syntax validated with Python
- [ ] `docker-compose up -d` starts all 5 services (requires Docker installed)
- [ ] `docker-compose ps` shows all services as "healthy" within 60s
- [ ] Squad API accessible at http://localhost:8000
- [ ] Prometheus accessible at http://localhost:9090
- [ ] Grafana accessible at http://localhost:3000
- [ ] Health checks: All return 200 OK
  - [ ] http://localhost:8000/health
  - [ ] http://localhost:9090/-/healthy
  - [ ] http://localhost:3000/api/health
- [ ] Metrics endpoint: http://localhost:8000/metrics returns Prometheus format
- [ ] Grafana dashboards load (4 dashboards from Epic 6)
- [ ] `docker-compose logs -f squad-api` shows JSON logs
- [ ] `docker-compose restart squad-api` restarts without data loss
- [ ] `docker-compose down && docker-compose up` preserves data
- [ ] Resource usage: `docker stats` shows limits enforced

### Network Testing

- [ ] Redis not accessible from host (except port 6379 for dev)
- [ ] PostgreSQL not accessible from host (except port 5432 for dev)
- [ ] Squad API can connect to Redis
- [ ] Squad API can connect to PostgreSQL
- [ ] Prometheus can scrape Squad API metrics
- [ ] Grafana can query Prometheus

### Cleanup Testing

- [ ] `docker-compose down` stops all services
- [ ] `docker-compose down -v` removes volumes
- [ ] Fresh start works: `docker-compose up -d` after cleanup

## Definition of Done

- [x] Story artifact created with AC1-AC7
- [x] docker-compose.yaml enhanced with:
  - [x] Separate backend/frontend networks
  - [x] Health checks for all services
  - [x] Resource limits (CPU/memory)
  - [x] Named volumes declared
  - [x] Service labels/metadata
  - [x] Production-ready configurations
- [x] .env.example updated with:
  - [x] All required variables
  - [x] Comments explaining each variable
  - [x] Links to get API keys
  - [x] Sensible defaults
- [x] YAML syntax validated (Python yaml.safe_load)
- [ ] Full deployment testing (requires Docker installation)
- [ ] Sprint status updated: 8-1 → done

## Dependencies

- Epic 0: Infrastructure services configured
- Epic 5: Prometheus metrics implemented
- Epic 6: Grafana dashboards created
- Epic 7: Configuration system ready

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Resource limits too restrictive | Medium | Start conservative, monitor with `docker stats`, adjust |
| Network isolation breaks dev workflow | Medium | Keep ports exposed for dev, document production changes |
| Volume permissions issues | Low | Use named volumes, document ownership |
| Health checks too aggressive | Low | Tune intervals/retries, add start_period |

## Notes

- This story consolidates existing docker-compose.yaml with improvements
- Focus on production-readiness while maintaining dev experience
- Networks keep backend isolated but allow dev port access
- Resource limits prevent runaway processes in production
- Health checks enable orchestration tools (Kubernetes, Swarm)

## References

- Epic 8 Technical Context: `.bmad-ephemeral/epics/8-deployment-documentation-context.md`
- Current docker-compose.yaml: `docker-compose.yaml` (105 lines)
- Prometheus config: `config/prometheus.yml`
- Grafana dashboards: `config/grafana/dashboards/`
