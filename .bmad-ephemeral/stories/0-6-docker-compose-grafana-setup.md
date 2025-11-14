# Story 0.6: Docker Compose - Grafana Setup

Status: drafted

## Story

As a desenvolvedor,
I want Grafana rodando via Docker Compose,
so that dashboards estejam disponíveis desde o início.

## Acceptance Criteria

1. ✅ Grafana roda em `localhost:3000`
2. ✅ Usa imagem `grafana/grafana:latest`
3. ✅ Datasource Prometheus auto-configured via provisioning
4. ✅ Dashboards pré-carregados (structure ready, dashboards em Epic 6)
5. ✅ Login: admin / password from env (default: admin)
6. ✅ Volume persistente: `./data/grafana:/var/lib/grafana`
7. ✅ UI acessível: `http://localhost:3000`
8. ✅ Depends on prometheus (start order)

## Tasks / Subtasks

- [ ] **Task 1:** Criar provisioning configs
  - [ ] 1.1: Criar `config/grafana/datasources/prometheus.yaml`:
    ```yaml
    apiVersion: 1
    datasources:
      - name: Prometheus
        type: prometheus
        access: proxy
        url: http://prometheus:9090
        isDefault: true
    ```
  - [ ] 1.2: Criar placeholder `config/grafana/dashboards/.gitkeep` (dashboards vêm em Epic 6)

- [ ] **Task 2:** Adicionar serviço Grafana ao docker-compose.yaml
  - [ ] 2.1: Adicionar serviço:
    ```yaml
      grafana:
        image: grafana/grafana:latest
        container_name: squad-grafana
        ports:
          - "3000:3000"
        environment:
          - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
        volumes:
          - ./config/grafana/datasources:/etc/grafana/provisioning/datasources
          - ./config/grafana/dashboards:/etc/grafana/provisioning/dashboards
          - ./data/grafana:/var/lib/grafana
        depends_on:
          - prometheus
        restart: unless-stopped
        networks:
          - squad-network
    ```

- [ ] **Task 3:** Atualizar .env.example
  - [ ] 3.1: Adicionar `GRAFANA_PASSWORD=admin` ao `.env.example`

- [ ] **Task 4:** Testar Grafana
  - [ ] 4.1: Start: `docker-compose up -d grafana`
  - [ ] 4.2: Login: `http://localhost:3000` (admin/admin)
  - [ ] 4.3: Verificar datasource: Configuration → Data Sources → Prometheus (should be green)
  - [ ] 4.4: Test query: Explore → Prometheus → `up{job="squad-api"}`

- [ ] **Task 5:** Commit
  - [ ] 5.1: `git add config/grafana/ docker-compose.yaml .env.example && git commit -m "Add Grafana (Story 0.6)"`

## Dev Notes

**Dashboards (Epic 6):** Success Rate, Rate Limiting, Performance, Cost  
**Datasource:** Prometheus (auto-configured via provisioning)  
**Alerts:** Configured in Epic 6  

[Source: docs/architecture.md#Epic-6]

## Dev Agent Record

### Context Reference
<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used
_To be filled by dev agent_

### Completion Notes List
_To be filled by dev agent_

### File List
- NEW: config/grafana/datasources/prometheus.yaml
- NEW: config/grafana/dashboards/.gitkeep
- MODIFIED: docker-compose.yaml
- MODIFIED: .env.example

---

**Change Log:**
- 2025-11-13: Story drafted by SM Agent (Bob)

