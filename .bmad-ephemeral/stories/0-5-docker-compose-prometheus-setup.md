# Story 0.5: Docker Compose - Prometheus Setup

Status: drafted

## Story

As a desenvolvedor,
I want Prometheus rodando via Docker Compose,
so that metrics podem ser coletadas desde o início.

## Acceptance Criteria

1. ✅ Prometheus roda em `localhost:9090`
2. ✅ Usa imagem `prom/prometheus:latest`
3. ✅ Config file: `./config/prometheus.yml` montado no container
4. ✅ Scrape target configurado: `squad-api:8000/metrics`
5. ✅ Scrape interval: 15s
6. ✅ Volume persistente: `./data/prometheus:/prometheus`
7. ✅ UI acessível: `http://localhost:9090`
8. ✅ Connected to `squad-network`

## Tasks / Subtasks

- [ ] **Task 1:** Criar config/prometheus.yml
  - [ ] 1.1: Criar arquivo `config/prometheus.yml`:
    ```yaml
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    scrape_configs:
      - job_name: 'squad-api'
        static_configs:
          - targets: ['squad-api:8000']
        metrics_path: '/metrics'
    ```

- [ ] **Task 2:** Adicionar serviço Prometheus ao docker-compose.yaml
  - [ ] 2.1: Adicionar serviço:
    ```yaml
      prometheus:
        image: prom/prometheus:latest
        container_name: squad-prometheus
        ports:
          - "9090:9090"
        volumes:
          - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
          - ./data/prometheus:/prometheus
        command:
          - '--config.file=/etc/prometheus/prometheus.yml'
          - '--storage.tsdb.path=/prometheus'
        restart: unless-stopped
        networks:
          - squad-network
    ```

- [ ] **Task 3:** Testar Prometheus
  - [ ] 3.1: Start: `docker-compose up -d prometheus`
  - [ ] 3.2: Acessar UI: `http://localhost:9090`
  - [ ] 3.3: Verificar targets: `http://localhost:9090/targets` (squad-api estará "down" até Story 0.7)
  - [ ] 3.4: Testar query simples: `up{job="squad-api"}`

- [ ] **Task 4:** Commit
  - [ ] 4.1: `git add config/prometheus.yml docker-compose.yaml && git commit -m "Add Prometheus (Story 0.5)"`

## Dev Notes

**Use Case:** Epic 5 - Observability Foundation  
**Metrics:** Request count, latency, tokens, rate limits  
**Query Language:** PromQL  

[Source: docs/architecture.md#Observability]

## Dev Agent Record

### Context Reference
<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used
_To be filled by dev agent_

### Completion Notes List
_To be filled by dev agent_

### File List
- NEW: config/prometheus.yml
- MODIFIED: docker-compose.yaml

---

**Change Log:**
- 2025-11-13: Story drafted by SM Agent (Bob)

