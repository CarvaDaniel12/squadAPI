# Story 0.7: FastAPI Application Skeleton

Status: drafted

## Story

As a desenvolvedor,
I want FastAPI app básico rodando,
so that tenho entrypoint para adicionar endpoints.

## Acceptance Criteria

1. ✅ FastAPI app roda em `localhost:8000`
2. ✅ Endpoint `/health` retorna `{"status": "ok"}`
3. ✅ Endpoint `/metrics` retorna Prometheus metrics (vazio inicialmente)
4. ✅ Swagger docs acessível em `/docs`
5. ✅ CORS habilitado (development mode)
6. ✅ Comando: `uvicorn src.main:app --reload`
7. ✅ File: `src/main.py` criado

## Tasks / Subtasks

- [ ] **Task 1:** Criar src/main.py com FastAPI skeleton
  - [ ] 1.1: Criar `src/main.py`:
    ```python
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from prometheus_client import make_asgi_app
    
    app = FastAPI(
        title="Squad API",
        version="0.1.0",
        description="Multi-Agent LLM Orchestration - Transforms external LLMs into specialized BMad agents"
    )
    
    # CORS (development)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Production: specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health")
    async def health():
        """Health check endpoint"""
        return {
            "status": "ok",
            "service": "squad-api",
            "version": "0.1.0"
        }
    
    # Mount Prometheus metrics
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    if __name__ == "__main__":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    ```

- [ ] **Task 2:** Testar FastAPI localmente
  - [ ] 2.1: Ativar venv: `source venv/bin/activate`
  - [ ] 2.2: Start app: `uvicorn src.main:app --reload`
  - [ ] 2.3: Verificar logs: "Application startup complete"
  - [ ] 2.4: Test health: `curl http://localhost:8000/health`
  - [ ] 2.5: Acessar docs: `http://localhost:8000/docs`
  - [ ] 2.6: Verificar metrics: `curl http://localhost:8000/metrics` (deve retornar texto Prometheus format)

- [ ] **Task 3:** Atualizar README com run instructions
  - [ ] 3.1: Adicionar seção "Running Locally":
    ```markdown
    ## Running Locally
    
    ```bash
    # Activate venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    
    # Start Squad API
    uvicorn src.main:app --reload
    
    # Test
    curl http://localhost:8000/health
    
    # Access docs
    open http://localhost:8000/docs
    ```
    ```

- [ ] **Task 4:** Commit
  - [ ] 4.1: `git add src/main.py README.md && git commit -m "Add FastAPI skeleton (Story 0.7)"`

## Dev Notes

**Endpoints (future):**
- `/api/v1/agent/execute` - Epic 1
- `/api/v1/agents/available` - Epic 1
- `/api/v1/providers/status` - Epic 3
- `/ws/agent-status` - Epic 10

**Middleware:**
- CORS: Development allows all, production restricts
- Logging: Epic 5 adds structured logging
- Auth: Epic 9 adds API key validation

[Source: docs/architecture.md#API-Contracts]

### Learnings from Previous Stories

**Expected Dependencies (Story 0.2):**
- `fastapi==0.104.1` installed
- `uvicorn[standard]==0.24.0` installed
- `prometheus-client==0.19.0` installed

**Expected Infrastructure (Stories 0.3-0.6):**
- Redis ready (Story 0.3) - Will connect in Epic 1
- PostgreSQL ready (Story 0.4) - Will use in Epic 9
- Prometheus ready (Story 0.5) - Now can scrape /metrics
- Grafana ready (Story 0.6) - Can visualize metrics

## Dev Agent Record

### Context Reference
<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used
_To be filled by dev agent_

### Completion Notes List
_To be filled by dev agent - document:_
- FastAPI version: `python -c "import fastapi; print(fastapi.__version__)"`
- Startup time: time from `uvicorn src.main:app` to "Application startup complete"
- Metrics format verified

### File List
- NEW: src/main.py
- MODIFIED: README.md

---

**Change Log:**
- 2025-11-13: Story drafted by SM Agent (Bob)

