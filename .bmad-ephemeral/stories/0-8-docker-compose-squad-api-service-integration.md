# Story 0.8: Docker Compose - Squad API Service Integration

Status: drafted

## Story

As a desenvolvedor,
I want Squad API rodando via Docker Compose,
so that todo stack (Redis, PostgreSQL, Prometheus, Grafana, App) sobe com 1 comando.

## Acceptance Criteria

**Given** todos services configurados individualmente (Stories 0.3-0.7)  
**When** executo `docker-compose up`  
**Then** todos services devem estar rodando:

1. ✅ Redis: healthy (port 6379)
2. ✅ PostgreSQL: healthy (port 5432)
3. ✅ Prometheus: scraping Squad API (port 9090)
4. ✅ Grafana: acessível com Prometheus datasource (port 3000)
5. ✅ Squad API: `/health` retorna ok (port 8000)
6. ✅ Prometheus scraping Squad API com sucesso (target "up")
7. ✅ `docker-compose ps` mostra todos services "Up (healthy)"
8. ✅ One-command startup: `docker-compose up` funciona

**And** validação completa:
- `curl http://localhost:8000/health` → 200 OK
- `curl http://localhost:9090/api/v1/targets` → squad-api target "up"
- Squad API logs mostram conexão Redis OK

## Tasks / Subtasks

- [ ] **Task 1:** Criar Dockerfile para Squad API
  - [ ] 1.1: Criar `Dockerfile` na raiz:
    ```dockerfile
    FROM python:3.11-slim
    
    WORKDIR /app
    
    # Copy requirements first (layer caching)
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    
    # Copy application
    COPY src/ /app/src/
    COPY config/ /app/config/
    COPY public/ /app/public/
    
    # Expose port
    EXPOSE 8000
    
    # Run application
    CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
    ```

- [ ] **Task 2:** Adicionar serviço squad-api ao docker-compose.yaml
  - [ ] 2.1: Adicionar serviço squad-api:
    ```yaml
      squad-api:
        build: .
        container_name: squad-api
        ports:
          - "8000:8000"
        environment:
          - REDIS_URL=redis://redis:6379
          - DATABASE_URL=postgresql://squad:${POSTGRES_PASSWORD:-dev_password}@postgres:5432/squad_api
          - GROQ_API_KEY=${GROQ_API_KEY}
          - CEREBRAS_API_KEY=${CEREBRAS_API_KEY}
          - GEMINI_API_KEY=${GEMINI_API_KEY}
          - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
          - SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}
        volumes:
          - ./src:/app/src
          - ./config:/app/config
          - ./.bmad:/app/.bmad:ro  # Mount BMad definitions (read-only)
          - ./docs:/app/docs
          - ./public:/app/public
        depends_on:
          redis:
            condition: service_healthy
          postgres:
            condition: service_healthy
        restart: unless-stopped
        networks:
          - squad-network
    ```

- [ ] **Task 3:** Testar build e startup
  - [ ] 3.1: Build image: `docker-compose build squad-api`
  - [ ] 3.2: Start all services: `docker-compose up -d`
  - [ ] 3.3: Watch logs: `docker-compose logs -f squad-api`
  - [ ] 3.4: Verificar Squad API started: "Application startup complete"
  - [ ] 3.5: Test health: `curl http://localhost:8000/health`

- [ ] **Task 4:** Validar integração completa
  - [ ] 4.1: Verificar todos services healthy:
    ```bash
    docker-compose ps
    # Todos devem mostrar "Up (healthy)" ou "Up"
    ```
  - [ ] 4.2: Verificar Prometheus scraping Squad API:
    - Open `http://localhost:9090/targets`
    - squad-api target deve estar "UP" (green)
  - [ ] 4.3: Verificar metrics endpoint:
    ```bash
    curl http://localhost:8000/metrics | grep python_info
    # Deve retornar metrics de Python
    ```
  - [ ] 4.4: Verificar Grafana pode acessar metrics:
    - Open `http://localhost:3000`
    - Explore → Prometheus → Query: `up{job="squad-api"}` → Should return 1

- [ ] **Task 5:** Testar restart e persistência
  - [ ] 5.1: Stop all: `docker-compose down`
  - [ ] 5.2: Start all: `docker-compose up -d`
  - [ ] 5.3: Verificar volumes persistem:
    ```bash
    ls -lh data/redis/
    ls -lh data/postgres/
    ls -lh data/prometheus/
    ls -lh data/grafana/
    ```
  - [ ] 5.4: Verificar todos services voltam healthy

- [ ] **Task 6:** Documentar stack completo no README
  - [ ] 6.1: Atualizar README com "Complete Stack":
    ```markdown
    ## Complete Stack (Docker Compose)
    
    Start all services with one command:
    
    ```bash
    # Start entire stack
    docker-compose up -d
    
    # Check status
    docker-compose ps
    
    # View logs
    docker-compose logs -f squad-api
    
    # Stop all
    docker-compose down
    ```
    
    ### Services
    
    | Service | Port | URL |
    |---------|------|-----|
    | Squad API | 8000 | http://localhost:8000 |
    | Swagger Docs | 8000 | http://localhost:8000/docs |
    | Prometheus | 9090 | http://localhost:9090 |
    | Grafana | 3000 | http://localhost:3000 |
    | Redis | 6379 | localhost:6379 |
    | PostgreSQL | 5432 | localhost:5432 |
    
    **First time setup:**
    1. Copy `.env.example` to `.env`
    2. Fill in API keys (GROQ_API_KEY, etc.)
    3. Run `docker-compose up -d`
    4. Access http://localhost:8000/docs
    ```

- [ ] **Task 7:** Commit e tag release
  - [ ] 7.1: Commit:
    ```bash
    git add Dockerfile docker-compose.yaml README.md
    git commit -m "Add Squad API Docker integration (Story 0.8) - Epic 0 Complete!"
    ```
  - [ ] 7.2: (Optional) Tag: `git tag v0.1.0-foundation`

## Dev Notes

### Architecture - Complete Stack

**Services Dependency Graph:**
```
squad-api
  ├── depends on: redis (healthy)
  ├── depends on: postgres (healthy)
  └── scraped by: prometheus
      └── visualized by: grafana
```

**Network Communication:**
- All services on `squad-network` (bridge)
- Services use DNS: `redis:6379`, `postgres:5432`, `squad-api:8000`
- Host access: `localhost:PORT`

### Dockerfile Strategy

**Multi-stage NOT used (for MVP):**
- Single stage: python:3.11-slim (~150MB)
- Requirements installed once (layer caching)
- Source code mounted as volume (hot-reload in dev)

**Production Optimization (Future):**
- Multi-stage build (builder + runtime)
- Remove dev tools
- Use Python slim or alpine
- Size reduction: ~150MB → ~80MB

### Environment Variables

**Required for Squad API:**
```bash
# LLM APIs (Required for Epic 1+)
GROQ_API_KEY=...
CEREBRAS_API_KEY=...
GEMINI_API_KEY=...
OPENROUTER_API_KEY=...

# Slack (Optional, Epic 6)
SLACK_WEBHOOK_URL=...

# Infra (Auto-configured by Docker)
REDIS_URL=redis://redis:6379
DATABASE_URL=postgresql://squad:PASSWORD@postgres:5432/squad_api
```

**Set in `.env` file** (not committed, from `.env.example`)

### Volume Mounts

**Code Volumes (hot-reload):**
- `./src:/app/src` - Source code changes reflected immediately
- `./config:/app/config` - Config changes reflected
- `./.bmad:/app/.bmad:ro` - BMad definitions (read-only)

**Data Volumes (persistence):**
- `./data/redis` - Redis RDB + AOF
- `./data/postgres` - PostgreSQL data
- `./data/prometheus` - Metrics TSDB
- `./data/grafana` - Dashboards + settings

### Health Check Strategy

**Depends on Healthchecks:**
```yaml
depends_on:
  redis:
    condition: service_healthy  # Wait for Redis ping
  postgres:
    condition: service_healthy  # Wait for pg_isready
```

**Benefit:** Squad API só inicia quando dependencies estão prontas

### Common Issues

**Issue 1: Build fails - pip install error**
- Check `requirements.txt` is correct (Story 0.2)
- Verify network access during build

**Issue 2: Squad API can't connect to Redis**
- Check `REDIS_URL=redis://redis:6379` (not localhost)
- Verify Redis is healthy: `docker-compose ps redis`

**Issue 3: Prometheus target "down"**
- Check Squad API is running: `docker-compose ps squad-api`
- Check `/metrics` endpoint: `curl http://localhost:8000/metrics`
- Verify `config/prometheus.yml` has correct target

**Issue 4: API keys not loading**
- Check `.env` file exists (copy from `.env.example`)
- Verify env vars in docker-compose.yaml reference `${VAR_NAME}`

### Testing Full Stack

**Smoke Test Script:**
```bash
#!/bin/bash
# smoke-test.sh

echo "🚀 Starting smoke test..."

# Start stack
docker-compose up -d
sleep 15  # Wait for all services

# Test Squad API
echo "Testing Squad API..."
curl -f http://localhost:8000/health || exit 1

# Test Prometheus scraping
echo "Testing Prometheus..."
curl -f http://localhost:9090/api/v1/targets | grep squad-api || exit 1

# Test metrics endpoint
echo "Testing metrics..."
curl -f http://localhost:8000/metrics | grep python_info || exit 1

echo "✅ All tests passed!"
```

### Project Structure Impact

**Files Created:**
- `Dockerfile` - NEW (Squad API image build instructions)

**Files Modified:**
- `docker-compose.yaml` - MODIFIED (add squad-api service, completing 6-service stack)
- `README.md` - MODIFIED (add Complete Stack documentation)

### References

- [Architecture - Deployment](docs/architecture.md#Deployment-Architecture) - Full docker-compose.yaml spec
- [Architecture - Project Structure](docs/architecture.md#Project-Structure) - Volume mounts
- [Epic 0](docs/epics.md#Epic-0) - Foundation requirements

### Learnings from Previous Stories

**From Stories 0.1-0.7:**
- Structure criada (0.1)
- Dependencies instaladas (0.2)
- Redis configurado (0.3)
- PostgreSQL configurado (0.4)
- Prometheus configurado (0.5)
- Grafana configurado (0.6)
- FastAPI skeleton criado (0.7)

**For This Story:**
- **Integra tudo** - This is the "glue" story
- Valida que infra completa funciona
- One-command startup: `docker-compose up`

**Success Criteria:**
- Todos 6 services rodando e saudáveis
- Squad API acessível e respondendo
- Prometheus coletando metrics
- Grafana visualizando dados

## Dev Agent Record

### Context Reference
<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used
_To be filled by dev agent_

### Debug Log References
_To be filled by dev agent - document:_
- Docker build output
- First startup logs from each service
- Any integration issues encountered

### Completion Notes List
_To be filled by dev agent - document:_
- Total startup time (docker-compose up → all healthy)
- Docker image sizes: `docker images | grep squad`
- Memory usage: `docker stats --no-stream`
- Recommendations for Story 1.1 (first Epic 1 story)

### File List
- NEW: Dockerfile
- MODIFIED: docker-compose.yaml (final integration)
- MODIFIED: README.md (Complete Stack docs)

---

**Change Log:**
- 2025-11-13: Story drafted by SM Agent (Bob)

---

## 🎉 **EPIC 0 COMPLETE!**

**Value Delivered:**
- ✅ Complete infrastructure running with `docker-compose up`
- ✅ 6 services integrated: Squad API, Redis, PostgreSQL, Prometheus, Grafana, Networking
- ✅ Hot-reload development environment
- ✅ Persistent data volumes
- ✅ Health checks and service dependencies
- ✅ One-command startup and teardown

**Next Epic:** Epic 1 - Agent Transformation Engine (The CORE MAGIC!)

