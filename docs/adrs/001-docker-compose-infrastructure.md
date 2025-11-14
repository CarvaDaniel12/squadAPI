# ADR-001: Docker Compose for Local Development

**Status:** Accepted
**Date:** 2025-11-13
**Epic:** 0 - Infrastructure Foundation
**Story:** 0.1 - Foundation Setup

## Context

Squad API requires multiple infrastructure services (Redis, PostgreSQL, Prometheus, Grafana) to function. Developers need a consistent, reproducible local development environment that:

1. Starts all services with one command
2. Works across Windows, macOS, and Linux
3. Isolates dependencies from host system
4. Matches production topology
5. Enables quick iteration (hot-reload)

**Alternatives considered:**
- Manual installation of each service
- Kubernetes (minikube, k3s)
- Virtual machines (Vagrant, VMware)
- Cloud-based dev environments

## Decision

Use **Docker Compose** for local development infrastructure with the following characteristics:

- **Single `docker-compose.yaml`** orchestrating 5 services
- **Named volumes** for data persistence (redis_data, postgres_data, etc.)
- **Dual networks** (backend for internal, frontend for exposed services)
- **Health checks** for all services with startup dependencies
- **Resource limits** to prevent host exhaustion
- **Volume mounts** for code (hot-reload) and configs
- **`.env` file** for configuration (API keys, passwords)

**Configuration:**
```yaml
version: '3.8'
services:
  redis: # Conversation context
  postgres: # Rate limit state
  prometheus: # Metrics collection
  grafana: # Dashboards
  squad-api: # FastAPI application
```

## Consequences

### Positive

- ✅ **One-command start:** `docker-compose up -d` starts entire stack
- ✅ **Consistency:** Same environment for all developers
- ✅ **Isolation:** No conflicts with host services
- ✅ **Easy cleanup:** `docker-compose down -v` removes everything
- ✅ **Resource efficient:** Lower overhead than VMs
- ✅ **Production parity:** Similar to Docker Swarm/Kubernetes deployment
- ✅ **Fast iteration:** Volume mounts enable hot-reload
- ✅ **Cross-platform:** Works on Windows, macOS, Linux

### Negative

- ❌ **Docker Desktop required:** ~2GB download, learning curve
- ❌ **Not production-ready:** Needs separate prod config (docker-compose.prod.yaml)
- ❌ **Single-node only:** Doesn't support clustering (use Swarm/K8s for that)
- ❌ **Volume performance:** Slower on macOS (use named volumes, not bind mounts)

## Alternatives Considered

### 1. Manual Installation

**Description:** Install Redis, PostgreSQL, etc. directly on host

**Pros:**
- No Docker overhead
- Native performance

**Cons:**
- Inconsistent across dev machines
- Version conflicts
- Hard to reset state
- Difficult onboarding

**Why Rejected:** Too much friction for new developers, inconsistent environments

### 2. Kubernetes (Minikube/K3s)

**Description:** Use Kubernetes for local development

**Pros:**
- Production parity with K8s deployment
- Scales to multi-node
- Advanced orchestration features

**Cons:**
- Steep learning curve
- Higher resource usage (2-4GB RAM for cluster)
- Slower startup (<30s for Docker Compose vs >2 min for minikube)
- Overkill for single-node development

**Why Rejected:** Too complex for local development, Docker Compose sufficient

### 3. Vagrant Virtual Machines

**Description:** Use Vagrant to provision VMs

**Pros:**
- Complete OS isolation
- Can run different Linux distros

**Cons:**
- High resource usage (4-8GB RAM per VM)
- Slow startup (minutes vs seconds)
- Large disk footprint (5-10GB per VM)
- Outdated tooling

**Why Rejected:** Too heavy, Docker containers more efficient

## Implementation Details

**docker-compose.yaml highlights:**

1. **Networks:**
   ```yaml
   networks:
     backend:  # Internal services (Redis, Postgres)
     frontend: # Exposed services (API, Grafana)
   ```

2. **Volumes:**
   ```yaml
   volumes:
     redis_data:      # Persistent conversation context
     postgres_data:   # Persistent rate limit state
     prometheus_data: # Metrics retention
     grafana_data:    # Dashboard config
   ```

3. **Health Checks:**
   ```yaml
   healthcheck:
     test: ["CMD", "redis-cli", "ping"]
     interval: 10s
     retries: 3
   ```

4. **Dependencies:**
   ```yaml
   depends_on:
     redis:
       condition: service_healthy
     postgres:
       condition: service_healthy
   ```

## Migration Path

If we outgrow Docker Compose:

1. **Docker Swarm:** Minimal changes to docker-compose.yaml
2. **Kubernetes:** Use Kompose to convert docker-compose.yaml to K8s manifests
3. **Cloud:** AWS ECS, GCP Cloud Run use similar container definitions

## References

- [docker-compose.yaml](../../docker-compose.yaml)
- [Epic 0 Technical Context](../../.bmad-ephemeral/epics/0-infrastructure-context.md)
- [Story 8.1: Docker Compose Complete Stack](../../docs/sprint-artifacts/8-1-docker-compose-complete-stack.md)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
