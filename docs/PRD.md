# Squad API - Product Requirements Document

**Author:** Dani  
**Date:** 2025-11-12  
**Version:** 1.0

---

## Executive Summary

Squad API é uma infraestrutura que **distribui o BMad Method** - transforma LLMs de APIs externas em agentes BMad especializados, exatamente como funciona hoje no Cursor local, mas escalável e production-ready.

**A Visão:**

Hoje você tem acesso a 8+ agentes especialistas (@analyst, @pm, @architect, etc.) - mas todos são incorporados por UMA única LLM local (Cursor). Squad API distribui isso: cada LLM externa (Groq, Cerebras, Gemini) **vira** um agente BMad específico - Mary, John, Alex - com persona completa, workflows estruturados, e metodologia embarcada.

**O Problema que Resolve:**

- **Hoje:** Você (não-programador) recuperou a capacidade de criar soluções via LLMs + BMad
- **Limitação:** Depende de uma única LLM local, não escalável, não reutilizável
- **Solução:** Squad API = BMad Method distribuído em múltiplas LLMs externas com rate limiting robusto

**O Resultado:**

Uma base **reutilizável** que permite criar múltiplos projetos (RL's atômicos, Test Dashboard, VTT App) com uma squad de especialistas sempre disponível.

### What Makes This Special

**O Momento Mágico:**

Não é quando dashboards funcionam ou rate limits não quebram. É quando você pede:

> "Analise este sistema"

E quem responde não é "Groq API", mas **Mary (Analyst) via Groq** - com:
- ✅ Persona de analista estratégica
- ✅ Workflows BMad estruturados
- ✅ Menu de opções especializadas
- ✅ Metodologia de elicitação completa

**Você sente que está conversando com a squad BMad de verdade**, não fazendo "API calls".

---

## Project Classification

**Technical Type:** API/Backend (Orchestration Infrastructure)  
**Domain:** Developer Tools (Agent Orchestration)  
**Complexity:** High (Production-ready, enterprise patterns)

**Características:**

- **Natureza:** Sistema de orquestração que transforma LLMs em agentes especializados
- **Stack:** Python 3.11+, FastAPI, Redis, PostgreSQL, Prometheus/Grafana
- **Padrões:** Token Bucket, Sliding Window, Worker/Boss, Fallback Chains
- **Arquitetura:** Complete Multi-Agent (decidido no Technical Research)

**Relação com BMad Method:**

Squad API **não substitui** BMad Method. Ele **distribui** BMad Method:
- `.bmad/bmm/agents/*.md` → Definições de agentes (Mary, John, Alex, etc.)
- Squad API → Carrega essas definições e **instrui LLMs externas a incorporá-las**
- Resultado → Cada LLM externa vira um agente BMad funcional

---

## Success Criteria

**MVP está pronto quando:**

### 1. Transformação Funciona (Core Magic)

```yaml
cenário: "Pedir análise ao orquestrador"

hoje_cursor:
  - Dani → @analyst.mdc → LLM local incorpora Mary
  - resposta: Mary (via LLM local) com persona completa

com_squad_api:
  - Dani → Orquestrador → LLM 1 (Groq) incorpora Mary
  - resposta: Mary (via Groq) com persona completa
  - sensação: "Estou conversando com Mary, não com 'Groq API'"

success: ✅ LLM externa age EXATAMENTE como agente BMad local
```

### 2. Resiliência & Disponibilidade

```yaml
rate_limiting:
  - 429_errors: <1% das requisições
  - auto_throttling: Funciona em spikes
  - fallback: Mary via Groq → Mary via Cerebras (<5s)
  
availability:
  - target: 99.5%+ (medido em 1 semana)
  - downtime_max: <1 hora por semana
```

### 3. Reutilização Comprovada

```yaml
projeto_1: Squad API (8-10 semanas build)
projeto_2: RL's atômicos (usando Squad API, <2 semanas)
projeto_3: Test Dashboard (usando Squad API, <1 semana)

success: ✅ "Build once, use everywhere" é realidade
```

### 4. Observabilidade Funcional

```yaml
dashboards:
  - Grafana mostra: requests, 429s, latency, tokens
  - Slack alerts: spikes, failures
  
debugging:
  - Posso ver: qual agente, qual LLM, qual status
  - Logs estruturados com context full
```

### Business Metrics

**Para Dani (Criador):**

**Curto prazo (3 meses):**
- Squad API funcional e testado em produção
- 1 projeto adicional (RL's atômicos) usando Squad API
- Portfolio técnico: "Eu construí isso!"

**Médio prazo (6-12 meses):**
- 3-5 projetos usando Squad API
- ROI comprovado: tempo economizado > tempo investido
- Autonomia: não depende de devs para criar soluções

**Longo prazo (1-2 anos):**
- Squad API como "superpoder" pessoal
- Transição de carreira: QA + Builder híbrido
- Potencial open-source/community

---

## Product Scope

### MVP - Minimum Viable Product (10 semanas)

**Core 1: Agent Transformation Engine**

O coração do Squad API - transforma LLMs em agentes BMad:

1. **Agent Loader**
   - Carrega `.bmad/bmm/agents/*.md` (Mary, John, Alex, etc.)
   - Parse de: persona, communication_style, principles, menu
   - Extrai workflows associados

2. **LLM Instructor**
   - Monta "system prompt" que instrui LLM a incorporar agente
   - Inclui: persona completa, menu de opções, rules, workflows
   - Formato: "You are Mary, a Business Analyst with 8+ years experience..."

3. **Conversation Manager**
   - Mantém "character" do agente durante múltiplas interações
   - Context window management (1M tokens)
   - State persistence (Redis)

4. **Agent Router**
   - Mapeia agente BMad → LLM provider específico
   - Config-driven: `analyst: groq/llama-3-70b`
   - Worker/Boss hierarchy: tenta worker primeiro, escalate se necessário

**Core 2: Rate Limiting Robusto**

Garante que squad nunca para por 429 errors:

1. **Token Bucket + Sliding Window**
   - Per-provider limits (Groq 12 RPM, Cerebras 60 RPM, etc.)
   - Redis-backed (shared state entre workers)
   - 60s sliding window (previne burst clustering)

2. **Auto-Throttling Adaptativo**
   - Detecta spikes de 429s (>3 em 1 min)
   - Reduz RPM em 20% automaticamente
   - Restaura após 10 min se estável

3. **Burst Interleaving**
   - Distribui carga uniformemente entre providers
   - Pattern: Groq burst → wait 10s → Cerebras burst → wait 10s

4. **Global Semaphore**
   - Max 10-12 requests concurrent (total)
   - Previne network overload

**Core 3: Fallback & Resilience**

Garante 99.5%+ SLA:

1. **Fallback Chains (Config-Driven)**
   ```yaml
   analyst:
     - cerebras/llama-3-8b (worker)
     - groq/llama-3-70b (boss)
   
   architect:
     - groq/llama-3-70b (boss)
     - gemini/gemini-2.5-pro (boss-ultimate)
   ```

2. **Automatic Escalation**
   - Worker fails → Boss tenta em <5s
   - Boss fails → Boss-ultimate (se configurado)
   - All fail → Clear error message

3. **Quality Validation**
   - Check response quality (confidence scoring)
   - Auto-escalate se quality baixa

**Core 4: Observability Completa**

Visibilidade total do sistema:

1. **Prometheus Metrics**
   - `llm_requests_total{provider, agent, status}`
   - `llm_requests_429_total{provider}`
   - `llm_request_duration_seconds{provider, agent}`
   - `llm_tokens_consumed{provider, type}`
   - `llm_bucket_tokens_available{provider}`
   - `llm_window_occupancy{provider}`

2. **Grafana Dashboards**
   - Request success rate (por provider, por agente)
   - 429 errors timeline
   - Latency P50/P95/P99
   - Token bucket status (real-time)

3. **Slack Alerts**
   - 429s > 5/min → Auto-throttle alert
   - Latency avg > 2s (potentes) → Investigate
   - Cost daily > 90% quota → Notify

4. **Structured Logging**
   - JSON logs com context full
   - Fields: request_id, agent, provider, status, retry_after, tokens

**Core 5: Base Reutilizável**

Design modular e config-driven:

1. **Config System (YAML)**
   - `config/rate_limits.yaml` - RPM, burst, window por provider
   - `config/agent_chains.yaml` - Fallback chains por agente
   - `config/providers.yaml` - API keys, models, endpoints

2. **Modular Architecture**
   - `src/rate_limit/` - Rate limiting layer (independente)
   - `src/agents/` - Agent transformation (independente)
   - `src/providers/` - Provider wrappers (independente)
   - `src/scheduler/` - Burst scheduling (independente)
   - `src/metrics/` - Observability (independente)

3. **Documentation**
   - README: Quick start, architecture overview
   - Runbooks: Deploy, troubleshoot, scale
   - ADRs: Decision records (Gemini SDK, Worker/Boss, etc.)

4. **Docker Compose**
   - Redis, PostgreSQL, Prometheus, Grafana
   - One-command setup: `docker-compose up`
   - Reproduzível em qualquer máquina

### Growth Features (Post-MVP)

**Phase 2: Expand Capabilities**

1. **Mais Providers**
   - HuggingFace PRO (teste PRO limits)
   - Claude API (quando disponível)
   - Together AI ($5 tier)
   - OpenAI (se budget permitir)

2. **Multimodal Support**
   - Imagens (útil para VTT App - mapas, tokens)
   - Áudio (voice commands?)
   - Vídeo (se algum projeto futuro precisar)

3. **Advanced Context Management**
   - RAG (Retrieval-Augmented Generation)
   - Vector DB (long-term memory para agentes)
   - Context compression (fit more em 1M tokens)

4. **Agent Memory**
   - Agentes "lembram" de conversas anteriores
   - Project-specific context (ex: RL's atômicos context)

**Phase 2.5: Simple Monitoring UI** (MOVIDO PARA MVP!)

1. **Agent Status Board**
   - UI simples (HTML/JS) mostrando squad status
   - Color-coded: ⚪ Idle, 🟢 Active, 🟡 Degraded, 🔴 Failed
   - Real-time updates (WebSocket)
   - Mostra: Agent name, Provider, Current task, Latency

**Why moved to MVP:**
- Essencial para "sentir a squad trabalhando"
- Muito mais simples que Grafana (humano-friendly)
- Quick win: ver agentes em ação

**Phase 3: Multi-User & Collaboration**

1. **Multi-User Support**
   - Auth system (OAuth2)
   - Per-user quotas
   - Shared squads (collaborate com outros)

2. **Advanced Web UI**
   - Dashboard completo para non-CLI users
   - Agent chat interface
   - Project management UI

3. **Team Features**
   - Shared projects
   - Agent collaboration (Mary + John trabalhando juntos)

**Phase 4: Community & Ecosystem**

1. **Open-Source (Maybe)**
   - Ajudar outras pessoas na mesma situação que Dani
   - Community contributions
   - Plugin system

2. **Custom Agents**
   - Users podem criar seus próprios agentes
   - Agent marketplace
   - Community workflows BMad

3. **Enterprise Features**
   - On-premise deployment
   - SSO integration
   - Advanced compliance (audit logs, PII sanitization avançada)

### Vision (Future)

**Long-term Dream:**

Squad API se torna a **infraestrutura padrão** para pessoas que querem criar soluções via LLMs + metodologias estruturadas (não apenas BMad).

- Suporta múltiplas metodologias (BMad, Agile, Lean, etc.)
- Marketplace de agentes especializados
- Hosted service (SaaS)
- Developer ecosystem vibrante

**Mas o core sempre permanece:**
> "Transformar LLMs genéricas em agentes especializados que trabalham pra você"

---

## API/Backend Specific Requirements

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Client (Dani)                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Orchestrator                        │
│  - Recebe: "Analise este sistema" (agent: analyst)      │
│  - Carrega: .bmad/bmm/agents/analyst.md                 │
│  - Instrui: LLM a incorporar Mary (Analyst)             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Rate Limiting Layer                         │
│  - Token Bucket (per-provider)                          │
│  - Sliding Window (60s)                                 │
│  - Global Semaphore (10-12 concurrent)                  │
│  - Auto-Throttling                                      │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬────────────┐
        ▼            ▼            ▼            ▼
  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
  │  Groq   │  │Cerebras │  │ Gemini  │  │OpenRoute│
  │  (Mary) │  │ (John)  │  │ (Alex)  │  │ (Sarah) │
  └─────────┘  └─────────┘  └─────────┘  └─────────┘
        │            │            │            │
        └────────────┴────────────┴────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         Response (Mary's analysis via Groq)              │
└─────────────────────────────────────────────────────────┘
```

### API Endpoints

**Core Endpoints:**

```python
POST /api/v1/agent/execute
{
  "agent": "analyst",  # Mary
  "task": "Analise este sistema: ...",
  "context": {...},    # Optional: project context
  "mode": "normal"     # or "yolo"
}

Response:
{
  "agent": "analyst",
  "agent_name": "Mary",
  "provider": "groq",
  "model": "llama-3-70b",
  "response": "...",   # Mary's analysis
  "metadata": {
    "latency_ms": 1850,
    "tokens_input": 2500,
    "tokens_output": 1200,
    "fallback_used": false
  }
}
```

```python
GET /api/v1/agents/available
# Lista todos agentes BMad disponíveis

Response:
{
  "agents": [
    {
      "id": "analyst",
      "name": "Mary",
      "title": "Business Analyst",
      "icon": "📊",
      "status": "available",
      "provider": "groq",
      "workflows": ["research", "product-brief", ...]
    },
    ...
  ]
}
```

```python
GET /api/v1/providers/status
# Status real-time de providers

Response:
{
  "providers": {
    "groq": {
      "status": "healthy",
      "rpm_limit": 12,
      "rpm_current": 3,
      "bucket_tokens": 9,
      "window_occupancy": "3/12 (last 60s)",
      "last_429": null
    },
    "cerebras": {
      "status": "healthy",
      "rpm_limit": 60,
      "rpm_current": 15,
      ...
    }
  }
}
```

```python
GET /health
# Health check endpoint

Response:
{
  "status": "healthy",
  "redis": "connected",
  "postgres": "connected",
  "providers": {
    "healthy": 4,
    "degraded": 0,
    "unavailable": 0
  }
}
```

### Authentication & Authorization

**MVP: Simple API Key**

```python
Headers:
  Authorization: Bearer <api_key>
```

- API key stored in environment variable
- Single-user mode (Dani)
- Rate limiting per API key (não critical no MVP)

**Post-MVP: OAuth2 + Multi-User**

- OAuth2 flows
- Per-user quotas
- Role-based access (admin, user, guest)

### Data Schemas

**Agent Definition (Loaded from .bmad/bmm/agents/*.md):**

```python
class AgentDefinition(BaseModel):
    id: str               # "analyst"
    name: str             # "Mary"
    title: str            # "Business Analyst"
    icon: str             # "📊"
    persona: Persona
    menu: List[MenuItem]
    workflows: List[str]
```

**Persona:**

```python
class Persona(BaseModel):
    role: str
    identity: str
    communication_style: str
    principles: str
```

**Agent Execution Request:**

```python
class AgentExecutionRequest(BaseModel):
    agent: str              # "analyst"
    task: str               # User's request
    context: Optional[dict] # Project context
    mode: str = "normal"    # "normal" or "yolo"
```

**Provider Configuration:**

```python
class ProviderConfig(BaseModel):
    name: str              # "groq"
    api_base: str          # "https://api.groq.com/v1"
    api_key: str           # From env
    models: List[str]      # ["llama-3-70b", "llama-3-8b"]
    rpm_limit: int         # 12
    burst: int             # 2
    window_sec: int        # 60
```

---

## Functional Requirements

### FR-1: Agent Transformation System

**Core Capability:** Carregar agentes BMad e instruir LLMs a incorporá-los

#### FR-1.1: Agent Loader

**Requirement:**
Sistema deve carregar definições de agentes BMad de `.bmad/bmm/agents/*.md`

**Acceptance Criteria:**
- ✅ Parse de arquivos .md BMad format
- ✅ Extrai: persona, communication_style, principles, menu
- ✅ Identifica workflows associados ao agente
- ✅ Cache de agentes carregados (Redis)
- ✅ Hot-reload se arquivos mudarem

**Connects to Magic:**
> "Ler as 'instruções' que definem quem é Mary, John, Alex"

#### FR-1.2: System Prompt Builder

**Requirement:**
Sistema deve construir "system prompt" completo que instrui LLM a incorporar agente

**Acceptance Criteria:**
- ✅ Inclui persona completa do agente
- ✅ Inclui communication_style e principles
- ✅ Inclui menu de opções (numerado)
- ✅ Inclui regras de ativação
- ✅ Formato: "You are [Name], a [Title]. Your role is..."

**Example Output:**
```
You are Mary, a Business Analyst with 8+ years experience.

PERSONA:
- Role: Strategic Business Analyst + Requirements Expert
- Identity: Senior analyst with deep expertise in market research...
- Communication Style: Systematic and probing. Connects dots others miss...
- Principles: Every business challenge has root causes waiting to be discovered...

MENU:
1. Show this menu (*help)
2. Start workflow-init (*workflow-init)
3. Check workflow status (*workflow-status)
...

RULES:
- ALWAYS communicate in PT-BR
- Stay in character until exit
- Load files ONLY when workflows require
...
```

**Connects to Magic:**
> "Transformar definição BMad em instruções que LLM entende"

#### FR-1.3: Conversation Manager

**Requirement:**
Sistema deve manter "character" do agente durante múltiplas interações

**Acceptance Criteria:**
- ✅ State persistence entre requests (Redis)
- ✅ Context window management (1M tokens)
- ✅ Conversation history preservada
- ✅ Agent "remembers" previous interactions
- ✅ Timeout: 1 hora de inatividade → clear state

**Connects to Magic:**
> "Mary 'lembra' do que você conversou, não é request isolado"

#### FR-1.4: Agent Router

**Requirement:**
Sistema deve mapear agente BMad → LLM provider correto

**Acceptance Criteria:**
- ✅ Config-driven mapping (`analyst: groq/llama-3-70b`)
- ✅ Worker/Boss hierarchy support
- ✅ Dynamic routing based on task complexity
- ✅ Fallback chains automatic

**Example Config:**
```yaml
agents:
  analyst:
    primary: groq/llama-3-70b
    fallback: cerebras/llama-3-8b
  
  architect:
    primary: groq/llama-3-70b
    fallback: gemini/gemini-2.5-pro
```

**Connects to Magic:**
> "Decidir qual LLM vai incorporar qual agente BMad"

---

### FR-2: Rate Limiting & Resilience

**Core Capability:** Garantir que squad nunca para por 429 errors

#### FR-2.1: Token Bucket Per-Provider

**Requirement:**
Implementar Token Bucket algorithm com Redis backend por provider

**Acceptance Criteria:**
- ✅ Per-provider buckets (Groq, Cerebras, Gemini, etc.)
- ✅ Configurable: RPM, burst, window_sec
- ✅ Redis-backed (shared state entre workers)
- ✅ Refill rate: RPM/60 tokens per second
- ✅ Block request se bucket vazio

**Config Example:**
```yaml
groq:
  rpm: 12
  burst: 2
  window_sec: 60
```

**Connects to Magic:**
> "Mary sempre disponível porque sistema gerencia rate limits inteligentemente"

#### FR-2.2: Sliding Window (60s)

**Requirement:**
Track requests em janela deslizante de 60 segundos

**Acceptance Criteria:**
- ✅ Timestamp de cada request (Redis sorted set)
- ✅ Check: count(requests in last 60s) < RPM limit
- ✅ Previne burst clustering em minute boundaries
- ✅ Auto-cleanup timestamps antigos

**Connects to Magic:**
> "Evita 'burst at minute 0' que causa 429s"

#### FR-2.3: Auto-Throttling Adaptativo

**Requirement:**
Detectar spikes de 429s e reduzir RPM automaticamente

**Acceptance Criteria:**
- ✅ Spike detection: >3 429s em 1 minuto → throttle
- ✅ Action: Reduz RPM em 20%
- ✅ Min floor: Nunca abaixo de 50% do original
- ✅ Restore: Após 10 min se estável
- ✅ Metrics: Log throttle events

**Connects to Magic:**
> "Sistema 'aprende' quando está sobrecarregando e se auto-ajusta"

#### FR-2.4: Fallback Chains

**Requirement:**
Automatic fallback se provider atinge rate limit ou falha

**Acceptance Criteria:**
- ✅ Config-driven chains (YAML)
- ✅ Try worker → boss → boss-ultimate (sequence)
- ✅ Fallback em <5s
- ✅ Quality validation: escalate se response baixa qualidade
- ✅ All providers fail → Clear error com suggestion

**Example:**
```yaml
analyst:
  - cerebras/llama-3-8b (worker, 60 RPM)
  - groq/llama-3-70b (boss, 12 RPM)
```

**Connects to Magic:**
> "Se Groq rate limit, Mary 'migra' pra Cerebras automaticamente - você nem percebe"

#### FR-2.5: Global Semaphore

**Requirement:**
Limitar concorrência total do sistema

**Acceptance Criteria:**
- ✅ Max 10-12 requests concurrent (configurável)
- ✅ asyncio.Semaphore implementation
- ✅ Previne network overload
- ✅ Fair queueing (FIFO)

**Connects to Magic:**
> "Mesmo com 13 agentes, nunca overwhelm network ou Redis"

---

### FR-3: Provider Integration

**Core Capability:** Wrappers para LLMs externas com interface unificada

#### FR-3.1: Provider Abstraction Layer

**Requirement:**
Interface comum para todos providers

**Acceptance Criteria:**
- ✅ Abstract class: `LLMProvider`
- ✅ Methods: `call(prompt, max_tokens, temp)`, `health_check()`
- ✅ Unified error handling
- ✅ Retry logic (exponential backoff)
- ✅ Retry-After header respect (429 responses)

**Interface:**
```python
class LLMProvider(ABC):
    @abstractmethod
    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> LLMResponse
    
    @abstractmethod
    async def health_check(self) -> bool
```

#### FR-3.2: Groq Provider

**Requirement:**
Wrapper para Groq API

**Acceptance Criteria:**
- ✅ Usa `groq` Python SDK
- ✅ Suporta models: llama-3-70b, llama-3-8b
- ✅ Rate limit: 12 RPM (conservative, testado)
- ✅ Burst: 2 requests
- ✅ Retry com backoff

#### FR-3.3: Cerebras Provider

**Requirement:**
Wrapper para Cerebras API (Beta)

**Acceptance Criteria:**
- ✅ REST API client (httpx/aiohttp)
- ✅ Rate limit: 60 RPM (generous Beta limits)
- ✅ Burst: 10 requests
- ✅ Handle Beta instability (fallback ready)

#### FR-3.4: Gemini Provider

**Requirement:**
Wrapper para Google Gemini usando SDK oficial

**Acceptance Criteria:**
- ✅ Usa `google-genai` SDK (NOT REST manual)
- ✅ Auto-detecta GEMINI_API_KEY
- ✅ Suporta: gemini-2.5-flash (15 RPM), gemini-2.5-pro (2 RPM)
- ✅ Multimodal ready (futuro)

**Rationale:**
ADR-002 (Technical Research) decidiu por SDK oficial vs REST manual

#### FR-3.5: OpenRouter Provider

**Requirement:**
Wrapper para OpenRouter free tier

**Acceptance Criteria:**
- ✅ REST API client
- ✅ Rate limit: 12 RPM (conservative, free tier)
- ✅ Burst: 2 requests
- ✅ Model: gemma-2b:free ou similar

#### FR-3.6: Together AI Provider (Optional)

**Requirement:**
Wrapper para Together AI (tier 1, $5 one-time)

**Acceptance Criteria:**
- ✅ REST API client
- ✅ Rate limit: 60 RPM
- ✅ Only if $5 investment approved

---

### FR-4: Observability & Monitoring

**Core Capability:** Visibilidade total do sistema

#### FR-4.1: Prometheus Metrics

**Requirement:**
Exposição de métricas detalhadas

**Acceptance Criteria:**
- ✅ Counters:
  - `llm_requests_total{provider, agent, status}`
  - `llm_requests_429_total{provider}`
  
- ✅ Histograms:
  - `llm_request_duration_seconds{provider, agent}`
  - `llm_tokens_consumed{provider, type}` (input/output)
  
- ✅ Gauges:
  - `llm_bucket_tokens_available{provider}`
  - `llm_window_occupancy{provider}`
  
- ✅ Endpoint: `/metrics` (Prometheus scrape)

**Connects to Magic:**
> "Ver em tempo real: Mary está respondendo rápido? Groq está saudável?"

#### FR-4.2: Grafana Dashboards

**Requirement:**
Dashboards pré-configurados para visualização

**Acceptance Criteria:**
- ✅ Dashboard 1: Request Success Rate
  - Taxa de sucesso por provider
  - Taxa de sucesso por agente
  - Breakdown: success/failure/429
  
- ✅ Dashboard 2: Rate Limiting Health
  - 429 errors timeline
  - Token bucket status (real-time)
  - Window occupancy por provider
  
- ✅ Dashboard 3: Performance
  - Latency P50/P95/P99
  - Por provider, por agente
  
- ✅ Dashboard 4: Cost Tracking
  - Tokens consumed (input/output)
  - Estimated cost (se aplicável)
  - Free-tier quota usage

**Connects to Magic:**
> "Dashboard mostra: Squad está saudável, Mary respondeu em 1.8s, Groq 3/12 RPM"

#### FR-4.3: Slack Alerts

**Requirement:**
Alertas automáticos para anomalias

**Acceptance Criteria:**
- ✅ Alert: 429s > 5/min
  - Message: "Auto-throttling ativado: Groq RPM reduzido de 12 → 9"
  
- ✅ Alert: Latency avg > 2s (potentes)
  - Message: "Investigate: Groq latency 3.5s (target: <2s)"
  
- ✅ Alert: Provider unhealthy
  - Message: "Groq unreachable, fallback ativo"
  
- ✅ Alert: Cost > 90% quota
  - Message: "Free-tier 90% utilizado hoje"

**Config:**
```yaml
slack:
  webhook_url: https://hooks.slack.com/...
  channel: "#squad-api-alerts"
```

#### FR-4.4: Structured Logging

**Requirement:**
Logs estruturados com contexto completo

**Acceptance Criteria:**
- ✅ Format: JSON
- ✅ Fields:
  - `timestamp`, `level`, `message`
  - `request_id`, `agent`, `provider`, `model`
  - `status`, `latency_ms`, `tokens_in`, `tokens_out`
  - `retry_count`, `fallback_used`, `error` (if any)
  
- ✅ Log levels: DEBUG, INFO, WARN, ERROR
- ✅ Rotation: Daily, keep 30 days

**Example Log:**
```json
{
  "timestamp": "2025-11-12T10:30:45Z",
  "level": "INFO",
  "message": "Agent execution success",
  "request_id": "req_abc123",
  "agent": "analyst",
  "agent_name": "Mary",
  "provider": "groq",
  "model": "llama-3-70b",
  "status": "success",
  "latency_ms": 1850,
  "tokens_in": 2500,
  "tokens_out": 1200,
  "fallback_used": false
}
```

---

### FR-6: Function Calling & Tool Execution

**Core Capability:** LLMs externas executam ações via tools fornecidas por Squad API

**Context:** LLM externa (Groq) NÃO tem acesso ao filesystem local. Mary via Groq precisa de **tools** para ler workflows, salvar outputs, fazer web search, etc.

#### FR-6.1: Tool Definition System

**Requirement:**
Sistema deve definir tools que LLMs podem usar

**Acceptance Criteria:**
- ✅ Tool: `load_file(path)` - Carrega workflow, agent, ou config file
- ✅ Tool: `save_file(path, content)` - Salva output (ex: research report)
- ✅ Tool: `web_search(query)` - Busca web para research workflows
- ✅ Tool: `list_directory(path)` - Lista arquivos disponíveis
- ✅ Tool: `update_workflow_status(workflow, file_path)` - Atualiza bmm-workflow-status.yaml
- ✅ Tool: `execute_workflow_step(step_data)` - Executa step de workflow BMad

**Tool Format (OpenAI-compatible):**
```json
{
  "type": "function",
  "function": {
    "name": "load_file",
    "description": "Load workflow, agent, or config file from project filesystem",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "type": "string",
          "description": "File path relative to project root"
        }
      },
      "required": ["path"]
    }
  }
}
```

**Connects to Magic:**
> "Mary via Groq pode 'ler' workflows BMad usando load_file tool"

#### FR-6.2: Tool Executor Engine

**Requirement:**
Squad API deve executar tools chamadas por LLMs externas

**Acceptance Criteria:**
- ✅ Receive tool_calls de LLM response
- ✅ Parse tool name e arguments
- ✅ Execute tool localmente (filesystem access)
- ✅ Return result para LLM em next message
- ✅ Security: Validate paths (prevent directory traversal)
- ✅ Logging: Log all tool executions

**Example Flow:**
```python
# 1. Mary via Groq responde com tool_call
response = {
  "choices": [{
    "message": {
      "tool_calls": [{
        "id": "call_123",
        "function": {
          "name": "load_file",
          "arguments": '{"path": ".bmad/bmm/workflows/research/workflow.yaml"}'
        }
      }]
    }
  }]
}

# 2. Squad API executa tool
file_content = load_file_from_filesystem(path)

# 3. Return to Mary
next_call = {
  "messages": [
    ...,
    {"role": "tool", "tool_call_id": "call_123", "content": file_content}
  ]
}
```

**Connects to Magic:**
> "Mary 'lê' workflow BMad mesmo estando em Groq, não no filesystem local"

#### FR-6.3: Multi-Turn Conversation com Tools

**Requirement:**
Suportar múltiplas rodadas de tool calling até task complete

**Acceptance Criteria:**
- ✅ Turn 1: User → Mary → Tool call (load_file)
- ✅ Turn 2: Tool result → Mary → Tool call (web_search)
- ✅ Turn 3: Search results → Mary → Tool call (save_file)
- ✅ Turn 4: Save confirmed → Mary → Final response
- ✅ Max turns: 10 (prevent infinite loops)

**Connects to Magic:**
> "Mary executa workflow BMad completo via múltiplos tool calls"

#### FR-6.4: Tool Execution Security

**Requirement:**
Validar tool calls para prevenir security issues

**Acceptance Criteria:**
- ✅ Path validation: Prevent `../../etc/passwd`
- ✅ Whitelist: Only allow paths em `.bmad/`, `docs/`, `config/`
- ✅ File size limits: Max 10MB per file
- ✅ Rate limiting: Max 20 tool calls per request
- ✅ Audit: Log all tool executions com user_id, agent, action

---

### FR-5: Configuration & Deployment

**Core Capability:** Sistema config-driven e reproduzível

#### FR-5.1: YAML Configuration System

**Requirement:**
Todas configs em YAML files

**Acceptance Criteria:**
- ✅ `config/rate_limits.yaml` - RPM, burst, window por provider
- ✅ `config/agent_chains.yaml` - Fallback chains por agente
- ✅ `config/providers.yaml` - API base URLs, models
- ✅ `.env` - API keys (não versionado)
- ✅ Validation: Pydantic models validam configs na startup

**Connects to Magic:**
> "Ajustar quem é Mary (Groq vs Cerebras) é só editar YAML, não código"

#### FR-5.2: Docker Compose Setup

**Requirement:**
One-command setup de toda infraestrutura

**Acceptance Criteria:**
- ✅ `docker-compose.yaml` inclui:
  - Redis 7.0+
  - PostgreSQL 15+
  - Prometheus
  - Grafana (com dashboards pré-configurados)
  - Squad API app
  
- ✅ Command: `docker-compose up` → tudo funciona
- ✅ Volumes: Data persiste entre restarts
- ✅ Healthchecks: Services reportam status

**Connects to Magic:**
> "Reproduzir setup em outra máquina = 1 comando"

#### FR-5.3: Environment Variables

**Requirement:**
API keys e secrets via environment variables

**Acceptance Criteria:**
- ✅ `.env.example` - Template com todas vars necessárias
- ✅ Required vars:
  - `GROQ_API_KEY`
  - `CEREBRAS_API_KEY`
  - `GEMINI_API_KEY`
  - `OPENROUTER_API_KEY`
  - `SLACK_WEBHOOK_URL` (optional)
  
- ✅ Load via `python-dotenv`
- ✅ Validation: Error se required vars missing

#### FR-5.4: Documentation

**Requirement:**
Documentação completa para setup e uso

**Acceptance Criteria:**
- ✅ `README.md`:
  - Quick start (5 min to running)
  - Architecture overview (diagram)
  - Configuration guide
  
- ✅ `docs/runbooks/`:
  - Deploy.md - Como deployar
  - Troubleshoot.md - Common issues
  - Scale.md - Como escalar
  
- ✅ `docs/adrs/`:
  - ADR-001: Rate Limiting Strategy
  - ADR-002: Gemini SDK vs REST
  - ADR-003: Worker/Boss Hierarchy

**Connects to Magic:**
> "6 meses depois, Dani consegue re-deployar porque docs estão completos"

---

## Non-Functional Requirements

### Performance

**NFR-P1: Latency Targets**

```yaml
target_latency:
  potentes: <2s (P95)  # Groq llama-3-70b, Gemini Pro
  pequenos: <5s (P95)  # Cerebras llama-3-8b, Gemini Flash
  
measurement:
  - P50: Metade dos requests abaixo do target
  - P95: 95% dos requests abaixo do target
  - P99: 99% dos requests abaixo do target
```

**Why it matters:**
Latência afeta "sensação" de conversar com agente. >5s feels "laggy".

**Connects to Magic:**
> "Mary responde rápido, conversa flui naturalmente"

**NFR-P2: Throughput**

```yaml
target_throughput:
  sustained: 120-130 RPM
  burst: Up to 150 RPM (com burst interleaving)
  
providers_combined:
  groq: 12 RPM
  cerebras: 60 RPM
  gemini_flash: 15 RPM
  openrouter: 12 RPM
  total: 99 RPM (base)
```

**Why it matters:**
Throughput define quantos agentes podem trabalhar simultaneamente.

**NFR-P3: Resource Usage**

```yaml
infrastructure:
  redis:
    memory: <500MB
    connections: <100
  
  postgres:
    storage: <1GB (MVP)
    connections: <50
  
  app:
    cpu: <2 cores
    memory: <1GB
```

**Why it matters:**
Low resource usage = pode rodar em laptop ou VPS barato.

---

### Security

**NFR-S1: API Key Management**

```yaml
storage:
  - API keys em environment variables (nunca hardcoded)
  - .env file NOT versionado (.gitignore)
  - Secrets rotation: Manual (MVP), Vault (future)
  
transmission:
  - HTTPS only para LLM APIs
  - TLS 1.2+ required
```

**Why it matters:**
Proteger API keys = proteger quota free-tier.

**NFR-S2: PII Sanitization (Basic)**

```yaml
implementation:
  - Regex patterns para detectar: emails, phone numbers, CPF
  - Warning: "PII detected, sanitize before sending?"
  - Auto-sanitize: Replace com [REDACTED]
  
scope:
  - Input sanitization (user prompts)
  - Log sanitization (structured logs)
```

**Why it matters:**
Compliance básico, evita leaks acidentais de dados sensíveis.

**NFR-S3: Audit Logging**

```yaml
storage:
  - PostgreSQL audit table
  - Fields: timestamp, user, agent, provider, action, status
  
retention:
  - 90 dias (MVP)
  - 1 ano (production)
```

**Why it matters:**
Rastreabilidade: "O que Mary fez no dia X?"

---

### Scalability

**NFR-SC1: Horizontal Scaling Ready**

```yaml
architecture:
  - Stateless app (FastAPI workers)
  - State em Redis/PostgreSQL (external)
  - Multiple workers can run simultaneously
  
scaling:
  - MVP: 1 worker (sufficient)
  - Production: 2-4 workers (for HA)
```

**Why it matters:**
Preparado para crescer se Dani tiver múltiplos projetos simultâneos.

**NFR-SC2: Redis Cluster Ready**

```yaml
mvp:
  - Single Redis instance (sufficient)
  
production:
  - Redis Cluster (3+ nodes)
  - Sentinel (automatic failover)
```

**Why it matters:**
Elimina Redis como SPOF (single point of failure).

---

### Reliability

**NFR-R1: Availability Target**

```yaml
target: 99.5%+ (measured weekly)

calculation:
  - 1 week = 168 hours
  - 99.5% = max 50 min downtime per week
  - 99.9% = max 10 min downtime per week (stretch goal)
```

**How achieved:**
- Fallback chains (provider fails → use another)
- Auto-throttling (429 spikes → auto-adjust)
- Health checks (detect unhealthy providers)

**Connects to Magic:**
> "Mary sempre disponível, mesmo se Groq falhar"

**NFR-R2: Data Durability**

```yaml
redis:
  - RDB snapshots: Every 1 hour
  - AOF: appendonly (persistence mode)
  - Backup: Daily (if production)
  
postgres:
  - WAL: enabled
  - Backup: Daily (if production)
```

**Why it matters:**
State persistence = conversations não se perdem em restart.

**NFR-R3: Error Recovery**

```yaml
retry_policy:
  - Transient errors (network, timeout): Retry with exponential backoff
  - Rate limit (429): Respect Retry-After header
  - Provider down: Fallback to another provider
  - All providers down: Clear error message + retry suggestion
```

---

### Integration

**NFR-I1: BMad Method Integration**

```yaml
requirement:
  - Must load `.bmad/bmm/agents/*.md` files
  - Parse BMad format (YAML frontmatter + markdown)
  - Support all BMad agent fields: persona, menu, workflows
  
compatibility:
  - BMad version: 6.0.0-alpha.8+
  - Forward compatible: New BMad fields ignored gracefully
```

**Why it matters:**
Squad API é **extensão** de BMad Method, não replacement.

**NFR-I2: Future Integrations**

```yaml
planned:
  - Slack bot (post-MVP)
  - Discord bot (post-MVP)
  - VS Code extension (future)
  - Web UI (Phase 3)
```

**Why it matters:**
Preparado para múltiplos "front-ends" consumirem Squad API.

---

## Implementation Planning

### Epic Breakdown Required

Requisitos acima devem ser decompostos em epics e stories implementáveis.

**Complexidade estimada:**
- **High complexity** (production-ready, múltiplos componentes enterprise)
- **10 semanas investment** (8 semanas + 2 buffer)
- **~15-20 epics estimados**
- **~60-80 stories estimados**

**Estrutura sugerida:**

```
Epic 1: Agent Transformation Engine
  - Story 1.1: Agent Loader (parse .bmad files)
  - Story 1.2: System Prompt Builder
  - Story 1.3: Conversation Manager (Redis state)
  - Story 1.4: Agent Router (config-driven)

Epic 2: Rate Limiting Layer
  - Story 2.1: Token Bucket implementation
  - Story 2.2: Sliding Window (60s)
  - Story 2.3: Auto-Throttling
  - Story 2.4: Global Semaphore

Epic 3: Provider Wrappers
  - Story 3.1: Abstract LLMProvider interface
  - Story 3.2: Groq provider
  - Story 3.3: Cerebras provider
  - Story 3.4: Gemini provider (SDK)
  - Story 3.5: OpenRouter provider

Epic 4: Fallback & Resilience
  - Story 4.1: Fallback chains (config)
  - Story 4.2: Quality validation
  - Story 4.3: Automatic escalation

Epic 5: Observability
  - Story 5.1: Prometheus metrics
  - Story 5.2: Grafana dashboards
  - Story 5.3: Slack alerts
  - Story 5.4: Structured logging

Epic 6: Configuration System
  - Story 6.1: YAML config loader
  - Story 6.2: Environment variables
  - Story 6.3: Pydantic validation

Epic 7: Infrastructure
  - Story 7.1: Docker Compose setup
  - Story 7.2: Redis configuration
  - Story 7.3: PostgreSQL setup

Epic 8: Documentation
  - Story 8.1: README + Quick Start
  - Story 8.2: Runbooks (deploy, troubleshoot)
  - Story 8.3: ADRs (decision records)

... (more epics)
```

**Next Step:** Run `*create-epics-and-stories` workflow para criar breakdown detalhado.

---

## References

- **Product Brief:** `docs/product-brief-squad-api-2025-11-12.md`
- **Technical Research:** `docs/research-technical-2025-11-12.md`

**Key Decisions (from Technical Research):**
- Architecture: Complete Multi-Agent (Option 3)
- Rate Limiting: pyrate-limiter + Redis (Token Bucket + Sliding Window)
- Gemini: SDK oficial (ADR-002)
- Agent Pattern: Hybrid Worker/Boss + Fallback (ADR-003)

---

## Next Steps

**Immediate (agora):**
1. **Epic & Story Breakdown** - Run: `*create-epics-and-stories`
   - Decompose requisitos em stories implementáveis
   - Estimar stories (story points)
   - Prioritizar por valor

**After Epics (Phase 1 - Planning):**
2. **UX Design** (Optional) - Se houver UI:
   - API tem UI? Provavelmente Dashboard/CLI
   - Se sim: Run `workflow create-design`

**Phase 2 (Solutioning):**
3. **Architecture** (Required) - Run: `workflow create-architecture`
   - System design detalhado
   - Technology choices
   - Data models, APIs, infrastructure

4. **Validate Architecture** (Optional) - Quality check
5. **Solutioning Gate Check** (Required) - PRD + Architecture alignment

**Phase 3 (Implementation):**
6. **Sprint Planning** (Required) - Run: `workflow sprint-planning`
   - 8 weeks roadmap
   - Sprint-by-sprint breakdown
   - Story assignment

---

_Este PRD captura a essência do Squad API:_

## **"Transformar LLMs genéricas em agentes BMad especializados - distribuindo o poder do BMad Method"**

**O momento mágico:** Quando você pede "Analise este sistema" e quem responde é **Mary (via Groq)** - não "uma API call", mas uma **analista estratégica** que segue workflows BMad, tem persona completa, e trabalha **pra você**.

_Created through collaborative discovery between Dani and John (PM Agent)._

