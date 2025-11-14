# Story 0.3: Docker Compose - Redis Setup

Status: drafted

## Story

As a desenvolvedor,
I want Redis rodando via Docker Compose,
so that rate limiting e cache tenham backend disponível.

## Acceptance Criteria

**Given** Docker instalado  
**When** executo `docker-compose up redis`  
**Then** Redis deve:

1. ✅ Rodar em `localhost:6379` acessível do host
2. ✅ Usar imagem `redis:7-alpine` (Alpine = lightweight)
3. ✅ Volume persistente mapeado: `./data/redis:/data`
4. ✅ Healthcheck funcional: `redis-cli ping` retorna PONG
5. ✅ RDB snapshots habilitados (save 900 1, save 300 10, save 60 10000)
6. ✅ AOF (Append-Only File) enabled: `appendonly yes`
7. ✅ Container reinicia automaticamente: `restart: unless-stopped`
8. ✅ Network `squad-network` criada e Redis conectado

**And** validação externa funciona:
- `redis-cli ping` (from host) retorna PONG
- `docker logs squad-redis` não mostra erros críticos

**And** persistência testada:
- Criar key: `redis-cli SET test_key "hello"`
- Stop container: `docker-compose stop redis`
- Start container: `docker-compose start redis`
- Key existe: `redis-cli GET test_key` retorna "hello"

## Tasks / Subtasks

- [ ] **Task 1:** Adicionar serviço Redis ao docker-compose.yaml (AC: #1-8)
  - [ ] 1.1: Criar seção `networks` no topo do arquivo:
    ```yaml
    version: '3.8'
    
    networks:
      squad-network:
        driver: bridge
    
    services:
    ```
  - [ ] 1.2: Adicionar serviço Redis completo:
    ```yaml
      redis:
        image: redis:7-alpine
        container_name: squad-redis
        ports:
          - "6379:6379"
        volumes:
          - ./data/redis:/data
        command: redis-server --appendonly yes --save 900 1 --save 300 10 --save 60 10000
        healthcheck:
          test: ["CMD", "redis-cli", "ping"]
          interval: 5s
          timeout: 3s
          retries: 5
        restart: unless-stopped
        networks:
          - squad-network
    ```
  - [ ] 1.3: Verificar indentação YAML correta (espaços, não tabs)

- [ ] **Task 2:** Criar diretório de dados e .gitignore (AC: #3)
  - [ ] 2.1: Criar pasta: `mkdir -p data/redis`
  - [ ] 2.2: Verificar `.gitignore` já exclui `data/` (criado em Story 0.1)
  - [ ] 2.3: Adicionar README em data/: `echo "Docker volume data - gitignored" > data/README.md`

- [ ] **Task 3:** Testar Redis standalone (AC: #1, #4)
  - [ ] 3.1: Start Redis: `docker-compose up -d redis`
  - [ ] 3.2: Verificar container rodando: `docker ps | grep redis`
  - [ ] 3.3: Verificar logs: `docker logs squad-redis` (sem erros)
  - [ ] 3.4: Testar healthcheck: `docker inspect squad-redis | grep Health` (deve mostrar "healthy")
  - [ ] 3.5: Testar conexão: `redis-cli ping` (deve retornar PONG)

- [ ] **Task 4:** Testar persistência (AC: #5, #6, persistência)
  - [ ] 4.1: Criar test key: `redis-cli SET test_persistence "Squad API rocks"`
  - [ ] 4.2: Verificar AOF file criado: `ls -lh data/redis/appendonly.aof`
  - [ ] 4.3: Stop container: `docker-compose stop redis`
  - [ ] 4.4: Start container: `docker-compose start redis`
  - [ ] 4.5: Verificar key persiste: `redis-cli GET test_persistence` (deve retornar "Squad API rocks")
  - [ ] 4.6: Limpar test key: `redis-cli DEL test_persistence`

- [ ] **Task 5:** Testar healthcheck e restart (AC: #4, #7)
  - [ ] 5.1: Forçar crash (opcional): `docker exec squad-redis redis-cli SHUTDOWN NOSAVE`
  - [ ] 5.2: Verificar auto-restart: `docker ps` (container deve voltar)
  - [ ] 5.3: Verificar healthcheck: `docker inspect squad-redis --format='{{.State.Health.Status}}'` (deve ser "healthy")

- [ ] **Task 6:** Documentar Redis no README (AC: validação)
  - [ ] 6.1: Adicionar seção "Infrastructure" ao README.md:
    ```markdown
    ## Infrastructure
    
    ### Redis (Caching & Rate Limiting)
    
    ```bash
    # Start Redis
    docker-compose up -d redis
    
    # Check status
    docker ps | grep redis
    redis-cli ping  # Should return PONG
    
    # View logs
    docker logs squad-redis
    
    # Stop
    docker-compose stop redis
    ```
    
    **Configuration:**
    - Port: 6379
    - Persistence: RDB + AOF
    - Data: `./data/redis/` (gitignored)
    ```

- [ ] **Task 7:** Validação final (AC: all)
  - [ ] 7.1: Clean restart test:
    ```bash
    docker-compose down
    docker-compose up -d redis
    sleep 10  # Wait for healthcheck
    redis-cli ping
    ```
  - [ ] 7.2: Verificar volume data criado: `ls -lh data/redis/`
  - [ ] 7.3: Commit: `git add docker-compose.yaml README.md data/README.md && git commit -m "Add Redis service (Story 0.3)"`

## Dev Notes

### Architecture Decisions

**Decision: Redis 7 Alpine**
- Image: `redis:7-alpine` (~30MB vs ~110MB debian)
- Rationale: Lightweight, production-ready, Alpine security
- [Source: docs/architecture.md#Deployment-Architecture]

**Decision: RDB + AOF Persistence**
- RDB: Snapshots (900s=1 change, 300s=10, 60s=10000)
- AOF: Every write operation logged
- Rationale: Balance performance vs data safety
- Recovery: AOF takes precedence (more recent data)
- [Source: docs/architecture.md#Data-Architecture - Redis persistence]

**Decision: Docker Network**
- Network: `squad-network` (bridge)
- Rationale: All services communicate via internal DNS
- Benefit: Services use `redis:6379` not `localhost:6379`
- [Source: docs/architecture.md#Deployment-Architecture]

### Redis Configuration

**Persistence Strategy:**
```
RDB (snapshots):
- save 900 1     # After 900s if 1 key changed
- save 300 10    # After 300s if 10 keys changed  
- save 60 10000  # After 60s if 10000 keys changed

AOF (append-only file):
- appendonly yes           # Enable AOF
- appendfsync everysec     # Fsync every second (default)
```

**Trade-offs:**
- RDB: Fast restarts, less disk I/O, but lose data between snapshots
- AOF: Better durability, but slower restarts and larger files
- **Using both:** Best of both worlds (ADR decision)

### Use Cases in Squad API

**Rate Limiting (Epic 2):**
- Token buckets: `bucket:{provider}` keys
- Sliding windows: `window:{provider}` sorted sets
- 429 spike tracking: `spike:{provider}` sorted sets
- [Source: docs/architecture.md#Data-Architecture]

**Agent State (Epic 1):**
- Agent definitions cache: `agent:{agent_id}`
- Conversation history: `conversation:{user_id}:{agent_id}`
- TTL: 3600s (1 hour)
- [Source: docs/architecture.md#Data-Architecture - Redis Data Models]

**Performance:**
- Expected load: ~130 RPM aggregate
- Redis capacity: 100k+ ops/sec (overkill for MVP)
- Latency target: <5ms (easily achieved)

### Healthcheck Details

**Test Command:** `redis-cli ping`
- Success: Returns "PONG"
- Failure: Connection refused or timeout

**Timing:**
- Interval: 5s (check every 5 seconds)
- Timeout: 3s (max wait time)
- Retries: 5 (mark unhealthy after 5 failures = 25s)
- Start period: 0s (check immediately)

**Status Progression:**
```
starting → healthy (if ping succeeds)
starting → unhealthy (if 5 consecutive failures)
healthy → unhealthy (if fails during operation)
```

### Common Issues

**Issue 1: Port 6379 already in use**
- Symptom: `ERROR: port is already allocated`
- Solution: `lsof -i :6379` (find process), kill or change port to 6380

**Issue 2: Permission denied on data/redis/**
- Symptom: `MISCONF Redis is configured to save RDB snapshots`
- Solution: `sudo chown -R $(whoami) data/redis/`

**Issue 3: Container keeps restarting**
- Symptom: `docker ps` shows "Restarting"
- Diagnosis: `docker logs squad-redis`
- Common cause: Bad redis.conf syntax in command
- Solution: Remove command, use defaults, verify syntax

### Testing Redis Connection

**From Host:**
```bash
redis-cli ping                    # PONG
redis-cli SET test "hello"        # OK
redis-cli GET test                # "hello"
redis-cli DEL test                # (integer) 1
```

**From Python (future stories):**
```python
import redis.asyncio as redis

client = redis.from_url("redis://localhost:6379")
await client.ping()  # Returns True
await client.set("test", "value")
await client.get("test")  # Returns b'value'
```

### Project Structure Impact

**Files Modified:**
- `docker-compose.yaml` - MODIFIED (add Redis service + network)
- `README.md` - MODIFIED (add Infrastructure section)
- `data/README.md` - NEW (document data directory)

**Files Created:**
- `data/redis/` - NEW directory (gitignored, created by Docker)
- `data/redis/appendonly.aof` - NEW (created by Redis)
- `data/redis/dump.rdb` - NEW (created by Redis)

### References

- [Architecture - Deployment](docs/architecture.md#Deployment-Architecture) - Docker Compose stack
- [Architecture - Data Models](docs/architecture.md#Data-Architecture) - Redis keys & structure
- [Epic 0 - Story 0.3](docs/epics.md#Story-0.3) - Original requirements
- [Epic 2](docs/epics.md#Epic-2) - Rate limiting (main Redis use case)

### Learnings from Previous Story

**From Story 0-2-dependencies-e-requirements-management (Status: drafted)**

Story 0.2 ainda não implementada, mas expectativas:
- `requirements.txt` completo com `redis[hiredis]==5.0.1`
- Dependencies instaladas no venv

**Expected Dependencies:**
- `redis[hiredis]` package installed (Python client)
- Isso permitirá Squad API se conectar ao Redis

**For This Story:**
- Focus apenas no Redis server (Docker)
- Python client testing vem em Story 1.5 (Conversation State Manager)

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

_To be filled by dev agent_

### Debug Log References

_To be filled by dev agent - document:_
- Docker compose up errors
- Redis healthcheck failures
- Persistence test results

### Completion Notes List

_To be filled by dev agent - document:_
- Redis version confirmed: `docker exec squad-redis redis-cli --version`
- Data directory size: `du -sh data/redis/`
- First key created for testing
- Any deviations from planned config

### File List

_To be filled by dev agent:_
- MODIFIED: docker-compose.yaml (add Redis service + network)
- MODIFIED: README.md (add Infrastructure section)
- NEW: data/README.md

---

**Change Log:**
- 2025-11-13: Story drafted by SM Agent (Bob)

