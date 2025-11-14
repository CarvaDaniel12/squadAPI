# Story 0.4: Docker Compose - PostgreSQL Setup

Status: drafted

## Story

As a desenvolvedor,
I want PostgreSQL rodando via Docker Compose,
so that audit logs e persistence tenham database disponível.

## Acceptance Criteria

**Given** Docker Compose configurado (Story 0.3 criou network)  
**When** executo `docker-compose up postgres`  
**Then** PostgreSQL deve:

1. ✅ Rodar em `localhost:5432` acessível do host
2. ✅ Usar imagem `postgres:15-alpine`
3. ✅ Database `squad_api` criado automaticamente
4. ✅ User `squad` e password configurados via environment variables
5. ✅ Volume persistente: `./data/postgres:/var/lib/postgresql/data`
6. ✅ Healthcheck funcional: `pg_isready -U squad` retorna success
7. ✅ Connected to `squad-network`
8. ✅ Container reinicia automaticamente

**And** conexão funciona:
- `psql -h localhost -U squad -d squad_api` conecta sem erro
- Password: valor de `POSTGRES_PASSWORD` env var

**And** persistência testada:
- Criar tabela test
- Stop/start container
- Tabela ainda existe

## Tasks / Subtasks

- [ ] **Task 1:** Adicionar serviço PostgreSQL ao docker-compose.yaml (AC: #1-8)
  - [ ] 1.1: Adicionar serviço PostgreSQL:
    ```yaml
      postgres:
        image: postgres:15-alpine
        container_name: squad-postgres
        ports:
          - "5432:5432"
        environment:
          POSTGRES_DB: squad_api
          POSTGRES_USER: squad
          POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-dev_password}
        volumes:
          - ./data/postgres:/var/lib/postgresql/data
        healthcheck:
          test: ["CMD-SHELL", "pg_isready -U squad"]
          interval: 5s
          timeout: 3s
          retries: 5
        restart: unless-stopped
        networks:
          - squad-network
    ```
  - [ ] 1.2: Verificar indentação YAML

- [ ] **Task 2:** Atualizar .env.example com PostgreSQL password (AC: #4)
  - [ ] 2.1: Adicionar ao `.env.example`:
    ```
    # PostgreSQL (Story 0.4)
    POSTGRES_PASSWORD=dev_password
    ```
  - [ ] 2.2: Criar `.env` local (se não existe): `cp .env.example .env`

- [ ] **Task 3:** Testar PostgreSQL standalone (AC: #1, #6)
  - [ ] 3.1: Start: `docker-compose up -d postgres`
  - [ ] 3.2: Verificar logs: `docker logs squad-postgres` (deve mostrar "database system is ready")
  - [ ] 3.3: Verificar healthcheck: `docker inspect squad-postgres | grep Health`
  - [ ] 3.4: Testar conexão: `psql -h localhost -U squad -d squad_api` (password: dev_password)

- [ ] **Task 4:** Testar persistência (AC: #5, persistência)
  - [ ] 4.1: Conectar: `psql -h localhost -U squad -d squad_api`
  - [ ] 4.2: Criar table test:
    ```sql
    CREATE TABLE test_persistence (
      id SERIAL PRIMARY KEY,
      message TEXT
    );
    INSERT INTO test_persistence (message) VALUES ('Squad API rocks');
    SELECT * FROM test_persistence;
    \q
    ```
  - [ ] 4.3: Stop: `docker-compose stop postgres`
  - [ ] 4.4: Start: `docker-compose start postgres`
  - [ ] 4.5: Verificar dados persistem:
    ```bash
    psql -h localhost -U squad -d squad_api -c "SELECT * FROM test_persistence;"
    ```
  - [ ] 4.6: Limpar: `psql -h localhost -U squad -d squad_api -c "DROP TABLE test_persistence;"`

- [ ] **Task 5:** Documentar PostgreSQL no README (AC: validação)
  - [ ] 5.1: Adicionar à seção Infrastructure:
    ```markdown
    ### PostgreSQL (Audit Logs & Persistence)
    
    ```bash
    # Start PostgreSQL
    docker-compose up -d postgres
    
    # Connect
    psql -h localhost -U squad -d squad_api
    # Password: check .env file (default: dev_password)
    
    # Check status
    docker ps | grep postgres
    docker logs squad-postgres
    ```
    
    **Configuration:**
    - Port: 5432
    - Database: squad_api
    - User: squad
    - Password: Set in `.env` (POSTGRES_PASSWORD)
    - Data: `./data/postgres/` (gitignored)
    ```

- [ ] **Task 6:** Validação final (AC: all)
  - [ ] 6.1: Clean restart:
    ```bash
    docker-compose down
    docker-compose up -d postgres
    sleep 10
    psql -h localhost -U squad -d squad_api -c "SELECT version();"
    ```
  - [ ] 6.2: Verificar volume criado: `ls -lh data/postgres/`
  - [ ] 6.3: Commit: `git add docker-compose.yaml .env.example README.md && git commit -m "Add PostgreSQL service (Story 0.4)"`

## Dev Notes

### Architecture Decisions

**Decision: PostgreSQL 15 Alpine**
- Image: `postgres:15-alpine` (~230MB vs ~380MB debian)
- Version: 15 (latest stable, JSON improvements)
- [Source: docs/architecture.md#Decision-Summary]

**Decision: Password via Environment Variable**
- Use `${POSTGRES_PASSWORD:-dev_password}`
- Allows override via `.env` file
- Default for local dev: `dev_password`
- Production: Override with strong password
- [Source: docs/architecture.md#Security-Architecture]

**Use Cases:**
- Epic 9: Audit logs (audit_logs table)
- Future: User accounts, project metadata
- [Source: docs/architecture.md#Data-Architecture - PostgreSQL]

### PostgreSQL Schema (Future)

**Audit Logs Table (Story 9.3):**
```sql
CREATE TABLE audit_logs (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  request_id VARCHAR(100),
  user_id VARCHAR(100),
  agent VARCHAR(50),
  provider VARCHAR(50),
  action TEXT,
  status VARCHAR(20),
  latency_ms INTEGER,
  tokens_input INTEGER,
  tokens_output INTEGER
);
```

### Common Issues

**Issue 1: Port 5432 already in use**
- Solution: Stop local PostgreSQL or change port

**Issue 2: Permission denied on data/postgres/**
- Solution: `sudo chown -R $(whoami) data/postgres/`

**Issue 3: Password authentication failed**
- Check `.env` file has POSTGRES_PASSWORD
- Verify docker-compose.yaml references `${POSTGRES_PASSWORD}`

### References

- [Architecture - Deployment](docs/architecture.md#Deployment-Architecture)
- [Architecture - Data Models](docs/architecture.md#Data-Architecture)
- [Epic 9 - Story 9.3](docs/epics.md#Story-9.3) - Audit Logs table

### Learnings from Previous Story

**From Story 0-3-docker-compose-redis-setup (Status: drafted)**

Expected from 0.3:
- `docker-compose.yaml` já existe com network `squad-network`
- Pattern estabelecido: healthcheck, restart, volumes

**For This Story:**
- Seguir mesmo pattern de Docker service
- Usar mesma network (squad-network)
- PostgreSQL e Redis side-by-side

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

_To be filled by dev agent_

### Debug Log References

_To be filled by dev agent_

### Completion Notes List

_To be filled by dev agent - document:_
- PostgreSQL version: `docker exec squad-postgres psql -U squad -d squad_api -c "SELECT version();"`
- Data directory size: `du -sh data/postgres/`
- Connection test results

### File List

_To be filled by dev agent:_
- MODIFIED: docker-compose.yaml
- MODIFIED: .env.example
- MODIFIED: README.md

---

**Change Log:**
- 2025-11-13: Story drafted by SM Agent (Bob)

