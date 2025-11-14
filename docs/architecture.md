# Squad API - Architecture Document

**Author:** Dani (with Winston - Architect Agent)
**Date:** 2025-11-12
**Version:** 1.0
**Project:** Squad API - Multi-Agent LLM Orchestration

---

## Executive Summary

Squad API distribui o **BMad Method** através de uma arquitetura de orquestração multi-agente que transforma LLMs de APIs externas (Groq, Cerebras, Gemini, OpenRouter) em agentes especializados BMad (Mary/Analyst, John/PM, Alex/Architect, etc.).

**Architectural Approach:** Complete Multi-Agent Architecture (Option 3 from Technical Research)

**Key Decisions:**
- **Language:** Python 3.11+ (async-first)
- **Framework:** FastAPI (API Gateway)
- **Rate Limiting:** pyrate-limiter + Redis (Token Bucket + Sliding Window)
- **State Management:** Redis (conversations, rate limits, cache)
- **Persistence:** PostgreSQL (audit logs)
- **Observability:** Prometheus + Grafana + Slack alerts
- **Agent Context:** System prompts (3-4k tokens) + Function calling tools
- **Patterns:** Output Parsers (LangChain), Parallel Execution (CrewAI), Tool Registry

**Architecture Highlights:**
- 🎯 **Core Magic:** Function calling permite Mary via Groq executar workflows BMad completos (load_file, save_file, web_search)
- 🛡️ **Resilience:** Auto-throttling + fallback chains garantem 99.5%+ SLA
- 📊 **Observability:** Dual monitoring (Grafana técnico + Status Board humano)
- 🔧 **Config-driven:** YAML configs permitem ajustes sem código
- ♻️ **Reusable:** Modular design para uso em múltiplos projetos futuros

### Prompt Plan + Local Optimizer Flow

- Recebemos o pedido do usuário e, se `prompt_optimizer` estiver habilitado, o módulo local gera um `PromptPlan` estruturado com metadados BMAD/Agile antes de qualquer chamada remota.
- `validate_prompt_plan` (ver `tests/unit/test_plan_validator.py`) garante metodologia BMAD, provedores configurados e DAG acíclico antes de liberarmos a execução.
- O `AgentOrchestrator` resolve as tarefas especializadas em ordem topológica usando `_execute_prompt_plan`, reaproveitando os provedores configurados e registrando tokens/latência de cada resposta (`tests/unit/test_agent_orchestrator_plan.py`).
- Após todas as tarefas, `_synthesize_plan_response` encaminha os outputs para o `prompt_optimizer.synthesize` para gerar uma resposta final alinhada ao `post_processing_prompt`; se o recurso local estiver indisponível, fazemos fallback deterministicamente concatenando cada tarefa.
- Esse fluxo garante que todo pedido passe pelo mini planejador BMAD antes de consumir LLMs externos, reforçando conformidade metodológica sem depender do cliente chamar workflows corretos.

---

## Project Initialization

**First Implementation Story (Story 0.1):**

```bash
# Create project structure
mkdir -p squad-api/{src,tests,config,docs,public}
cd squad-api

# Python virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize git
git init
git add .
git commit -m "Initial Squad API structure"
```

**No starter template** - Custom Python backend with specific architecture requirements.

---

## Decision Summary

| Category | Decision | Version | Affects Epics | Rationale |
| -------- | -------- | ------- | ------------- | --------- |
| **Language** | Python | 3.11+ | All | Async-first, rich ecosystem, BMad compatibility |
| **API Framework** | FastAPI | 0.104.1+ | Epic 0, 1 | Modern async, auto OpenAPI docs, high performance |
| **Rate Limiting** | pyrate-limiter | 3.1.1+ | Epic 2 | Token Bucket + Redis backend, battle-tested |
| **HTTP Client** | aiohttp | 3.9.1+ | Epic 3 | Async, connection pooling, proven |
| **Retry Logic** | tenacity | 8.2.3+ | Epic 2, 4 | Exponential backoff, Retry-After support |
| **LLM SDK (Gemini)** | google-genai | 0.2.2+ | Epic 3 | Official SDK, type-safe, multimodal-ready (ADR-002) |
| **LLM SDK (Groq)** | groq | 0.4.1+ | Epic 3 | Function calling support, async |
| **State/Cache** | Redis | 7.0+ | Epic 0, 1, 2 | Shared state, persistence, scalable |
| **Database** | PostgreSQL | 15+ | Epic 0, 9 | Audit logs, ACID compliance |
| **Metrics** | prometheus-client | 0.19.0+ | Epic 5 | Industry standard, Grafana integration |
| **Validation** | Pydantic | 2.5.0+ | All | Type safety, output parsing (LangChain pattern) |
| **Config** | PyYAML + pydantic-settings | 6.0.1+ / 2.1.0+ | Epic 7 | Config-driven, validation |
| **Testing** | pytest + pytest-asyncio | 7.4.3+ / 0.21.1+ | All | Async support, fixtures |
| **Load Testing** | Locust | 2.17+ | Epic 9 | HTTP/WebSocket support, realistic scenarios |
| **Deployment** | Docker Compose | Latest | Epic 0, 8 | Reproducible, multi-service orchestration |
| **Monitoring UI** | HTML/JS + WebSocket | Native | Epic 10 | Simple, real-time, human-friendly |

**Versioning Strategy:** Pin all dependencies for reproducibility

---

## Project Structure

```
squad-api/
├── .github/
│   └── workflows/              # CI/CD (future)
│       └── tests.yml
├── .bmad/                      # BMad Method definitions (mounted)
│   └── bmm/
│       ├── agents/            # Mary, John, Alex definitions
│       ├── workflows/         # Research, PRD, Architecture workflows
│       └── config.yaml
├── config/
│   ├── rate_limits.yaml       # RPM, burst, window per provider
│   ├── agent_chains.yaml      # Fallback chains per agent
│   ├── providers.yaml         # API endpoints, models
│   ├── prometheus.yml         # Scrape configs
│   └── grafana/
│       ├── datasources/
│       └── dashboards/        # Pre-configured dashboards
├── data/                      # Docker volumes (gitignored)
│   ├── redis/
│   ├── postgres/
│   ├── prometheus/
│   └── grafana/
├── docs/
│   ├── runbooks/
│   │   ├── deploy.md
│   │   ├── troubleshoot.md
│   │   └── go-live.md
│   ├── adrs/
│   │   ├── ADR-001-rate-limiting-strategy.md
│   │   ├── ADR-002-gemini-sdk-vs-rest.md
│   │   ├── ADR-003-worker-boss-hierarchy.md
│   │   ├── ADR-004-function-calling-vs-mcp.md
│   │   └── ADR-005-simple-status-ui.md
│   ├── PRD.md
│   ├── epics.md
│   ├── product-brief-squad-api-2025-11-12.md
│   ├── research-technical-2025-11-12.md
│   └── architecture.md (this file)
├── logs/                      # Application logs (gitignored)
│   └── squad-api.{date}.log
├── public/                    # Static files for Status UI
│   └── status.html
├── src/
│   ├── __init__.py
│   ├── main.py               # FastAPI entrypoint
│   ├── agents/               # Epic 1: Agent Transformation
│   │   ├── __init__.py
│   │   ├── parser.py         # BMad agent file parser (Story 1.1)
│   │   ├── loader.py         # Agent loader service (Story 1.3)
│   │   ├── prompt_builder.py # System prompt builder (Story 1.4)
│   │   ├── conversation.py   # Conversation manager (Story 1.5)
│   │   ├── router.py         # Agent router (Story 1.6)
│   │   ├── orchestrator.py   # Main orchestrator (Story 1.7)
│   │   ├── context.py        # Context window manager (Story 1.9)
│   │   ├── watcher.py        # Hot-reload support (Story 1.10)
│   │   ├── fallback.py       # Fallback executor (Story 4.1)
│   │   └── quality.py        # Quality validator (Story 4.2)
│   ├── api/                  # FastAPI routes
│   │   ├── __init__.py
│   │   ├── agents.py         # /api/v1/agent/* endpoints
│   │   ├── providers.py      # /api/v1/providers/* endpoints
│   │   ├── health.py         # /health endpoint
│   │   └── websocket.py      # WebSocket for status board (Epic 10)
│   ├── config/               # Configuration management (Epic 7)
│   │   ├── __init__.py
│   │   ├── loader.py         # YAML config loader (Story 7.1)
│   │   ├── env.py            # Environment variables (Story 7.2)
│   │   └── validator.py      # Config validation (Story 7.3)
│   ├── metrics/              # Epic 5: Observability
│   │   ├── __init__.py
│   │   ├── requests.py       # Request tracking (Story 5.1)
│   │   ├── latency.py        # Latency tracking (Story 5.2)
│   │   └── tokens.py         # Token consumption (Story 5.3)
│   ├── models/               # Pydantic models
│   │   ├── __init__.py
│   │   ├── agent.py          # AgentDefinition, Persona (Story 1.2)
│   │   ├── request.py        # AgentExecutionRequest
│   │   ├── response.py       # AgentExecutionResponse (Output Parsers!)
│   │   ├── provider.py       # ProviderConfig
│   │   └── status.py         # AgentStatus (Epic 10)
│   ├── monitoring/           # Epic 10: Status tracking
│   │   ├── __init__.py
│   │   └── status_tracker.py # Agent status tracker (Story 10.3)
│   ├── providers/            # Epic 3: Provider Wrappers
│   │   ├── __init__.py
│   │   ├── base.py           # LLMProvider interface (Story 3.1)
│   │   ├── groq_provider.py  # Groq wrapper (Story 3.2)
│   │   ├── cerebras_provider.py  # Cerebras wrapper (Story 3.3)
│   │   ├── gemini_provider.py    # Gemini SDK wrapper (Story 3.4)
│   │   ├── openrouter_provider.py  # OpenRouter wrapper (Story 3.5)
│   │   ├── together_provider.py   # Together AI (optional, Story 3.6)
│   │   ├── factory.py        # Provider factory (Story 3.7)
│   │   └── retry.py          # Retry logic (Story 2.5, 2.6)
│   ├── rate_limit/           # Epic 2: Rate Limiting
│   │   ├── __init__.py
│   │   ├── limiter.py        # Token Bucket (Story 2.1)
│   │   ├── sliding_window.py # Sliding Window (Story 2.2)
│   │   ├── combined.py       # Combined limiter (Story 2.3)
│   │   ├── semaphore.py      # Global semaphore (Story 2.4)
│   │   └── throttle.py       # Auto-throttling (Stories 4.3, 4.4, 4.5)
│   ├── scheduler/            # Burst scheduling (optional)
│   │   ├── __init__.py
│   │   └── burst_scheduler.py  # Burst interleaving
│   ├── security/             # Epic 9: Security
│   │   ├── __init__.py
│   │   └── pii.py            # PII detection/sanitization (Stories 9.1, 9.2)
│   ├── tools/                # Epic 1: Function Calling (Stories 1.13-1.16)
│   │   ├── __init__.py
│   │   ├── definitions.py    # Tool definitions (Story 1.13)
│   │   ├── executor.py       # Tool executor (Story 1.14)
│   │   └── web_search.py     # Web search tool (Story 1.16)
│   ├── alerts/               # Epic 6: Alerts
│   │   ├── __init__.py
│   │   └── slack.py          # Slack notifications (Stories 6.5, 6.6)
│   └── utils/
│       ├── __init__.py
│       └── logging.py        # JSON formatter (Story 5.4)
├── tests/
│   ├── unit/                 # Unit tests
│   │   ├── test_agents/
│   │   ├── test_providers/
│   │   ├── test_rate_limit/
│   │   └── test_tools/
│   ├── integration/          # Integration tests
│   │   ├── test_agent_execution.py  # Story 1.11
│   │   ├── test_fallback.py         # Story 4.6
│   │   └── test_status_ui.py        # Story 10.6
│   ├── e2e/                  # End-to-end tests
│   │   └── test_full_system.py      # Story 8.7
│   ├── load/                 # Load tests
│   │   └── locustfile.py            # Story 9.6
│   └── conftest.py           # Pytest fixtures
├── .dockerignore
├── .env                      # Secrets (gitignored)
├── .env.example              # Template (Story 7.2)
├── .gitignore
├── docker-compose.yaml       # All services (Stories 0.3-0.8)
├── Dockerfile
├── pytest.ini
├── README.md                 # Quick Start (Story 8.2)
├── requirements.txt          # All dependencies (Story 0.2)
└── pyproject.toml           # Optional: Poetry alternative
```

**Total Lines of Code Estimated:** ~8,000-10,000 LOC (production code + tests)

---

## Epic to Architecture Mapping

| Epic | Component/Module | Key Files | Purpose |
|------|------------------|-----------|---------|
| **Epic 0** | Infrastructure | docker-compose.yaml, src/main.py | Foundation: Redis, PostgreSQL, Prometheus, Grafana, FastAPI |
| **Epic 1** | Agent Transformation | src/agents/*, src/tools/* | **CORE MAGIC:** Load BMad agents, instruct LLMs, execute workflows via tools |
| **Epic 2** | Rate Limiting | src/rate_limit/* | Token Bucket + Sliding Window, prevent 429 errors |
| **Epic 3** | Provider Wrappers | src/providers/* | Groq, Cerebras, Gemini, OpenRouter clients |
| **Epic 4** | Fallback & Resilience | src/agents/fallback.py, src/rate_limit/throttle.py | Auto-throttling, fallback chains, 99.5%+ SLA |
| **Epic 5** | Observability Foundation | src/metrics/*, src/utils/logging.py | Prometheus metrics, structured logging |
| **Epic 6** | Dashboards & Alerts | config/grafana/*, src/alerts/* | Grafana dashboards, Slack alerts |
| **Epic 7** | Configuration | src/config/*, config/*.yaml | YAML-based, Pydantic validation, hot-reload |
| **Epic 8** | Deployment & Docs | docker-compose.yaml, docs/runbooks/*, README.md | Docker Compose, runbooks, ADRs |
| **Epic 9** | Production Readiness | src/security/*, tests/load/* | PII sanitization, audit logs, load testing |
| **Epic 10** | Status UI | public/status.html, src/api/websocket.py | Simple monitoring UI (⚪🟢🟡🔴) |

---

## Technology Stack Details

### Core Technologies

**Runtime & Framework:**
```yaml
python: 3.11+
  rationale: Modern async support, type hints, performance
  features: asyncio, type annotations, structural pattern matching

fastapi: 0.104.1+
  rationale: Modern async framework, auto OpenAPI docs, high performance
  features: async endpoints, WebSocket support, dependency injection
  validation: Pydantic 2.0+ integration

uvicorn: 0.24.0+
  rationale: ASGI server for FastAPI
  features: async workers, graceful shutdown
```

**Rate Limiting & Caching:**
```yaml
redis: 7.0-alpine
  rationale: In-memory store, persistence, pub/sub
  use_cases:
    - Token buckets (rate limiting state)
    - Sliding windows (request timestamps)
    - Conversation history (agent context)
    - Agent definition cache
    - Dedup cache (SHA-256 hashes)
  persistence: RDB snapshots + AOF

pyrate-limiter: 3.1.1+
  rationale: Token Bucket algorithm, Redis backend
  features: Per-provider buckets, burst support, async-compatible
  verified: ADR-001 (Technical Research)
```

**Database:**
```yaml
postgresql: 15-alpine
  rationale: ACID compliance, JSON support, mature
  use_cases:
    - Audit logs (who did what when)
    - Future: Project metadata, user accounts
  persistence: WAL enabled, daily backups
```

**LLM Provider SDKs:**
```yaml
groq: 0.4.1+
  models: llama-3-70b-8192, llama-3-8b-8192
  rpm_limit: 12 (conservative, tested)
  features: Function calling, async support

google-genai: 0.2.2+
  models: gemini-2.5-flash, gemini-2.5-pro
  rpm_limit: 15 (flash), 2 (pro)
  features: Native tools, multimodal, 1M context
  rationale: ADR-002 chose SDK over REST

aiohttp: 3.9.1+
  use_case: Cerebras, OpenRouter (REST APIs)
  features: Async, connection pooling, timeout handling
```

**Observability:**
```yaml
prometheus-client: 0.19.0+
  metrics: Counters, Histograms, Gauges
  endpoint: /metrics

grafana: latest (Docker)
  dashboards: 4 pre-configured (Success Rate, Rate Limiting, Performance, Cost)
  datasource: Prometheus

slack_webhooks: Native httpx
  channels: #squad-api-alerts
  throttling: Max 1 alert/5min per type
```

**Development Tools:**
```yaml
pytest: 7.4.3+
  plugins: pytest-asyncio, pytest-cov
  coverage_target: 80%+

black: 23.12.0+
  config: line-length 100, target py311

ruff: 0.1.8+
  features: Fast linter, replaces flake8/isort

mypy: 1.7.1+
  config: strict mode, check untyped defs
```

### Integration Points

**1. LLM APIs (External):**
```
Squad API ←→ Groq API (llama-3-70b, llama-3-8b)
          ←→ Cerebras API (llama-3-8b)
          ←→ Gemini API (gemini-2.5-flash, gemini-2.5-pro)
          ←→ OpenRouter API (gemma-2b:free)
          ←→ Together AI API (mixtral-8x7b) [optional]

Protocol: HTTPS, JSON payloads
Auth: Bearer token (API keys)
Rate Limits: Managed by src/rate_limit/
```

**2. BMad Method Files (Mounted):**
```
Squad API ←→ .bmad/bmm/agents/*.md (agent definitions)
          ←→ .bmad/bmm/workflows/**/*.yaml (workflow definitions)
          ←→ .bmad/bmm/config.yaml (BMad config)

Access: Local filesystem (read-only via tools)
Security: Whitelist paths ['.bmad/', 'docs/', 'config/']
```

**3. Internal Services (Docker network):**
```
Squad API ←→ Redis (cache, rate limits, conversations)
          ←→ PostgreSQL (audit logs)
          ←→ Prometheus (metrics push via /metrics)

Network: squad-network (Docker internal)
Communication: TCP sockets, health checks
```

**4. External Integrations:**
```
Squad API ←→ Slack Webhooks (alerts)
          ←→ Tavily API (web search tool) [optional]

Protocol: HTTPS webhooks
Retry: Exponential backoff
```

---

## Novel Pattern Designs

### Pattern 1: Distributed BMad Method Execution

**Problem:** BMad workflows são complexos (load files, execute steps, save outputs). LLM externa (Groq) não tem acesso ao filesystem.

**Solution:** Function Calling Bridge

**Components:**

1. **Agent Definition (Local):**
   - `.bmad/bmm/agents/analyst.md` define Mary
   - Includes: persona, menu, workflows, rules

2. **System Prompt Builder:**
   - Carrega definition (3-4k tokens)
   - Builds complete prompt: "You are Mary, a Business Analyst..."
   - Includes BMad menu, rules, activation steps

3. **Tool Registry:**
   - `load_file(path)` - Read workflows, templates
   - `save_file(path, content)` - Write research reports
   - `web_search(query)` - Fetch current data
   - `update_workflow_status(workflow, file)` - Update progress tracking
   - `list_directory(path)` - Discover available files

4. **Multi-Turn Orchestrator:**
   - Turn 1: User → "Execute research" → Mary calls `load_file(workflow.yaml)`
   - Turn 2: Workflow content → Mary calls `web_search("LLM rate limiting 2025")`
   - Turn 3: Search results → Mary calls `save_file("research-report.md", content)`
   - Turn 4: Confirmation → Mary → "Research workflow complete!"

**Data Flow:**
```
User Request
    ↓
FastAPI (/api/v1/agent/execute)
    ↓
Agent Orchestrator
    ↓ (load agent definition)
.bmad/bmm/agents/analyst.md → Mary persona
    ↓ (build system prompt)
System Prompt (3-4k tokens) + Tools definition
    ↓ (call LLM)
Groq API (llama-3-70b) with tools
    ↓ (Mary decides: need workflow file)
Tool Call: load_file(".bmad/bmm/workflows/research/workflow.yaml")
    ↓ (Squad API executes tool)
Tool Executor → Read file → Return content
    ↓ (send tool result back)
Groq API (Mary receives workflow, executes steps)
    ↓ (Mary calls more tools: web_search, save_file)
Multiple tool rounds (max 10 turns)
    ↓ (final response)
Mary: "Research workflow complete! Saved to docs/research-technical-{date}.md"
```

**Why This Works:**
- Mary via Groq has FULL persona (system prompt)
- Mary can READ workflows (load_file tool)
- Mary can WRITE outputs (save_file tool)
- Mary can SEARCH web (web_search tool)
- Mary can UPDATE status (update_workflow_status tool)

**Result:** LLM externa executa workflow BMad COMPLETO, indistinguível de LLM local!

---

### Pattern 2: Hybrid Worker/Boss with Auto-Escalation

**Problem:** Different agents have different complexity needs. Using powerful model (Groq llama-3-70b, 12 RPM) for simple tasks wastes quota.

**Solution:** Intelligent tier-based routing with automatic escalation

**Components:**

1. **Agent Chains (Config):**
```yaml
# config/agent_chains.yaml
agents:
  analyst:
    - provider: cerebras
      model: llama-3-8b
      tier: worker
      rpm: 60
      fallback_conditions: [rate_limit, low_confidence]

    - provider: groq
      model: llama-3-70b
      tier: boss
      rpm: 12
      fallback_conditions: [rate_limit]

  architect:
    - provider: groq
      model: llama-3-70b
      tier: boss
      rpm: 12
      fallback_conditions: [rate_limit, low_confidence]

    - provider: gemini
      model: gemini-2.5-pro
      tier: boss-ultimate
      rpm: 2
      fallback_conditions: []
```

2. **Quality Validator:**
   - Checks response length, format, confidence markers
   - Worker tier: Basic validation (>50 chars, valid format)
   - Boss tier: Deeper validation (>200 chars, coherent structure)

3. **Fallback Executor:**
   - Try worker first (Cerebras 60 RPM - fast and abundant)
   - If quality low or rate limited → Escalate to boss (Groq 12 RPM)
   - If boss fails → Boss-ultimate (Gemini Pro 2 RPM)

**Benefits:**
- 5x more throughput (Cerebras 60 RPM vs Groq 12 RPM)
- Cost optimization (all free-tier, but quota-limited)
- Quality assurance (auto-escalate if worker insufficient)
- Resilience (fallback chains guarantee 99.5%+ SLA)

---

### Pattern 3: LangChain-Inspired Output Parsers

**Problem:** LLM responses are unstructured. Need consistent, type-safe outputs for downstream processing.

**Solution:** Pydantic Output Parsers (LangChain pattern)

**Implementation:**
```python
# src/models/response.py (Output Parser Models)
from pydantic import BaseModel, Field
from typing import List, Optional

class ResearchOutput(BaseModel):
    """Output parser for Research workflow"""
    findings: List[str] = Field(..., description="Key findings from research")
    recommendations: str = Field(..., description="Final recommendation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    sources: List[str] = Field(..., description="URLs of sources cited")

class ArchitectureOutput(BaseModel):
    """Output parser for Architecture workflow"""
    decisions: List[dict] = Field(..., description="Architectural decisions made")
    diagrams: Optional[str] = Field(None, description="ASCII diagrams or descriptions")
    risks: List[str] = Field(..., description="Identified risks")

class CodeReviewOutput(BaseModel):
    """Output parser for Code Review workflow"""
    status: str = Field(..., description="approved|changes_requested|rejected")
    issues: List[dict] = Field(..., description="List of issues found")
    suggestions: List[str] = Field(..., description="Improvement suggestions")

# Usage in orchestrator:
response_text = await provider.call(...)
parsed = ResearchOutput.model_validate_json(response_text)  # Type-safe!
```

**Benefits:**
- Type safety (Pydantic validation)
- Consistent structure across all agent responses
- Easy to test (validate against schema)
- LLM can be instructed: "Return JSON matching this schema"

---

### Pattern 4: CrewAI-Style Parallel Task Execution

**Problem:** Sequential execution wastes time. Multiple agents could work simultaneously.

**Solution:** Async parallel execution with task dependencies

**Implementation:**
```python
# src/scheduler/parallel.py (CrewAI pattern)
from typing import List
import asyncio

class TaskScheduler:
    """Inspired by CrewAI process orchestration"""

    async def execute_parallel(self, tasks: List[AgentTask]) -> List[AgentResponse]:
        """Execute independent tasks in parallel"""
        # Group by dependencies
        independent = [t for t in tasks if not t.depends_on]
        dependent = [t for t in tasks if t.depends_on]

        # Execute independent tasks in parallel
        results = {}
        if independent:
            parallel_results = await asyncio.gather(*[
                self.orchestrator.execute(task)
                for task in independent
            ])
            results.update({t.id: r for t, r in zip(independent, parallel_results)})

        # Execute dependent tasks (can also parallelize if no cross-dependencies)
        for task in dependent:
            # Wait for dependencies
            dep_results = {dep: results[dep] for dep in task.depends_on}

            # Execute with dependency results in context
            result = await self.orchestrator.execute(task, context=dep_results)
            results[task.id] = result

        return list(results.values())

# Usage example:
tasks = [
    AgentTask(id="architect", agent="architect", task="Design system", depends_on=[]),
    AgentTask(id="dev1", agent="dev", task="Implement API", depends_on=["architect"]),
    AgentTask(id="dev2", agent="dev", task="Implement DB", depends_on=["architect"]),
    AgentTask(id="qa", agent="qa", task="Write tests", depends_on=["dev1", "dev2"])
]

results = await scheduler.execute_parallel(tasks)
# Architect runs first
# Dev1 + Dev2 run in parallel after architect completes
# QA runs after both devs complete
```

**Benefits:**
- Minimize total execution time
- Respect task dependencies
- Maximize throughput utilization

---

## Implementation Patterns

These patterns ensure consistent implementation across all AI agents:

### Pattern Category: Function Calling & Tools

**Pattern:** Tool definitions follow OpenAI-compatible schema

**Convention:**
```json
{
  "type": "function",
  "function": {
    "name": "snake_case_name",
    "description": "Clear description of what tool does",
    "parameters": {
      "type": "object",
      "properties": {...},
      "required": [...]
    }
  }
}
```

**Example:**
```python
{
  "type": "function",
  "function": {
    "name": "load_file",
    "description": "Load workflow, agent, or config file from project filesystem. Only use for files in .bmad/, docs/, or config/ directories.",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "type": "string",
          "description": "File path relative to project root (e.g., '.bmad/bmm/workflows/research/workflow.yaml')"
        }
      },
      "required": ["path"]
    }
  }
}
```

**Enforcement:** All agents MUST use these exact tool definitions. Provider wrappers validate tool_calls against registry.

---

### Pattern Category: Output Structure (LangChain-Inspired)

**Pattern:** Structured responses using Pydantic models

**Convention:**
- Define `{WorkflowName}Output` model for each workflow type
- LLM instructed to return JSON matching schema
- Squad API validates with `model_validate_json()`
- If validation fails → retry with schema reminder

**Example:**
```python
# In system prompt for Mary (Research workflow):
"""
When completing research workflow, return JSON matching this schema:
{
  "findings": ["Finding 1", "Finding 2", ...],
  "recommendations": "Primary recommendation with rationale",
  "confidence": 0.85,
  "sources": ["URL1", "URL2", ...]
}
"""

# In Squad API:
response_text = await groq.call(...)
try:
    parsed = ResearchOutput.model_validate_json(response_text)
    # Type-safe access: parsed.findings, parsed.confidence
except ValidationError:
    # Retry with schema reminder
    await groq.call(..., additional_instruction="Follow JSON schema exactly")
```

**Enforcement:** All workflow outputs MUST have Pydantic model. Define in `src/models/outputs/`.

---

### Pattern Category: Async Execution

**Pattern:** All I/O operations are async

**Convention:**
- LLM calls: `async def call(...)` with aiohttp/async SDKs
- Redis operations: `redis.asyncio` client
- Database: `asyncpg` for PostgreSQL
- Tool execution: `async def execute(...)`
- Rate limiting: Async context managers

**Example:**
```python
# GOOD: Async all the way
async def execute_agent(request):
    async with global_semaphore.acquire():
        async with rate_limiter.acquire(provider):
            async with redis_client.pipeline() as pipe:
                await pipe.set(key, value)
                response = await provider.call(...)
                await pipe.execute()
    return response

# BAD: Blocking calls
def execute_agent_bad(request):  # ❌ Not async
    redis_client.set(key, value)  # ❌ Blocking
    response = requests.post(...)  # ❌ Blocking
```

**Enforcement:** Code review, mypy checks for async consistency.

---

## Consistency Rules

### Naming Conventions

**Files & Modules:**
```python
# Files: snake_case
agent_parser.py
groq_provider.py
rate_limiter.py

# Classes: PascalCase
class AgentParser:
class GroqProvider:
class RateLimiter:

# Functions/methods: snake_case
def parse_agent_file():
async def call_llm():

# Constants: UPPER_SNAKE_CASE
MAX_CONCURRENT = 12
WHITELIST_PATHS = ['.bmad/', 'docs/']
```

**Database (PostgreSQL):**
```sql
-- Tables: snake_case, plural
CREATE TABLE audit_logs (...);
CREATE TABLE agent_executions (...);

-- Columns: snake_case
user_id, agent_name, created_at

-- Foreign keys: explicit naming
fk_user_id, fk_agent_id
```

**Redis Keys:**
```
# Pattern: {namespace}:{entity}:{id}
agent:analyst
conversation:user123:analyst
bucket:groq
window:cerebras
spike:gemini
agent_status:pm
```

**API Endpoints:**
```
# Pattern: /api/v{version}/{resource}/{action}
POST /api/v1/agent/execute
GET /api/v1/agents/available
GET /api/v1/providers/status
GET /health
GET /metrics
WS /ws/agent-status
```

**Config Files:**
```yaml
# Files: snake_case.yaml
rate_limits.yaml
agent_chains.yaml
providers.yaml

# Keys: snake_case
agents:
  analyst:
    primary: groq/llama-3-70b
```

---

### Code Organization

**Pattern:** Feature-based organization, not layer-based

```python
# GOOD: Feature modules
src/agents/          # All agent-related code together
src/rate_limit/      # All rate limiting together
src/providers/       # All provider wrappers together

# BAD: Layer-based
src/controllers/     # ❌ Mixed concerns
src/services/        # ❌ Mixed concerns
src/repositories/    # ❌ Mixed concerns
```

**Test Organization:** Mirror source structure
```
tests/unit/test_agents/parser_test.py  ← mirrors src/agents/parser.py
tests/unit/test_providers/groq_test.py ← mirrors src/providers/groq_provider.py
```

---

### Error Handling

**Pattern:** Custom exception hierarchy + FastAPI exception handlers

**Convention:**
```python
# src/exceptions.py
class SquadAPIException(Exception):
    """Base exception"""
    pass

class AgentNotFoundException(SquadAPIException):
    """Agent ID not found"""
    pass

class RateLimitExceeded(SquadAPIException):
    """Provider rate limit hit"""
    def __init__(self, provider: str, retry_after: Optional[int] = None):
        self.provider = provider
        self.retry_after = retry_after

class AllProvidersFailed(SquadAPIException):
    """All providers in fallback chain failed"""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id

# FastAPI handlers
@app.exception_handler(AgentNotFoundException)
async def agent_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "agent_not_found",
            "message": f"Agent '{exc.agent_id}' not found",
            "available_agents": await get_available_agents()
        }
    )
```

**Enforcement:** All exceptions inherit from `SquadAPIException`. Use FastAPI handlers for consistent error responses.

---

### Logging Strategy

**Pattern:** Structured JSON logging with context propagation

**Convention:**
```python
# src/utils/logging.py
import logging
import json
from datetime import datetime
from contextvars import ContextVar

# Context variables for request tracing
request_id_ctx: ContextVar[str] = ContextVar('request_id', default='')
agent_id_ctx: ContextVar[str] = ContextVar('agent_id', default='')

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
            "agent": agent_id_ctx.get(),
        }

        # Add extra fields from record
        for key in ['provider', 'status', 'latency_ms', 'tokens_in', 'tokens_out']:
            if hasattr(record, key):
                log_data[key] = getattr(record, key)

        return json.dumps(log_data)

# Usage:
logger.info(
    "Agent execution success",
    extra={
        "provider": "groq",
        "status": "success",
        "latency_ms": 1850,
        "tokens_in": 2500,
        "tokens_out": 1200
    }
)
# Output: {"timestamp":"...","level":"INFO","message":"Agent execution success","request_id":"req_123","agent":"analyst","provider":"groq",...}
```

**Log Levels:**
- DEBUG: Tool calls, internal state changes
- INFO: Successful operations, workflow completions
- WARN: Auto-throttling, fallbacks, retries
- ERROR: Failures, exceptions

**Rotation:** Daily, keep 30 days

**Enforcement:** All logging MUST use JSONFormatter. No print() statements in production code.

---

## Data Architecture

### Redis Data Models

**1. Agent Definitions (Cache):**
```
Key: agent:{agent_id}
Value: JSON (AgentDefinition serialized)
TTL: 3600s (1 hour)
Example: agent:analyst → {"id":"analyst","name":"Mary",...}
```

**2. Conversation History:**
```
Key: conversation:{user_id}:{agent_id}
Value: JSON array of messages
TTL: 3600s (1 hour inactivity)
Max size: 50 messages (rolling)
Example: conversation:dani:analyst → [{"role":"user","content":"..."},...]
```

**3. Token Buckets (Rate Limiting):**
```
Key: bucket:{provider}
Value: pyrate-limiter RedisBucket state
TTL: None (persistent)
Example: bucket:groq → (internal pyrate-limiter format)
```

**4. Sliding Windows:**
```
Key: window:{provider}
Type: Sorted Set
Score: unix timestamp
Member: request_id (UUID)
TTL: 60s auto-cleanup
Example: window:groq → {req_123: 1699800000, req_124: 1699800001, ...}
```

**5. 429 Spike Tracking:**
```
Key: spike:{provider}
Type: Sorted Set
Score: unix timestamp
Member: error_id (UUID)
TTL: 60s
Example: spike:groq → {err_1: 1699800000, err_2: 1699800005, ...}
```

**6. Agent Status:**
```
Key: agent_status:{agent_id}
Type: Hash
Fields: status, status_color, current_task, last_active, latency_ms
TTL: None (persistent, updated on each execution)
Example: agent_status:analyst → {status: "active", status_color: "green", ...}
```

### PostgreSQL Data Models

**1. Audit Logs:**
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    request_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(100),
    agent VARCHAR(50) NOT NULL,
    agent_name VARCHAR(100),
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100),
    action TEXT NOT NULL,
    status VARCHAR(20) NOT NULL,  -- success|failure|rate_limited
    latency_ms INTEGER,
    tokens_input INTEGER,
    tokens_output INTEGER,
    error_message TEXT,
    fallback_used BOOLEAN DEFAULT FALSE,
    tool_calls_count INTEGER DEFAULT 0
);

CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_agent ON audit_logs(agent);
CREATE INDEX idx_audit_provider ON audit_logs(provider);
CREATE INDEX idx_audit_status ON audit_logs(status);
```

**2. Future Tables (Post-MVP):**
```sql
-- User management (Phase 3: Multi-user)
CREATE TABLE users (...);

-- Project contexts (Phase 2: Multiple projects)
CREATE TABLE projects (...);

-- MCP Index metadata (Phase 2: RAG)
CREATE TABLE indexed_documents (...);
```

---

## API Contracts

### REST Endpoints

**POST /api/v1/agent/execute**

Execute BMad agent via LLM externa

**Request:**
```json
{
  "agent": "analyst",
  "task": "Execute research workflow for LLM rate limiting",
  "context": {
    "project": "squad-api",
    "sprint_id": 42
  },
  "mode": "normal"  // or "yolo"
}
```

**Response (Success):**
```json
{
  "agent": "analyst",
  "agent_name": "Mary",
  "provider": "groq",
  "model": "llama-3-70b",
  "response": "Research workflow complete! Saved to docs/research-technical-2025-11-12.md",
  "metadata": {
    "request_id": "req_abc123",
    "latency_ms": 1850,
    "tokens_input": 2500,
    "tokens_output": 1200,
    "fallback_used": false,
    "tool_calls_count": 5,
    "turns": 4
  }
}
```

**Response (Error):**
```json
{
  "error": "all_providers_failed",
  "message": "All providers failed for agent 'analyst'",
  "details": {
    "cerebras": "Rate limit exceeded (429)",
    "groq": "Connection timeout"
  },
  "suggestions": [
    "Wait 60s and retry",
    "Check provider status: GET /api/v1/providers/status"
  ]
}
```

**GET /api/v1/agents/available**

List all BMad agents

**Response:**
```json
{
  "count": 8,
  "agents": [
    {
      "id": "analyst",
      "name": "Mary",
      "title": "Business Analyst",
      "icon": "📊",
      "status": "available",
      "provider": "groq",
      "model": "llama-3-70b",
      "workflows": ["research", "product-brief", "workflow-init", "workflow-status", "domain-research", "brainstorm-project", "party-mode"],
      "tools_enabled": true
    },
    ...
  ]
}
```

**GET /api/v1/providers/status**

Provider health and rate limit status

**Response:**
```json
{
  "providers": {
    "groq": {
      "status": "healthy",
      "rpm_limit": 12,
      "rpm_current": 3,
      "bucket_tokens": 9,
      "window_occupancy": "3/12 (last 60s)",
      "last_429": null,
      "latency_avg_ms": 1850
    },
    "cerebras": {
      "status": "healthy",
      "rpm_limit": 60,
      "rpm_current": 15,
      "bucket_tokens": 45,
      "window_occupancy": "15/60 (last 60s)",
      "last_429": null,
      "latency_avg_ms": 980
    }
  },
  "aggregate": {
    "healthy": 4,
    "degraded": 0,
    "unavailable": 0,
    "total_rpm_available": 87,
    "throughput_current": 18
  }
}
```

**GET /health**

System health check

**Response:**
```json
{
  "status": "healthy",  // healthy|degraded|unhealthy
  "timestamp": "2025-11-12T10:30:45Z",
  "uptime_seconds": 86400,
  "components": {
    "redis": {"status": "healthy", "latency_ms": 2},
    "postgres": {"status": "healthy", "latency_ms": 5},
    "prometheus": {"status": "healthy"},
    "providers": {
      "groq": {"status": "healthy", "rpm_available": 9},
      "cerebras": {"status": "healthy", "rpm_available": 55},
      "gemini": {"status": "healthy", "rpm_available": 12},
      "openrouter": {"status": "degraded", "rpm_available": 0}
    }
  }
}
```

### WebSocket Endpoint

**WS /ws/agent-status**

Real-time agent status updates

**Message Format (Server → Client):**
```json
[
  {
    "id": "analyst",
    "name": "Mary",
    "title": "Business Analyst",
    "icon": "📊",
    "status": "active",
    "status_color": "green",
    "provider": "groq",
    "model": "llama-3-70b",
    "current_task": "Executing research workflow",
    "latency_ms": 1850,
    "last_active": "2025-11-12T10:30:45Z",
    "uptime": "2h 34min"
  },
  {
    "id": "pm",
    "name": "John",
    "title": "Product Manager",
    "icon": "📋",
    "status": "idle",
    "status_color": "gray",
    "provider": "cerebras",
    "model": "llama-3-8b",
    "last_active": "2025-11-12T09:45:12Z"
  },
  ...
]
```

**Update Triggers:**
- Agent execution starts → status: active
- Agent execution completes → status: idle (after 5s)
- Latency > target → status: degraded
- Execution fails → status: failed
- Fallback activated → update provider field

---

## Security Architecture

### Authentication & Authorization (MVP: Simple)

**API Key (Bearer Token):**
```python
# .env
SQUAD_API_KEY=secret_key_here

# Middleware
from fastapi.security import HTTPBearer
security = HTTPBearer()

@app.post("/api/v1/agent/execute")
async def execute_agent(request: AgentExecutionRequest, token: str = Depends(security)):
    if token.credentials != os.getenv("SQUAD_API_KEY"):
        raise HTTPException(403, "Invalid API key")
    ...
```

**Post-MVP:** OAuth2, multi-user, per-user quotas

### Secrets Management

**Environment Variables:**
```bash
# .env (gitignored)
GROQ_API_KEY=gsk_...
CEREBRAS_API_KEY=csk_...
GEMINI_API_KEY=...
OPENROUTER_API_KEY=...
TOGETHER_API_KEY=...
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
SQUAD_API_KEY=...
DATABASE_URL=postgresql://squad:dev_password@localhost:5432/squad_api
REDIS_URL=redis://localhost:6379
```

**Validation on Startup:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    groq_api_key: str
    cerebras_api_key: str
    gemini_api_key: str
    openrouter_api_key: str
    slack_webhook_url: Optional[str] = None

    class Config:
        env_file = '.env'

# Raises clear error if missing
settings = Settings()
```

### PII Sanitization

**Regex Patterns:**
```python
# src/security/pii.py
PATTERNS = {
    'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    'phone_br': r'\(\d{2}\)\s?\d{4,5}-?\d{4}',
    'cpf': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
    'credit_card': r'\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}',
}

# Auto-sanitize
def sanitize(text: str) -> str:
    for pii_type, pattern in PATTERNS.items():
        text = re.sub(pattern, f'[{pii_type.upper()}_REDACTED]', text)
    return text
```

**Applied to:** User prompts (before sending to LLM), Logs (before writing)

### Tool Execution Security

**Path Validation:**
```python
# src/tools/executor.py
WHITELIST_PATHS = ['.bmad/', 'docs/', 'config/']

def validate_path(path: str):
    # Prevent directory traversal
    if '..' in path or path.startswith('/'):
        raise SecurityError("Path traversal not allowed")

    # Whitelist check
    if not any(path.startswith(p) for p in WHITELIST_PATHS):
        raise SecurityError(f"Path '{path}' not in whitelist")

    # Additional: Check file size before reading
    if os.path.getsize(path) > 10_000_000:  # 10MB
        raise SecurityError("File too large")
```

---

## Performance Considerations

### Latency Optimization

**1. Connection Pooling:**
```python
# Reuse HTTP connections
from aiohttp import ClientSession, TCPConnector

class GroqProvider:
    def __init__(self):
        self.session = ClientSession(
            connector=TCPConnector(limit=100, limit_per_host=30)
        )

    async def call(self, ...):
        async with self.session.post(...) as resp:  # Reuses connection
            ...
```

**2. Redis Pipelining:**
```python
# Batch Redis operations
async with redis.pipeline() as pipe:
    await pipe.get(f"agent:{agent_id}")
    await pipe.get(f"conversation:{user_id}:{agent_id}")
    await pipe.zadd(f"window:{provider}", {req_id: timestamp})
    results = await pipe.execute()
```

**3. Parallel Tool Execution:**
```python
# If Mary calls multiple tools simultaneously
if len(tool_calls) > 1:
    results = await asyncio.gather(*[
        tool_executor.execute(tc.function.name, tc.function.arguments)
        for tc in tool_calls
    ])
```

### Throughput Optimization

**1. Burst Interleaving (Optional - Post-MVP):**
```python
# Distribute load uniformly across providers
# Epic 2 basic version, optional enhancement:
async def interleaved_execution(requests: List):
    # Group by provider
    by_provider = group_by_provider(requests)

    # Round-robin bursts
    while any(by_provider.values()):
        for provider in ['cerebras', 'groq', 'gemini', 'openrouter']:
            if not by_provider[provider]:
                continue

            burst = by_provider[provider][:BURST_SIZE]
            await execute_burst(provider, burst)
            by_provider[provider] = by_provider[provider][BURST_SIZE:]

            await asyncio.sleep(10)  # Wait between providers
```

**2. Dedup Cache (Future):**
```python
# SHA-256 hash of (agent_id + task) → cached response
# Avoids redundant LLM calls for identical requests
# Story for Phase 2
```

---

## Deployment Architecture

### Docker Compose Stack

```yaml
# docker-compose.yaml
version: '3.8'

networks:
  squad-network:
    driver: bridge

services:
  redis:
    image: redis:7-alpine
    container_name: squad-redis
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - squad-network

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
    networks:
      - squad-network

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
    networks:
      - squad-network

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
    networks:
      - squad-network

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
    networks:
      - squad-network
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

**One-Command Startup:**
```bash
docker-compose up
# All services: Redis, PostgreSQL, Prometheus, Grafana, Squad API
# Access: http://localhost:8000/status (Status Board)
#         http://localhost:3000 (Grafana)
#         http://localhost:9090 (Prometheus)
```

---

## Development Environment

### Prerequisites

```yaml
required:
  - Docker Desktop 4.x+ (for Docker Compose)
  - Python 3.11+ (for local development)
  - Git 2.x+

recommended:
  - VS Code (with Python extension)
  - Redis CLI (for debugging)
  - pgAdmin (for PostgreSQL inspection)

api_keys:
  required:
    - Groq API key (free tier: 12 RPM)
    - Cerebras API key (Beta: 60 RPM)
    - Gemini API key (free tier: 15 RPM Flash)
    - OpenRouter API key (free tier: 12 RPM)
  optional:
    - Together AI API key ($5 tier: 60 RPM)
    - Slack webhook URL (for alerts)
```

### Setup Commands

```bash
# 1. Clone repository
git clone https://github.com/dani/squad-api
cd squad-api

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys:
#   GROQ_API_KEY=...
#   CEREBRAS_API_KEY=...
#   GEMINI_API_KEY=...
#   etc.

# 5. Start infrastructure
docker-compose up -d redis postgres prometheus grafana

# 6. Initialize database (migrations)
python -m src.db.migrations.init

# 7. Run Squad API (development mode)
uvicorn src.main:app --reload --port 8000

# 8. Verify
curl http://localhost:8000/health
# Should return: {"status":"healthy",...}

# 9. Open Status Board
open http://localhost:8000/status
# See all 8 agents (initially idle - gray)

# 10. Test agent execution
curl -X POST http://localhost:8000/api/v1/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"agent":"analyst","task":"Olá Mary!"}'
# Status Board should show Mary: active (green)
```

---

## Architecture Decision Records (ADRs)

### ADR-001: Rate Limiting Strategy

**Status:** ACCEPTED

**Context:**
Squad API orquestra 11-13 LLM providers externos com rate limits diferentes (2-60 RPM). Testes iniciais do RL Atômico mostraram 19.6% success → 80% falhas por burst overload.

**Decision:**
Use **pyrate-limiter + Redis** com Token Bucket + Sliding Window (60s)

**Alternatives Considered:**
1. aiolimiter (in-memory) - Simples mas não escalável
2. pyrate-limiter + Redis - **CHOSEN**
3. Custom implementation - Reinventar a roda

**Rationale:**
- Token Bucket: Burst support (2-10 requests) com sustained rate enforcement
- Sliding Window: Previne "burst at minute 0" clustering
- Redis backend: Shared state entre workers, survives restarts
- Battle-tested: Used em production por empresas de alta escala

**Consequences:**
- ✅ Positive: Horizontal scaling, state persistence, proven reliability
- ❌ Negative: Redis dependency (SPOF), ~1-3ms latency overhead
- Mitigation: Redis Cluster (3 nodes) + Sentinel para HA

**References:**
- Technical Research: docs/research-technical-2025-11-12.md (Option 3)
- Your tested data: 19.6% → 100% success with redistribution

---

### ADR-002: Gemini Integration - SDK vs REST

**Status:** ACCEPTED

**Context:**
Google Gemini oferece 15 RPM (Flash), 2 RPM (Pro). Pode integrar via REST manual ou SDK oficial.

**Decision:**
Use **google-genai SDK oficial**

**Alternatives:**
1. REST API manual (httpx) - Controle total
2. google-genai SDK - **CHOSEN**

**Rationale:**
- Código 5x mais limpo (3 lines vs 15)
- Type safety (Pydantic internals)
- Official support (Google mantém atualizado)
- Multimodal-ready (future: images para VTT App)
- Error handling melhor

**Consequences:**
- ✅ Positive: Maintainability, fewer bugs, future-proof
- ❌ Negative: Dependency adicional, menos controle granular
- Neutral: SDK não tem rate limiting (adicionamos externo)

---

### ADR-003: Worker/Boss Agent Hierarchy

**Status:** ACCEPTED

**Context:**
11-13 agentes com capacidades diferentes. Cerebras (60 RPM, llama-3-8b) é 5x mais rápido que Groq (12 RPM, llama-3-70b).

**Decision:**
**Hybrid Worker/Boss + Fallback chains**

**Pattern:**
```yaml
analyst:
  - cerebras/llama-3-8b (worker, 60 RPM)  # Try cheap first
  - groq/llama-3-70b (boss, 12 RPM)       # Escalate if needed
```

**Rationale:**
- Throughput optimization: 60 RPM > 12 RPM
- Quality assurance: Auto-escalate se worker quality baixa
- Cost optimization: Fail cheap (workers use less quota)
- Resilience: Fallback se rate limit

**Consequences:**
- ✅ Positive: 5x throughput, quality guaranteed, cost-efficient
- ❌ Negative: Complexity (routing logic, quality validation)
- Implementation: Config-driven chains (easy to adjust)

---

### ADR-004: Function Calling vs MCP for MVP

**Status:** ACCEPTED (MVP), REVISIT (Post-MVP)

**Context:**
LLMs externas não têm acesso ao filesystem. Precisam executar workflows BMad (read files, save outputs).

**Decision:**
**Function Calling Direto** para MVP

**Alternatives:**
1. MCP Server com RAG/embeddings - Semantic search
2. Function Calling direto - **CHOSEN for MVP**

**Rationale:**
- **Context window:** 8 agents × 3-4k tokens = 30k total (3% de 1M) → Caber no system prompt é viável
- **Simplicity:** Function calling é native (Groq, Gemini suportam)
- **Proven:** CrewAI, LangChain usam
- **MCP overkill:** Semantic search para 8 agents é overengineering

**Post-MVP Reconsideration:**
- When: 10+ custom agents, 100+ workflows, multiple projects
- Then: MCP Server com Chroma/FAISS embeddings faz sentido
- Phase 2 candidate

**Consequences:**
- ✅ Positive: Simple, proven, fast to implement
- ❌ Negative: System prompt > 3k tokens (acceptable trade-off)
- Future: MCP Server documented como Phase 2 enhancement

**References:**
- Dani's research: LangChain + CrewAI + MCP patterns
- Tool designs: Stories 1.13-1.16

---

### ADR-005: Simple Status UI vs Grafana Only

**Status:** ACCEPTED

**Context:**
Precisa "sentir" squad trabalhando - ver Mary, John, Alex em ação.

**Decision:**
**Simple HTML/JS Status Board** (além de Grafana)

**Why Both:**
- Grafana: Técnico (metrics, graphs, P95 latencies)
- Status Board: Humano (⚪🟢🟡🔴, "Mary está trabalhando")

**Rationale:**
- Grafana é excelente para troubleshooting técnico
- Status Board é emocional - **vê** squad viva
- Quick win: 1 arquivo HTML, WebSocket simples
- Human-friendly: Cores, emojis, status claro

**Consequences:**
- ✅ Positive: User experience++, monitoring dual (técnico + humano)
- ❌ Negative: +6 stories (Epic 10)
- Trade-off: Worth it - core para "sentir o magic"

---

## Implementation Status (Epic 2-4)

**Last Updated:** 2025-11-13
**Updated By:** Winston (Architect) via course correction
**Context:** Epic 2, 3, 4 foram implementados rapidamente. Esta seção documenta as decisões arquiteturais tomadas.

### Epic 2: Rate Limiting Layer - IMPLEMENTED ✅

**Decisão Arquitetural:** Multi-Algorithm Rate Limiting

**Problema:** Evitar 429 errors de providers mantendo throughput máximo

**Solução Implementada:**
1. **Token Bucket** (pyrate-limiter): Burst support com refill rate
2. **Sliding Window** (Redis sorted sets): Precision tracking (não usa minute boundaries)
3. **Combined Limiter:** Ambos algoritmos JUNTOS (mais robusto)
4. **Global Semaphore** (asyncio): Max 12 concurrent requests (previne resource exhaustion)

**Arquitetura:**
```
Request Flow:
├─ Global Semaphore (12 slots)
│  ├─ Acquire slot (FIFO queue)
│  ├─ Token Bucket Check (burst available?)
│  ├─ Sliding Window Check (< RPM limit in last 60s?)
│  ├─ LLM Call
│  └─ Release slot
```

**Componentes Criados:**
- `src/rate_limit/token_bucket.py` - Token bucket com Redis backend
- `src/rate_limit/sliding_window.py` - Sliding window tracker
- `src/rate_limit/combined.py` - Combina ambos algoritmos
- `src/rate_limit/semaphore.py` - Global concurrency limit
- `src/providers/retry.py` - Exponential backoff com jitter
- `src/providers/retry_after.py` - Retry-After header support
- `src/config/rate_limits.py` - Config loader
- `config/rate_limits.yaml` - Rate limit configuration

**Métricas (Epic 2.8):**
- Prometheus metrics para requests, 429s, retries, tokens
- Gauges para bucket tokens, window occupancy, semaphore state
- Histograms para latency, wait time

**Testes:** 107 tests (token bucket, sliding window, combined, semaphore, retry)
**Coverage:** 65-100% per module

**Resultado:** <1% de 429 errors esperado

---

### Epic 3: Provider Wrappers - IMPLEMENTED ✅

**Decisão Arquitetural:** Abstract Provider Interface + Factory Pattern

**Problema:** Múltiplos providers (Groq, Cerebras, Gemini, OpenRouter) com APIs diferentes

**Solução Implementada:**
1. **LLMProvider Abstract Interface:** Todos providers implementam mesma interface
2. **Provider Factory:** Cria providers dinamicamente de YAML config
3. **Dual Calling Convention:** Suporta `call(system, user)` E `call(messages=[])`

**Interface Padronizada:**
```python
class LLMProvider(ABC):
    @abstractmethod
    async def call(
        system_prompt: str = None,
        user_prompt: str = None,
        messages: list = None,  # OpenAI format
        max_tokens: int = None,
        temperature: float = None
    ) -> LLMResponse

    @abstractmethod
    async def health_check() -> bool
```

**Providers Implementados:**
- **Groq** (groq SDK): Llama-3.3-70B-Versatile (30 RPM, ~1200ms avg)
- **Cerebras** (aiohttp REST): Llama-3.1-8B (30 RPM, ~560ms avg, **65% FASTER!**)
- **Gemini** (google-genai SDK): Gemini 2.0 Flash (15 RPM, ~1900ms avg)
- **OpenRouter** (aiohttp REST): Auto-routing free models (20 RPM, ~2200ms avg)
- **Stub Provider:** Para testes (no API calls)

**Arquitetura:**
```
ProviderFactory
├─ Loads: config/providers.yaml
├─ Creates: Provider instances (Groq, Cerebras, Gemini, OpenRouter)
├─ Validates: API keys from environment
└─ Returns: Dict[provider_name -> LLMProvider instance]

Orchestrator
├─ Receives: providers dict
├─ Router selects: Optimal provider for agent
├─ Calls: provider.call(messages=[...])
└─ Returns: LLMResponse (content, tokens, latency)
```

**Componentes Criados:**
- `src/providers/base.py` - Abstract LLMProvider
- `src/providers/groq_provider.py` - Groq wrapper
- `src/providers/cerebras_provider.py` - Cerebras wrapper
- `src/providers/gemini_provider.py` - Gemini wrapper
- `src/providers/openrouter_provider.py` - OpenRouter wrapper
- `src/providers/stub_provider.py` - Test provider
- `src/providers/factory.py` - Provider factory
- `src/models/provider.py` - Provider models
- `config/providers.yaml` - Provider configuration

**Testes:** 46 tests (base, stub, groq mocked)
**Coverage:** 0-98% (alguns providers não exercitados ainda sem API keys reais)

**Throughput Agregado:** 95 RPM (30+30+15+20)

---

### Epic 4: Fallback & Resilience - IMPLEMENTED ✅

**Decisão Arquitetural:** Automatic Fallback Chains + Quality-Based Escalation + Auto-Throttling

**Problema:** Garantir 99.5%+ SLA mesmo com provider failures

**Solução Implementada:**
1. **Fallback Chain Executor:** Auto-retry com providers alternativos
2. **Quality Validator:** Detecta respostas ruins e escala para provider melhor
3. **Auto-Throttling:** Detecta spikes de 429 e reduz RPM automaticamente

**Arquitetura de Fallback:**
```
Request → Primary Provider (e.g., Groq)
  ├─ Success → Return response ✅
  ├─ 429 Error → Try Fallback #1 (Cerebras)
  │  ├─ Success → Return response ✅
  │  └─ 429 Error → Try Fallback #2 (Gemini)
  │     ├─ Success → Return response ✅
  │     └─ 429 Error → Try Fallback #3 (OpenRouter)
  │        ├─ Success → Return response ✅
  │        └─ Error → AllProvidersFailed ❌
```

**Quality Escalation:**
```
Worker Provider (Cerebras 8B)
  ├─ Response received
  ├─ Quality Validator checks:
  │  ├─ Length > 50 chars?
  │  ├─ No error markers ("I cannot", "I don't know")?
  │  ├─ No corruption?
  │  └─ Quality score > 0.6?
  ├─ IF quality BAD:
  │  └─ Auto-escalate to Boss Provider (Groq 70B)
  └─ IF quality OK:
     └─ Return response
```

**Auto-Throttling:**
```
Spike Detection (3+ 429s in 60s):
  ├─ Reduce RPM by 20%
  ├─ Log throttle event
  └─ Update rate limiter config

Restore Logic (stable for 5 min):
  ├─ Increase RPM by 10%
  ├─ Cap at original RPM
  └─ Update rate limiter config
```

**Componentes Criados:**
- `src/agents/fallback.py` - Fallback chain executor
- `src/agents/quality.py` - Quality validator & escalation
- `src/rate_limit/auto_throttle.py` - Auto-throttling system
- `config/agent_chains.yaml` - Fallback chain configuration
- `config/agent_routing.yaml` - Agent-to-provider routing

**Fallback Chains Configurados:**
- **Boss tier** (analyst, architect, pm): Groq → Gemini → Cerebras → OpenRouter
- **Worker tier** (dev, tea, sm): Cerebras → Groq → Gemini → OpenRouter
- **Creative tier** (tech-writer, ux-designer): Gemini → Groq → Cerebras → OpenRouter

**Testes:** 32 tests (fallback, quality, auto-throttle, integration)
**Coverage:** 93% (Epic 4 modules)

**SLA Esperado:** 99.5%+ (4 providers com fallback chains)

---

### Agent-to-Provider Distribution (Implemented)

**Decisão:** Load balancing tier-based

**Distribuição Atual:**
```
BOSS TIER → Groq (Llama-3.3-70B):
  - Mary (analyst): 1196ms avg
  - Winston (architect): 1793ms avg
  - John (pm): 1731ms avg
  Use case: Complex reasoning, strategic planning

WORKER TIER → Cerebras (Llama-3.1-8B):
  - Amelia (dev): 583ms avg (65% FASTER!)
  - Bob (sm): 501ms avg
  - Murat (tea): 586ms avg
  Use case: Code generation, test generation, fast tasks

CREATIVE TIER → Gemini (2.0 Flash):
  - Paige (tech-writer): 4951ms avg
  - Sally (ux-designer): 3504ms avg
  Use case: Documentation, UX design, creative tasks

FALLBACK TIER → OpenRouter (Auto-routing):
  - Available for all agents as fallback
  Use case: Diversity, redundancy
```

**Performance Gains:**
- Worker tier **65% faster** than Boss tier
- No provider bottlenecks (load distributed)
- Optimal model selection per task type

**Load Utilization:**
- Groq: 3 agents → 10 RPM avg each → 33% capacity
- Cerebras: 3 agents → 10 RPM avg each → 33% capacity
- Gemini: 2 agents → 7.5 RPM avg each → 50% capacity
- OpenRouter: 0 agents primary → 0% capacity (fallback only)

**Result:** Efficient resource utilization, no waste!

---

## Testing Strategy

### Unit Testing with Stub Providers

**Challenge:** Unit tests should NOT depend on:
- Real API keys
- Network availability
- External service uptime
- Non-deterministic LLM responses

**Solution:** Stub Provider Pattern (Story 3.8)

**Implementation:**

```python
# tests/stubs/stub_provider.py
from src.providers.base import LLMProvider, LLMResponse
from typing import Optional, List, Dict
import asyncio

class StubLLMProvider(LLMProvider):
    """Fake provider for unit tests - no real API calls"""

    def __init__(self, fixed_response: Optional[str] = None):
        self.fixed_response = fixed_response or '{"status": "success"}'
        self.call_count = 0
        self.call_history: List[Dict] = []

    async def call(self, messages: List[Dict], tools: Optional[List] = None) -> LLMResponse:
        self.call_count += 1
        self.call_history.append({"messages": messages, "tools": tools})

        await asyncio.sleep(0.05)  # Simulate realistic latency

        return LLMResponse(
            content=self.fixed_response,
            provider="stub",
            model="test-model",
            tokens_input=100,
            tokens_output=50,
            latency_ms=50
        )

    def reset(self):
        self.call_count = 0
        self.call_history = []
```

**Usage in Tests:**

```python
# tests/unit/test_agent_orchestrator.py
import pytest
from tests.stubs.stub_provider import StubLLMProvider
from src.agents.orchestrator import AgentOrchestrator

@pytest.mark.asyncio
async def test_agent_execution_success():
    # Arrange
    stub = StubLLMProvider(
        fixed_response='{"findings": ["Rate limiting is critical"], "confidence": 0.95}'
    )
    orchestrator = AgentOrchestrator(provider=stub)

    # Act
    result = await orchestrator.execute(agent="analyst", task="Analyze rate limiting")

    # Assert
    assert stub.call_count == 1
    assert "analyst" in str(stub.call_history[0]["messages"])
    assert result.content is not None

    # Verify prompt construction
    system_prompt = stub.call_history[0]["messages"][0]["content"]
    assert "Mary" in system_prompt  # Agent persona injected

    stub.reset()

@pytest.mark.asyncio
async def test_tool_calling():
    # Arrange
    stub = StubLLMProvider(
        fixed_response='{"tool_calls": [{"name": "load_file", "args": {"path": ".bmad/agents/analyst.md"}}]}'
    )
    orchestrator = AgentOrchestrator(provider=stub)

    # Act
    result = await orchestrator.execute(agent="analyst", task="Load workflow")

    # Assert
    assert stub.call_count >= 1
    assert "tools" in stub.call_history[0]  # Tools passed to LLM
```

**Benefits:**
- ✅ **Fast:** No network I/O (tests run in <100ms)
- ✅ **Deterministic:** Same input → same output
- ✅ **Offline:** Work without internet
- ✅ **CI/CD Friendly:** No secrets needed
- ✅ **Cost-Free:** No API quota consumed
- ✅ **Inspectable:** Verify prompt construction, tool definitions

**Test Pyramid:**

```
         E2E Tests (5%)
        /            \
       /  Real APIs   \
      /________________\

     Integration (15%)
    /   Stub + Redis  \
   /____________________\

  Unit Tests (80%)
 /   Stub Providers    \
/_______________________\
```

**Coverage Targets:**
- Unit tests: 80%+ coverage
- Integration tests: Key flows (agent execution, fallback, tool calling)
- E2E tests: Full system with real providers (run nightly)

### Provider Swapping Pattern

**One-Line Provider Change:**

```python
# Development/Testing (stub)
from tests.stubs.stub_provider import StubLLMProvider
provider = StubLLMProvider(fixed_response='{"result": "test"}')

# Production (real)
from src.providers.groq_provider import GroqProvider
provider = GroqProvider(api_key=os.getenv("GROQ_API_KEY"))
```

**Everything else stays the same** - interface contract (`LLMProvider.call()`) unchanged.

**Benefits:**
- Swap provider without touching orchestration code
- Easy A/B testing (compare Groq vs Cerebras)
- Graceful degradation (fallback to stub if all providers down)

---

## Future Enhancements (Post-MVP)

### Phase 2: MCP Server with RAG

**When to Implement:**
- 10+ custom agents
- 100+ workflows BMad
- Multiple projects sharing Squad API

**Architecture:**
```
Squad API ← MCP Server (localhost:8080)
            ↓
            - Chroma Vector DB
            - .bmad/ indexed (embeddings)
            - Semantic search agents/workflows
            - Chunk management (300-500 words)
            - Hybrid search (embeddings + BM25)
```

**Benefits:**
- Semantic search: "Find workflow for market research" → Returns relevant workflows
- Context compression: Only load relevant chunks, not full files
- Scalability: 1000+ workflows, 100+ agents

**Tool Integration:**
```python
# New tool: mcp_search
{
  "name": "mcp_search",
  "description": "Semantic search across BMad workflows and agent definitions",
  "parameters": {
    "query": "Natural language query (e.g., 'workflow for technical research')",
    "k": "Number of results (default: 4)"
  }
}

# Mary via Groq calls:
tool_call: mcp_search(query="workflow for market analysis", k=3)

# MCP Server returns:
[
  ".bmad/bmm/workflows/research/instructions-market.md",
  ".bmad/bmm/workflows/product-brief/instructions.md",
  ...
]
```

**Implementation Epic (Future):**
- Epic 11: MCP Server Integration
- 8-10 stories
- +2 weeks timeline

---

### Phase 2: Auto-Pilot Multi-Agent Orchestration

**Vision:** Squad API autonomously decomposes complex tasks and coordinates multiple agents in sequence or parallel.

**Current (MVP):** Single agent execution
```bash
POST /api/v1/agent/execute
{
  "agent": "analyst",
  "task": "Execute research workflow"
}
# User explicitly chooses which agent
```

**Future (Auto-Pilot):** Multi-agent autonomous execution
```bash
POST /api/v1/task/execute
{
  "task": "Build donation tracking system with PostgreSQL and React frontend"
}

# Squad API automatically:
# 1. Analyzes task complexity
# 2. Decomposes into subtasks
# 3. Creates execution plan
# 4. Executes agents: Architect → Dev (backend) → Dev (frontend) → QA
# 5. Synthesizes deliverable
```

**Real-World Example:**

```json
{
  "task": "Build VTT app with dice roller, character sheets, and initiative tracker"
}

// Squad API Response:
{
  "execution_plan": {
    "stages": [
      {
        "name": "Architecture",
        "agents": [{"agent": "architect", "task": "Design system architecture"}],
        "execution": "sequential"
      },
      {
        "name": "Implementation",
        "agents": [
          {"agent": "dev", "task": "Implement dice roller API", "depends_on": ["architect"]},
          {"agent": "dev", "task": "Implement character sheet storage", "depends_on": ["architect"]},
          {"agent": "dev", "task": "Implement initiative tracker", "depends_on": ["architect"]}
        ],
        "execution": "parallel"  // 3 devs work simultaneously!
      },
      {
        "name": "Quality Assurance",
        "agents": [
          {"agent": "qa", "task": "Write integration tests", "depends_on": ["dev"]},
          {"agent": "tech-writer", "task": "Create user docs", "depends_on": ["dev"]}
        ],
        "execution": "parallel"
      }
    ]
  },
  "deliverables": {
    "architecture": "docs/architecture-vtt-app.md",
    "api_code": "src/vtt-api/",
    "tests": "tests/vtt/",
    "documentation": "docs/user-guide.md"
  },
  "total_time": "18 minutes",
  "agents_used": 6,
  "parallel_speedup": "3.2x"
}
```

**Architecture Components:**

```python
# src/orchestrator/task_decomposer.py
class TaskDecomposer:
    """Intelligent task decomposition using powerful LLM"""

    def __init__(self, llm_provider: LLMProvider):
        # Use Gemini Pro (2 RPM) for complex reasoning
        self.llm = llm_provider

    async def decompose(self, task: str) -> ExecutionPlan:
        """Analyze task and create multi-agent execution plan"""

        prompt = f"""You are a project manager coordinating a squad of specialized AI agents.

Available agents:
- Analyst (Mary): Research, market analysis, requirements gathering
- PM (John): Product strategy, roadmaps, PRDs
- Architect (Alex): System design, architecture decisions
- Dev (multiple): Backend, frontend, APIs
- QA: Test planning, test automation
- Tech Writer: Documentation

Task: {task}

Create an execution plan (JSON):
{{
  "stages": [
    {{
      "name": "stage name",
      "agents": [
        {{"agent": "agent_id", "task": "specific subtask", "depends_on": []}}
      ],
      "execution": "sequential|parallel"
    }}
  ],
  "estimated_time_minutes": 30,
  "complexity": "simple|medium|complex"
}}

Guidelines:
- Break complex tasks into stages
- Identify dependencies (Architect before Dev, Dev before QA)
- Maximize parallelism where possible (multiple Devs can work simultaneously)
- Keep subtasks specific and actionable
"""

        response = await self.llm.call(prompt)
        return ExecutionPlan.model_validate_json(response)

# src/orchestrator/multi_agent_dispatcher.py
class MultiAgentDispatcher:
    """Coordinates execution of multiple agents respecting dependencies"""

    async def execute_plan(self, plan: ExecutionPlan) -> ProjectDeliverable:
        """Execute multi-agent plan with dependency resolution"""

        results = {}

        for stage in plan.stages:
            if stage.execution == "parallel":
                # Execute all tasks in stage simultaneously
                stage_results = await asyncio.gather(*[
                    self.execute_agent_task(
                        task,
                        context={dep: results[dep] for dep in task.depends_on}
                    )
                    for task in stage.agents
                ])
            else:
                # Sequential execution
                stage_results = []
                for task in stage.agents:
                    result = await self.execute_agent_task(
                        task,
                        context={dep: results[dep] for dep in task.depends_on}
                    )
                    stage_results.append(result)

            # Store results for next stage
            for task, result in zip(stage.agents, stage_results):
                results[task.task_id] = result

        # Synthesize final deliverable
        return self.synthesize(results, plan)

    async def execute_agent_task(self, task: AgentTask, context: Dict) -> AgentResult:
        """Execute single agent with inherited context"""

        # Build prompt with context from previous agents
        enriched_task = f"""
Previous work:
{self.format_context(context)}

Your task:
{task.task}
"""

        # Execute via standard agent orchestrator
        return await self.orchestrator.execute(
            agent=task.agent,
            task=enriched_task
        )
```

**API Endpoint:**

```python
# src/api/v1/task.py
@router.post("/execute")
async def execute_task(request: TaskExecutionRequest):
    """Auto-Pilot: Decompose and execute complex task"""

    # 1. Decompose task into execution plan
    decomposer = TaskDecomposer(gemini_pro_provider)
    plan = await decomposer.decompose(request.task)

    # 2. Execute plan with multi-agent coordination
    dispatcher = MultiAgentDispatcher(agent_orchestrator)
    deliverable = await dispatcher.execute_plan(plan)

    # 3. Return complete solution
    return TaskExecutionResponse(
        plan=plan,
        deliverable=deliverable,
        total_time_seconds=deliverable.elapsed_time,
        agents_used=deliverable.agents_used,
        parallel_speedup=deliverable.parallel_speedup
    )
```

**When to Implement:**
- After MVP proves single-agent execution works reliably
- When Dani wants "hands-free" project bootstrapping
- Phase 2 (weeks 11-16)

**Epic for Phase 2:**

**Epic 12: Auto-Pilot Multi-Agent Orchestration** (8-10 stories, 2 weeks)
- Story 12.1: Task Decomposer (LLM-based analysis)
- Story 12.2: Execution Plan Model (Pydantic schemas)
- Story 12.3: Dependency Graph Resolver
- Story 12.4: Multi-Agent Dispatcher (parallel + sequential)
- Story 12.5: Context Propagation (results → next agents)
- Story 12.6: Result Synthesizer (combine outputs)
- Story 12.7: `/api/v1/task/execute` endpoint
- Story 12.8: Integration tests for multi-agent flows
- Story 12.9: Auto-Pilot UI (show execution graph in real-time)
- Story 12.10: Performance optimization (caching, dedup)

**Benefits:**
- ✅ True "hands-free" development (describe task → get solution)
- ✅ Parallel execution (3-5x speedup for independent tasks)
- ✅ Smart coordination (agents share context automatically)
- ✅ Reusable patterns (same orchestration for any project)

**Example Use Cases:**
- "Build CRUD API for user management" → Architect + Dev + QA
- "Create landing page with hero section and pricing" → Designer + Dev + QA
- "Add authentication to existing app" → Architect + Dev (backend) + Dev (frontend) + QA + Tech Writer

**Alignment with BMad Method:**
- Task Decomposer = PM agent (creates sprint backlog)
- Multi-Agent Dispatcher = Scrum Master (coordinates team)
- Auto-Pilot = Full BMad workflow executed by external LLMs

---

### Phase 3: Advanced LangChain Integration

**When:** Orchestration complexity exceeds custom implementation

**Features to Adopt:**
- `AgentExecutor` para workflow orchestration
- `ConversationBufferMemory` com pruning inteligente
- `RouterChain` para dynamic agent routing
- `LLMChain` compositions

**Benefits:**
- Leverage LangChain ecosystem
- Less custom code maintenance
- Community patterns

**Trade-off:**
- Dependency weight (+50MB)
- Learning curve
- Abstraction overhead

---

## Implementation Guidance for AI Agents

### For Epic 0 (Foundation):

**Agent Instructions:**
1. Create exact directory structure from Project Structure section
2. Use exact dependency versions from Decision Summary table
3. Docker Compose MUST match yaml in Deployment Architecture
4. All healthchecks MUST be implemented as specified

**Critical Files:**
- requirements.txt: Pin ALL versions
- docker-compose.yaml: Include ALL services
- .gitignore: Exclude .env, data/, __pycache__

---

### For Epic 1 (Agent Transformation):

**Agent Instructions:**
1. BMad agent parser (Story 1.1):
   - Parse YAML frontmatter + XML agent block
   - Extract: persona, menu, workflows
   - Return AgentDefinition Pydantic model

2. System Prompt Builder (Story 1.4):
   - Include complete persona (3-4k tokens)
   - Format: "You are {Name}, a {Title}. PERSONA: ... MENU: ... RULES: ..."
   - Must be comprehensive - LLM relies entirely on this

3. Tool Definition (Story 1.13):
   - Follow OpenAI-compatible format EXACTLY
   - Tools: load_file, save_file, web_search, list_directory, update_workflow_status
   - Security: Validate paths in executor

4. Multi-Turn Loop (Story 1.15):
   - Max 10 turns (prevent infinite loops)
   - Preserve conversation history
   - Each turn: LLM → tool_calls → execute → results → next LLM call

**Critical Success:**
Mary via Groq must be INDISTINGUISHABLE from Mary via Cursor local!

---

### For Epic 2 (Rate Limiting):

**Agent Instructions:**
1. Token Bucket (Story 2.1):
   - Use pyrate-limiter RedisBucket
   - Config: RPM, burst, window_sec from rate_limits.yaml
   - Refill rate: RPM/60 tokens/second

2. Sliding Window (Story 2.2):
   - Redis Sorted Set with unix timestamps
   - Cleanup: Remove timestamps > 60s old
   - Check: count(last 60s) < RPM limit

3. Combined Approach (Story 2.3):
   - Check sliding window FIRST (cheaper)
   - Then acquire token bucket
   - Both must pass

4. Global Semaphore (Story 2.4):
   - asyncio.Semaphore(12) - max concurrent
   - Wrap ALL provider calls
   - FIFO queueing

**Critical Success:**
<1% de 429 errors em carga normal (120-130 RPM sustained)

---

### For Epic 3 (Provider Wrappers):

**Agent Instructions:**
1. Abstract Interface (Story 3.1):
   - Define LLMProvider ABC
   - Methods: call(), health_check(), count_tokens()
   - All providers MUST implement this interface

2. Groq Provider (Story 3.2):
   - Use `groq` SDK (async)
   - Function calling support required
   - Handle tool_calls in response

3. Gemini Provider (Story 3.4):
   - Use `google-genai` SDK (NOT REST)
   - Auto-detect GEMINI_API_KEY from env
   - Combine system + user prompts (Gemini format)

4. Provider Factory (Story 3.7):
   - Load config/providers.yaml
   - Create instances dynamically
   - Register em dict: providers['groq'] → GroqProvider()

**Critical Success:**
All providers return consistent LLMResponse format

---

### For Epic 10 (Status UI):

**Agent Instructions:**
1. WebSocket Server (Story 10.1):
   - Endpoint: ws://localhost:8000/ws/agent-status
   - Send initial state on connect
   - Broadcast updates when status changes
   - Handle disconnects gracefully

2. Status Tracking (Story 10.3):
   - Idle (⚪ gray): Not used in last 5 min
   - Active (🟢 green): Executing now, latency < target
   - Degraded (🟡 yellow): Executing but latency > target
   - Failed (🔴 red): Last execution failed

3. HTML/JS Board (Story 10.4):
   - Use provided HTML template EXACTLY
   - CSS: Dark theme (#1e1e1e background)
   - Auto-reconnect on WebSocket close
   - Format timestamps: "Just now", "5 min ago", "2h 15min ago"

**Critical Success:**
Dani opens `http://localhost:8000/status` e vê squad em tempo real!

---

## Summary

**Architecture Type:** Complete Multi-Agent with Function Calling Tools

**Key Architectural Principles:**
1. **Boring Technology:** Proven patterns (FastAPI, Redis, PostgreSQL), no exotic choices
2. **Config-Driven:** Adjust behavior via YAML, not code changes
3. **Async-First:** Non-blocking I/O throughout (asyncio, aiohttp, async SDKs)
4. **Modular:** Each epic maps to independent module
5. **Observable:** Dual monitoring (Grafana technical + Status Board human)
6. **Resilient:** Auto-throttling + fallback chains guarantee 99.5%+ SLA
7. **Reusable:** Design enables use in multiple future projects

**Total Implementation:**
- 11 Epics
- 82 Stories
- ~10,000 LOC
- 10 weeks timeline (8 weeks + 2 buffer)

**Readiness for Implementation:**
✅ All architectural decisions made
✅ Technology stack verified (versions from 2025)
✅ Project structure defined (complete tree)
✅ Patterns documented (consistency rules)
✅ Novel patterns designed (function calling bridge)
✅ ADRs captured (rationale preserved)

**Next Phase:** Sprint Planning → Story-by-story implementation

---

_This architecture document serves as the consistency contract for all AI development agents. Follow these decisions precisely to ensure cohesive implementation._

_Created through collaborative discovery between Dani and Winston (Architect Agent)._

