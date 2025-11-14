# Squad API - Epic & Story Breakdown

**Project:** Squad API  
**Author:** Dani (with John - PM Agent)  
**Date:** 2025-11-12  
**PRD:** docs/PRD.md

---

## Epic Structure Overview

**Total:** 10 Epics | ~65-75 Stories estimadas | 10 semanas

**Sequencing Logic:**

```
Epic 0: Foundation → Epic 1-2: Core Magic → Epic 3-4: Resilience → 
Epic 5-6: Observability → Epic 7-8: Integration → Epic 9: Launch
```

---

## Epics Summary

### **Epic 0: Project Foundation & Infrastructure** (Semana 1)
**Goal:** Estabelecer base técnica que habilita todo desenvolvimento subsequente  
**Value:** Zero → Running system com infraestrutura completa  
**Stories:** 8 stories

**Why First:** 
- Sem Redis/PostgreSQL/Docker, nada mais funciona
- Foundation habilita desenvolvimento paralelo de epics futuros
- Quick wins: Infra rodando = momentum

---

### **Epic 1: Agent Transformation Engine** (Semanas 2-3)
**Goal:** Carregar agentes BMad e instruir LLMs a incorporá-los  
**Value:** **CORE MAGIC** - LLMs genéricas viram Mary, John, Alex  
**Stories:** 10-12 stories

**Why Second:**
- É o coração do Squad API (o magic!)
- Precisa de Redis (Epic 0 dependency)
- Habilita teste do conceito core logo cedo

---

### **Epic 2: Rate Limiting Layer** (Semana 3)
**Goal:** Garantir squad nunca para por 429 errors  
**Value:** Resiliência básica - sistema não quebra  
**Stories:** 8 stories

**Why Third:**
- Precisa de Agent Transformation para testar (Epic 1)
- Sem rate limiting, impossível testar com APIs reais
- Habilita development contínuo sem interrupções

---

### **Epic 3: Provider Wrappers** (Semana 4)
**Goal:** Wrappers para Groq, Cerebras, Gemini, OpenRouter  
**Value:** Multi-provider diversity = throughput agregado  
**Stories:** 7 stories (1 abstraction + 5 providers + 1 factory)

**Why Fourth:**
- Precisa de Rate Limiting (Epic 2)
- Cada provider testável independentemente
- Habilita distribuição de agentes em múltiplas LLMs

---

### **Epic 4: Fallback & Resilience** (Semana 5)
**Goal:** Fallback automático e auto-throttling adaptativo  
**Value:** 99.5%+ SLA - Mary sempre disponível  
**Stories:** 6 stories

**Why Fifth:**
- Precisa de múltiplos providers (Epic 3)
- Testa resiliência real (simulate failures)
- Completa o core resilience promise

---

### **Epic 5: Observability Foundation** (Semana 5)
**Goal:** Prometheus metrics e structured logging  
**Value:** Visibilidade - "o que está acontecendo?"  
**Stories:** 5 stories

**Why Sixth:**
- Pode começar em paralelo com Epic 4
- Crítico para debugging e tuning
- Foundation para dashboards (Epic 6)

---

### **Epic 6: Monitoring Dashboards** (Semana 6)
**Goal:** Grafana dashboards e Slack alerts  
**Value:** Observabilidade completa - vejo squad trabalhando  
**Stories:** 6 stories

**Why Seventh:**
- Precisa de Prometheus metrics (Epic 5)
- Dashboards tornam sistema "visível"
- Alerts previnem problemas antes de escalar

---

### **Epic 7: Configuration System** (Semana 6)
**Goal:** Config-driven, reproduzível, YAML-based  
**Value:** Reutilizável - ajustar sem código  
**Stories:** 5 stories

**Why Eighth:**
- Pode começar em paralelo com Epic 6
- Consolida configs espalhados em sistema único
- Habilita deployment fácil (Epic 8)

---

### **Epic 8: Deployment & Documentation** (Semana 7)
**Goal:** Docker Compose completo e docs profissionais  
**Value:** Reproduzível em 1 comando  
**Stories:** 7 stories

**Why Ninth:**
- Precisa de todos componentes (Epics 0-7)
- Consolida deployment
- Docs garantem reutilização futura

---

### **Epic 9: Production Readiness** (Semana 8)
**Goal:** Security, audit, compliance, launch prep  
**Value:** Production-ready - pode deployar com confiança  
**Stories:** 8 stories

**Why Last:**
- Precisa de sistema completo (Epics 0-8)
- PII sanitization, audit logs
- Security review, load testing
- Go-live staging → production

---

**Buffer (Semanas 9-10):**
- Ajustes pós-load tests
- Bug fixes críticos
- Documentation gaps
- Polish final

---

## Epic 0: Project Foundation & Infrastructure

**Goal:** Estabelecer base técnica que habilita todo desenvolvimento subsequente  
**Timeline:** Semana 1  
**Value:** Zero → Running system com infraestrutura completa  
**Dependencies:** None (primeiro epic)

---

### Story 0.1: Monorepo Setup e Estrutura Inicial

**As a** desenvolvedor,  
**I want** estrutura de projeto organizada e padronizada,  
**So that** todo código tenha lugar definido e seja fácil navegar.

**Acceptance Criteria:**

**Given** um diretório vazio para Squad API  
**When** executo setup inicial  
**Then** estrutura completa deve existir:

```
squad-api/
├── .github/
│   └── workflows/        # CI/CD (future)
├── config/
│   ├── rate_limits.yaml
│   ├── agent_chains.yaml
│   └── providers.yaml
├── src/
│   ├── __init__.py
│   ├── main.py          # FastAPI entrypoint
│   ├── agents/          # Agent transformation
│   ├── providers/       # LLM provider wrappers
│   ├── rate_limit/      # Rate limiting layer
│   ├── scheduler/       # Burst scheduling
│   ├── metrics/         # Observability
│   └── models/          # Pydantic models
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── docs/
│   ├── runbooks/
│   └── adrs/
├── .env.example
├── .gitignore
├── docker-compose.yaml
├── requirements.txt
├── pytest.ini
└── README.md
```

**And** `.gitignore` exclui: `.env`, `__pycache__`, `*.pyc`, `.pytest_cache`, `venv/`

**Prerequisites:** None

**Technical Notes:**
- Use Python 3.11+ virtual environment
- Git init e initial commit após estrutura
- README inicial com project overview

---

### Story 0.2: Dependencies e Requirements Management

**As a** desenvolvedor,  
**I want** todas dependências Python gerenciadas centralmente,  
**So that** setup é reproduzível e versionado.

**Acceptance Criteria:**

**Given** estrutura de projeto criada  
**When** instalo dependências  
**Then** `requirements.txt` deve incluir:

```txt
# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Rate Limiting
pyrate-limiter==3.1.1
redis[hiredis]==5.0.1

# Async HTTP
aiohttp==3.9.1
httpx==0.25.2

# Retry
tenacity==8.2.3

# LLM SDKs
groq==0.4.1
google-genai==0.2.2

# Config
python-dotenv==1.0.0
pyyaml==6.0.1

# Observability
prometheus-client==0.19.0

# Database
asyncpg==0.29.0
sqlalchemy[asyncio]==2.0.23

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Dev Tools
black==23.12.0
ruff==0.1.8
mypy==1.7.1
```

**And** `pip install -r requirements.txt` funciona sem erros

**Prerequisites:** Story 0.1

**Technical Notes:**
- Pin versions para reproduzibilidade
- Incluir dev tools (black, ruff, mypy)
- Separar em sections (core, rate limiting, etc.)

---

### Story 0.3: Docker Compose - Redis Setup

**As a** desenvolvedor,  
**I want** Redis rodando via Docker Compose,  
**So that** rate limiting e cache tenham backend disponível.

**Acceptance Criteria:**

**Given** Docker instalado  
**When** executo `docker-compose up redis`  
**Then** Redis deve:
- ✅ Rodar em `localhost:6379`
- ✅ Usar imagem `redis:7-alpine`
- ✅ Volume persistente: `./data/redis:/data`
- ✅ Healthcheck: `redis-cli ping` retorna PONG
- ✅ RDB snapshots habilitados (save 900 1)
- ✅ AOF enabled (appendonly yes)

**And** `redis-cli ping` retorna PONG

**Prerequisites:** Story 0.1

**Technical Notes:**
```yaml
# docker-compose.yaml
services:
  redis:
    image: redis:7-alpine
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
```

---

### Story 0.4: Docker Compose - PostgreSQL Setup

**As a** desenvolvedor,  
**I want** PostgreSQL rodando via Docker Compose,  
**So that** audit logs e persistence tenham database disponível.

**Acceptance Criteria:**

**Given** Docker Compose configurado  
**When** executo `docker-compose up postgres`  
**Then** PostgreSQL deve:
- ✅ Rodar em `localhost:5432`
- ✅ Usar imagem `postgres:15-alpine`
- ✅ Database: `squad_api`
- ✅ User/Password via environment variables
- ✅ Volume persistente: `./data/postgres:/var/lib/postgresql/data`
- ✅ Healthcheck: `pg_isready` retorna success

**And** consigo conectar: `psql -h localhost -U squad -d squad_api`

**Prerequisites:** Story 0.1

**Technical Notes:**
```yaml
# docker-compose.yaml
services:
  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: squad_api
      POSTGRES_USER: squad
      POSTGRES_PASSWORD: dev_password
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U squad"]
      interval: 5s
```

---

### Story 0.5: Docker Compose - Prometheus Setup

**As a** desenvolvedor,  
**I want** Prometheus rodando via Docker Compose,  
**So that** metrics podem ser coletadas desde o início.

**Acceptance Criteria:**

**Given** Docker Compose configurado  
**When** executo `docker-compose up prometheus`  
**Then** Prometheus deve:
- ✅ Rodar em `localhost:9090`
- ✅ Usar imagem `prom/prometheus:latest`
- ✅ Config: `./config/prometheus.yml`
- ✅ Scrape Squad API: `http://squad-api:8000/metrics`
- ✅ Scrape interval: 15s
- ✅ Volume persistente: `./data/prometheus:/prometheus`

**And** UI Prometheus acessível em `http://localhost:9090`

**Prerequisites:** Story 0.1

**Technical Notes:**
```yaml
# config/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'squad-api'
    static_configs:
      - targets: ['squad-api:8000']
```

---

### Story 0.6: Docker Compose - Grafana Setup

**As a** desenvolvedor,  
**I want** Grafana rodando via Docker Compose,  
**So that** dashboards estejam disponíveis desde o início.

**Acceptance Criteria:**

**Given** Prometheus rodando  
**When** executo `docker-compose up grafana`  
**Then** Grafana deve:
- ✅ Rodar em `localhost:3000`
- ✅ Usar imagem `grafana/grafana:latest`
- ✅ Datasource: Prometheus auto-configurado
- ✅ Dashboards pré-carregados (provisioned)
- ✅ Login: admin/admin (change on first login)
- ✅ Volume persistente: `./data/grafana:/var/lib/grafana`

**And** UI Grafana acessível em `http://localhost:3000`

**Prerequisites:** Story 0.5

**Technical Notes:**
- Provisioning: `./config/grafana/` com datasources e dashboards
- Dashboards vêm de Epic 6, mas structure ready agora

---

### Story 0.7: FastAPI Application Skeleton

**As a** desenvolvedor,  
**I want** FastAPI app básico rodando,  
**So that** tenho entrypoint para adicionar endpoints.

**Acceptance Criteria:**

**Given** estrutura de projeto criada  
**When** executo `python src/main.py`  
**Then** FastAPI deve:
- ✅ Rodar em `localhost:8000`
- ✅ Endpoint `/health` retorna `{"status": "ok"}`
- ✅ Endpoint `/metrics` retorna metrics Prometheus format (vazio inicialmente)
- ✅ Swagger docs em `/docs`
- ✅ CORS habilitado (development mode)

**And** `curl http://localhost:8000/health` retorna 200 OK

**Prerequisites:** Story 0.2

**Technical Notes:**
```python
# src/main.py
from fastapi import FastAPI
from prometheus_client import make_asgi_app

app = FastAPI(title="Squad API", version="0.1.0")

@app.get("/health")
async def health():
    return {"status": "ok"}

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

---

### Story 0.8: Docker Compose - Squad API Service Integration

**As a** desenvolvedor,  
**I want** Squad API rodando via Docker Compose,  
**So that** todo stack (Redis, PostgreSQL, Prometheus, Grafana, App) sobe com 1 comando.

**Acceptance Criteria:**

**Given** todos services configurados individualmente  
**When** executo `docker-compose up`  
**Then** todos services devem:
- ✅ Redis: healthy
- ✅ PostgreSQL: healthy
- ✅ Prometheus: scraping Squad API
- ✅ Grafana: acessível com Prometheus datasource
- ✅ Squad API: `/health` retorna ok

**And** `docker-compose ps` mostra todos services "Up (healthy)"

**Prerequisites:** Stories 0.3, 0.4, 0.5, 0.6, 0.7

**Technical Notes:**
```yaml
# docker-compose.yaml
services:
  redis: ...
  postgres: ...
  prometheus: ...
  grafana: ...
  
  squad-api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://squad:dev_password@postgres:5432/squad_api
    volumes:
      - ./src:/app/src
      - ./config:/app/config
```

**Epic 0 Complete!** 🎉  
**Value Delivered:** Infraestrutura completa rodando com `docker-compose up`

---

## Epic 1: Agent Transformation Engine

**Goal:** Carregar agentes BMad e instruir LLMs a incorporá-los  
**Timeline:** Semanas 2-3  
**Value:** **CORE MAGIC** - LLMs genéricas viram Mary, John, Alex  
**Dependencies:** Epic 0 (Redis para cache)

---

### Story 1.1: BMad Agent File Parser

**As a** desenvolvedor,  
**I want** parser para arquivos `.bmad/bmm/agents/*.md`,  
**So that** posso extrair definições de agentes BMad.

**Acceptance Criteria:**

**Given** arquivo `.bmad/bmm/agents/analyst.md` exists  
**When** executo parser  
**Then** deve extrair:
- ✅ YAML frontmatter: name, description
- ✅ XML agent block: name, title, icon
- ✅ Persona: role, identity, communication_style, principles
- ✅ Menu items: cmd, workflow paths
- ✅ Activation steps

**And** retorna `AgentDefinition` Pydantic model

**Prerequisites:** Story 0.2

**Technical Notes:**
```python
# src/agents/parser.py
import yaml
import xml.etree.ElementTree as ET

class AgentParser:
    def parse(self, filepath: str) -> AgentDefinition:
        content = self.read_file(filepath)
        
        # Parse YAML frontmatter
        frontmatter = yaml.safe_load(self.extract_frontmatter(content))
        
        # Parse XML agent block
        xml_block = self.extract_xml_block(content)
        tree = ET.fromstring(xml_block)
        
        # Extract persona
        persona = self.parse_persona(tree)
        
        # Extract menu
        menu = self.parse_menu(tree)
        
        return AgentDefinition(
            id=frontmatter['name'],
            name=tree.get('name'),
            title=tree.get('title'),
            icon=tree.get('icon'),
            persona=persona,
            menu=menu
        )
```

---

### Story 1.2: Agent Definition Models (Pydantic)

**As a** desenvolvedor,  
**I want** Pydantic models para agent definitions,  
**So that** tenho type safety e validation.

**Acceptance Criteria:**

**Given** agent parsed de arquivo  
**When** crio `AgentDefinition` instance  
**Then** deve validar:
- ✅ `id`: string não-vazia
- ✅ `name`: string não-vazia
- ✅ `title`: string não-vazia
- ✅ `persona`: Persona model válido
- ✅ `menu`: List[MenuItem] válida

**And** validation errors são claros e específicos

**Prerequisites:** None (pode ser paralelo com 1.1)

**Technical Notes:**
```python
# src/models/agent.py
from pydantic import BaseModel, Field
from typing import List, Optional

class Persona(BaseModel):
    role: str = Field(..., min_length=1)
    identity: str = Field(..., min_length=1)
    communication_style: str = Field(..., min_length=1)
    principles: str = Field(..., min_length=1)

class MenuItem(BaseModel):
    cmd: str  # "*help", "*research", etc.
    description: Optional[str] = None
    workflow: Optional[str] = None
    exec: Optional[str] = None

class AgentDefinition(BaseModel):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    icon: str = ""
    persona: Persona
    menu: List[MenuItem]
```

---

### Story 1.3: Agent Loader Service

**As a** desenvolvedor,  
**I want** service que carrega todos agentes BMad na startup,  
**So that** agentes estejam disponíveis para orquestração.

**Acceptance Criteria:**

**Given** arquivos `.bmad/bmm/agents/*.md` existem  
**When** Squad API inicia  
**Then** deve:
- ✅ Scan directory `.bmad/bmm/agents/`
- ✅ Parse todos arquivos `.md`
- ✅ Carregar agentes: analyst, pm, architect, sm, dev, tea, ux-designer, tech-writer
- ✅ Store em cache (Redis) com TTL 1 hora
- ✅ Log: "Loaded 8 BMad agents"

**And** endpoint `GET /api/v1/agents/available` retorna lista completa

**Prerequisites:** Stories 1.1, 1.2

**Technical Notes:**
```python
# src/agents/loader.py
class AgentLoader:
    def __init__(self, bmad_path: str, redis_client):
        self.bmad_path = bmad_path
        self.redis = redis_client
        self.parser = AgentParser()
    
    async def load_all(self) -> Dict[str, AgentDefinition]:
        agents_dir = Path(self.bmad_path) / "bmm/agents"
        agents = {}
        
        for file in agents_dir.glob("*.md"):
            if file.stem in ['README', 'index']:
                continue
            
            agent = self.parser.parse(str(file))
            agents[agent.id] = agent
            
            # Cache em Redis
            await self.redis.setex(
                f"agent:{agent.id}",
                3600,  # 1 hour TTL
                agent.model_dump_json()
            )
        
        return agents
```

---

### Story 1.4: System Prompt Builder

**As a** orquestrador,  
**I want** construir system prompt completo que instrui LLM a incorporar agente,  
**So that** LLM externa age como Mary, John, etc.

**Acceptance Criteria:**

**Given** AgentDefinition carregado (ex: Mary/Analyst)  
**When** construo system prompt  
**Then** deve incluir:

```
You are Mary, a Business Analyst with 8+ years experience.

PERSONA:
- Role: Strategic Business Analyst + Requirements Expert
- Identity: Senior analyst with deep expertise in market research, competitive analysis, and requirements elicitation.
- Communication Style: Systematic and probing. Connects dots others miss. Structures findings hierarchically.
- Principles: Every business challenge has root causes waiting to be discovered. Ground findings in verifiable evidence.

MENU:
1. Show numbered menu (*help)
2. Start workflow-init (*workflow-init)
3. Check workflow status (*workflow-status)
4. Guide through Brainstorming (*brainstorm-project)
5. Produce Project Brief (*product-brief)
6. Document existing Project (*document-project)
7. Guide through Research (*research)
8. Consult other expert agents (*party-mode)
9. Advanced elicitation (*adv-elicit)
10. Exit (*exit)

RULES:
- ALWAYS communicate in PT-BR
- Stay in character until exit selected
- Menu triggers use asterisk (*)
- Number all lists, use letters for sub-options
- Load files ONLY when executing menu items

You must fully embody this agent's persona. NEVER break character until exit command.
```

**And** prompt length < 4000 tokens (fit em context window)

**Prerequisites:** Stories 1.1, 1.2, 1.3

**Technical Notes:**
```python
# src/agents/prompt_builder.py
class SystemPromptBuilder:
    def build(self, agent: AgentDefinition, user_config: dict) -> str:
        sections = [
            self._intro(agent),
            self._persona(agent.persona),
            self._menu(agent.menu),
            self._rules(user_config),  # PT-BR, etc.
            self._activation_reminder()
        ]
        return "\n\n".join(sections)
```

---

### Story 1.5: Conversation State Manager (Redis)

**As a** orquestrador,  
**I want** gerenciar estado de conversação por agente,  
**So that** Mary "lembra" do que foi discutido anteriormente.

**Acceptance Criteria:**

**Given** usuário conversando com Mary via Groq  
**When** envia múltiplas mensagens  
**Then** sistema deve:
- ✅ Store conversation history em Redis
- ✅ Key: `conversation:{user_id}:{agent_id}`
- ✅ Value: JSON array de messages
- ✅ TTL: 1 hora de inatividade
- ✅ Max messages: 50 (rolling window)

**And** próxima mensagem inclui history completo no context

**Prerequisites:** Stories 0.3, 1.4

**Technical Notes:**
```python
# src/agents/conversation.py
class ConversationManager:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def add_message(
        self, 
        user_id: str, 
        agent_id: str, 
        role: str,  # "user" or "assistant"
        content: str
    ):
        key = f"conversation:{user_id}:{agent_id}"
        
        # Get existing
        history = await self.get_history(user_id, agent_id)
        
        # Add new
        history.append({"role": role, "content": content})
        
        # Trim to last 50
        history = history[-50:]
        
        # Save with 1h TTL
        await self.redis.setex(
            key,
            3600,
            json.dumps(history)
        )
```

---

### Story 1.6: Agent Router Core Logic

**As a** orquestrador,  
**I want** mapear agente BMad → LLM provider,  
**So that** sei qual LLM vai incorporar qual agente.

**Acceptance Criteria:**

**Given** config `agent_chains.yaml` exists  
**When** requisito executar "analyst"  
**Then** deve:
- ✅ Lookup chain: analyst → [cerebras/llama-3-8b, groq/llama-3-70b]
- ✅ Return primary: cerebras/llama-3-8b (worker tier)
- ✅ Store fallback: groq/llama-3-70b (boss tier)

**And** router é config-driven (editar YAML, não código)

**Prerequisites:** Story 1.3

**Technical Notes:**
```python
# src/agents/router.py
class AgentRouter:
    def __init__(self, config_path: str):
        self.chains = self.load_config(config_path)
    
    def get_provider(self, agent_id: str) -> ProviderConfig:
        chain = self.chains['agents'][agent_id]
        primary = chain[0]  # First in chain
        return self.parse_provider(primary)
    
    def get_fallback_chain(self, agent_id: str) -> List[ProviderConfig]:
        chain = self.chains['agents'][agent_id]
        return [self.parse_provider(p) for p in chain]
```

**Config:**
```yaml
# config/agent_chains.yaml
agents:
  analyst:
    - cerebras/llama-3-8b  # worker
    - groq/llama-3-70b     # boss
  
  pm:
    - cerebras/llama-3-8b
    - groq/llama-3-70b
  
  architect:
    - groq/llama-3-70b
    - gemini/gemini-2.5-pro
```

---

### Story 1.7: Agent Execution Orchestrator

**As a** usuário (Dani),  
**I want** endpoint que executa agente BMad via LLM externa,  
**So that** posso pedir "Mary, analise este sistema" e receber resposta.

**Acceptance Criteria:**

**Given** agentes carregados e providers configurados  
**When** envio request:
```json
POST /api/v1/agent/execute
{
  "agent": "analyst",
  "task": "Analise este sistema: ...",
  "context": {}
}
```

**Then** sistema deve:
- ✅ Load agent definition (Mary)
- ✅ Build system prompt (Story 1.4)
- ✅ Get conversation history (Story 1.5)
- ✅ Route to provider (Story 1.6): cerebras/llama-3-8b
- ✅ Call LLM com system + user prompts
- ✅ Save response em conversation history
- ✅ Return response

**And** response format:
```json
{
  "agent": "analyst",
  "agent_name": "Mary",
  "provider": "cerebras",
  "model": "llama-3-8b",
  "response": "...",  # Mary's analysis
  "metadata": {
    "latency_ms": 1850,
    "tokens_input": 2500,
    "tokens_output": 1200
  }
}
```

**Prerequisites:** Stories 1.3, 1.4, 1.5, 1.6

**Technical Notes:**
```python
# src/agents/orchestrator.py
class AgentOrchestrator:
    def __init__(self, loader, prompt_builder, conv_manager, router):
        self.loader = loader
        self.prompt_builder = prompt_builder
        self.conv = conv_manager
        self.router = router
    
    async def execute(
        self, 
        user_id: str,
        request: AgentExecutionRequest
    ) -> AgentExecutionResponse:
        # 1. Load agent
        agent = await self.loader.get(request.agent)
        
        # 2. Build system prompt
        system_prompt = self.prompt_builder.build(agent)
        
        # 3. Get history
        history = await self.conv.get_history(user_id, request.agent)
        
        # 4. Route to provider
        provider = self.router.get_provider(request.agent)
        
        # 5. Call LLM (next epic will implement)
        response = await provider.call(
            system_prompt=system_prompt,
            user_prompt=request.task,
            history=history
        )
        
        # 6. Save to history
        await self.conv.add_message(user_id, request.agent, "user", request.task)
        await self.conv.add_message(user_id, request.agent, "assistant", response.content)
        
        return response
```

---

### Story 1.8: Agent List Endpoint

**As a** usuário,  
**I want** listar todos agentes BMad disponíveis,  
**So that** sei quais especialistas posso usar.

**Acceptance Criteria:**

**Given** agentes carregados  
**When** chamo `GET /api/v1/agents/available`  
**Then** retorna:
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
      "provider": "cerebras",
      "model": "llama-3-8b",
      "workflows": ["research", "product-brief", "workflow-init", ...]
    },
    {
      "id": "pm",
      "name": "John",
      "title": "Product Manager",
      "icon": "📋",
      ...
    }
  ]
}
```

**Prerequisites:** Story 1.3

**Technical Notes:**
- Endpoint simples, apenas lista agents loaded
- Include provider assignment de router

---

### Story 1.9: Context Window Management

**As a** orquestrador,  
**I want** gerenciar tamanho de context window,  
**So that** não estouro 1M token limit das LLMs.

**Acceptance Criteria:**

**Given** conversation history > 50 messages  
**When** construo context para LLM call  
**Then** deve:
- ✅ Token counting (approximado): ~4 chars = 1 token
- ✅ System prompt: ~3000 tokens
- ✅ History: Últimas N messages que fit em 100k tokens
- ✅ User prompt: Current message
- ✅ Total: < 200k tokens (safety margin de 1M)

**And** se history muito longa: trim oldest messages

**Prerequisites:** Story 1.5

**Technical Notes:**
```python
# src/agents/context.py
class ContextWindowManager:
    MAX_CONTEXT_TOKENS = 200_000  # Safety margin (1M available)
    
    def build_context(
        self,
        system_prompt: str,
        history: List[dict],
        user_prompt: str
    ) -> List[dict]:
        # Approximate token counting
        tokens_system = len(system_prompt) // 4
        tokens_user = len(user_prompt) // 4
        
        budget_remaining = self.MAX_CONTEXT_TOKENS - tokens_system - tokens_user
        
        # Fit history in budget
        fitted_history = self.fit_history(history, budget_remaining)
        
        return [
            {"role": "system", "content": system_prompt},
            *fitted_history,
            {"role": "user", "content": user_prompt}
        ]
```

---

### Story 1.10: Agent Hot-Reload Support

**As a** desenvolvedor,  
**I want** agentes recarregados automaticamente se arquivos mudarem,  
**So that** posso iterar em agent definitions sem restart.

**Acceptance Criteria:**

**Given** Squad API rodando  
**When** edito `.bmad/bmm/agents/analyst.md`  
**Then** deve:
- ✅ Detect file change (watchdog)
- ✅ Re-parse agent definition
- ✅ Update cache (Redis)
- ✅ Log: "Reloaded agent: analyst"
- ✅ Next request usa new definition

**And** no restart necessário

**Prerequisites:** Story 1.3

**Technical Notes:**
```python
# src/agents/watcher.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class AgentFileWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.md'):
            agent_id = Path(event.src_path).stem
            self.reload_agent(agent_id)
```

---

### Story 1.11: Basic Integration Test - Agent Execution

**As a** desenvolvedor,  
**I want** teste que valida agent execution end-to-end,  
**So that** sei que transformação Mary funciona.

**Acceptance Criteria:**

**Given** Squad API rodando com mock LLM provider  
**When** executo teste:
```python
response = await client.post("/api/v1/agent/execute", json={
    "agent": "analyst",
    "task": "Olá Mary, tudo bem?"
})
```

**Then** deve:
- ✅ Status: 200 OK
- ✅ Response contains: agent="analyst", agent_name="Mary"
- ✅ Mock LLM received system prompt com persona Mary
- ✅ Response é em PT-BR (communication_language)

**And** conversation history salva em Redis

**Prerequisites:** Story 1.7

**Technical Notes:**
- Use pytest + httpx.AsyncClient
- Mock provider (não chama API real)
- Valida integration completa

---

### Story 1.12: Error Handling - Agent Not Found

**As a** usuário,  
**I want** erro claro se agente não existe,  
**So that** sei que digitei nome errado.

**Acceptance Criteria:**

**Given** Squad API rodando  
**When** chamo agente inexistente:
```json
POST /api/v1/agent/execute
{"agent": "invalid_agent", "task": "..."}
```

**Then** deve retornar:
```json
HTTP 404 Not Found
{
  "error": "agent_not_found",
  "message": "Agent 'invalid_agent' not found",
  "available_agents": ["analyst", "pm", "architect", ...]
}
```

**Prerequisites:** Story 1.7

**Technical Notes:**
- FastAPI HTTPException
- Include helpful message com agents disponíveis

### Story 1.13: Tool Definition System

**As a** orquestrador,  
**I want** definir tools que Mary pode usar,  
**So that** ela pode executar ações (load files, save outputs, web search).

**Acceptance Criteria:**

**Given** Mary via Groq precisa ler workflow  
**When** defino tools disponíveis  
**Then** deve incluir:
- ✅ `load_file(path)` - Carrega workflow, agent, config
- ✅ `save_file(path, content)` - Salva research report, etc.
- ✅ `web_search(query)` - Busca web (para research workflows)
- ✅ `list_directory(path)` - Lista arquivos disponíveis
- ✅ `update_workflow_status(workflow, file)` - Atualiza bmm-workflow-status.yaml

**And** tools em formato OpenAI-compatible (Groq, Gemini usam)

**Prerequisites:** None

**Technical Notes:**
```python
# src/tools/definitions.py
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "load_file",
            "description": "Load workflow, agent, or config file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["path"]
            }
        }
    },
    # ... outros tools
]
```

---

### Story 1.14: Tool Executor Engine

**As a** sistema,  
**I want** executar tools chamadas por Mary via Groq,  
**So that** ela pode ler workflows e salvar outputs.

**Acceptance Criteria:**

**Given** Mary via Groq retorna tool_call  
**When** Squad API processa response  
**Then** deve:
- ✅ Parse tool_calls array
- ✅ Extract: tool name, arguments, call_id
- ✅ Execute tool localmente
  - `load_file` → Read from filesystem
  - `save_file` → Write to filesystem
  - `web_search` → Call search API
- ✅ Return result para Mary em next turn
- ✅ Security: Validate paths (whitelist)

**And** Mary recebe tool result e pode continuar workflow

**Prerequisites:** Story 1.13

**Technical Notes:**
```python
# src/tools/executor.py
class ToolExecutor:
    WHITELIST_PATHS = ['.bmad/', 'docs/', 'config/']
    
    async def execute(self, tool_name: str, arguments: dict) -> str:
        # Security validation
        if tool_name == "load_file":
            path = arguments['path']
            self.validate_path(path)
            return self.read_file(path)
        
        elif tool_name == "save_file":
            path = arguments['path']
            content = arguments['content']
            self.validate_path(path)
            self.write_file(path, content)
            return f"File saved: {path}"
        
        # ... outros tools
    
    def validate_path(self, path: str):
        # Prevent directory traversal
        if '..' in path:
            raise SecurityError("Path traversal not allowed")
        
        # Whitelist check
        if not any(path.startswith(p) for p in self.WHITELIST_PATHS):
            raise SecurityError(f"Path not in whitelist: {path}")
```

---

### Story 1.15: Multi-Turn Tool Calling Loop

**As a** orquestrador,  
**I want** suportar múltiplas rodadas de tool calling,  
**So that** Mary pode executar workflow BMad completo (load → search → save).

**Acceptance Criteria:**

**Given** Mary executando research workflow  
**When** conversation progride  
**Then** deve:
- ✅ Turn 1: User → Mary → tool_call(load_file: workflow.yaml)
- ✅ Turn 2: Tool result → Mary → tool_call(web_search: "LLM rate limiting 2025")
- ✅ Turn 3: Search results → Mary → tool_call(save_file: research report)
- ✅ Turn 4: Save confirmed → Mary → "Research workflow completo!"
- ✅ Max turns: 10 (prevent infinite loops)

**And** cada turn preserva conversation history

**Prerequisites:** Stories 1.14, 1.5 (conversation manager)

**Technical Notes:**
```python
# src/agents/orchestrator.py (updated)
async def execute(self, request):
    messages = self.build_initial_messages(request)
    max_turns = 10
    
    for turn in range(max_turns):
        # Call LLM with tools
        response = await provider.call(
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )
        
        # Check if tool_calls presente
        if response.tool_calls:
            # Execute tools
            for tool_call in response.tool_calls:
                result = await self.tool_executor.execute(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments)
                )
                
                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
            
            # Continue loop (next turn)
            continue
        else:
            # No more tool calls, final response
            return response.content
```

---

### Story 1.16: Web Search Tool Integration

**As a** Mary via Groq,  
**I want** fazer web search quando research workflow pedir,  
**So that** posso buscar dados atualizados de 2025.

**Acceptance Criteria:**

**Given** Mary executando research workflow  
**When** precisa de dados atuais  
**Then** pode:
- ✅ Call tool: `web_search(query="LLM rate limiting best practices 2025")`
- ✅ Squad API executa search (Tavily API ou similar)
- ✅ Return: Top 5 results com titles, URLs, snippets
- ✅ Mary usa results para escrever research report

**And** search results são relevantes e atualizados

**Prerequisites:** Story 1.14

**Technical Notes:**
```python
# src/tools/web_search.py
import httpx

async def web_search(query: str, max_results: int = 5) -> str:
    # Use Tavily API (ou similar)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.tavily.com/search",
            json={"query": query, "max_results": max_results},
            headers={"Authorization": f"Bearer {TAVILY_API_KEY}"}
        )
        results = response.json()['results']
        
        # Format para Mary
        formatted = []
        for r in results:
            formatted.append(f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}\n")
        
        return "\n---\n".join(formatted)
```

**Epic 1 Complete!** 🎉  
**Value Delivered:** LLMs externas incorporam agentes BMad + executam workflows via tools - **Core Magic completo!**

---

## Epic 2: Rate Limiting Layer

**Goal:** Garantir squad nunca para por 429 errors  
**Timeline:** Semana 3  
**Value:** Resiliência básica - sistema não quebra  
**Dependencies:** Epic 0 (Redis), Epic 1 (para testar com agents reais)

---

### Story 2.1: Token Bucket Algorithm Implementation

**As a** desenvolvedor,  
**I want** Token Bucket algorithm usando pyrate-limiter,  
**So that** posso enforçar rate limits com burst support.

**Acceptance Criteria:**

**Given** pyrate-limiter instalado  
**When** crio limiter para Groq (12 RPM, burst 2)  
**Then** deve:
- ✅ Allow burst de 2 requests imediatos
- ✅ Refill rate: 12/60 = 0.2 tokens/second
- ✅ Block 13th request em <60s
- ✅ Allow requests depois de refill

**And** teste simula 15 requests em 10s: 2 pass, 13 wait

**Prerequisites:** Story 0.2, 0.3

**Technical Notes:**
```python
# src/rate_limit/limiter.py
from pyrate_limiter import Limiter, TokenBucket, RedisBucket
import redis.asyncio as redis

class RateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.limiters = {}
    
    def create_limiter(self, provider: str, rpm: int, burst: int):
        bucket = RedisBucket(f'bucket:{provider}', self.redis)
        limiter = Limiter(
            TokenBucket(rate=rpm, capacity=burst),
            bucket=bucket
        )
        self.limiters[provider] = limiter
        return limiter
```

---

### Story 2.2: Sliding Window (60s) Implementation

**As a** desenvolvedor,  
**I want** sliding window de 60s tracker,  
**So that** previno burst clustering em minute boundaries.

**Acceptance Criteria:**

**Given** requests sendo feitos  
**When** sistema track requests  
**Then** deve:
- ✅ Store timestamps em Redis sorted set
- ✅ Key: `window:{provider}`
- ✅ Score: unix timestamp
- ✅ Cleanup: Remove timestamps > 60s old
- ✅ Check: count(last 60s) < RPM limit

**And** teste valida: 12 requests em 10s, depois 12 em next 10s → 2nd batch waits

**Prerequisites:** Story 0.3

**Technical Notes:**
```python
# src/rate_limit/sliding_window.py
class SlidingWindow:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def add_request(self, provider: str):
        key = f"window:{provider}"
        now = time.time()
        
        # Add current request
        await self.redis.zadd(key, {str(uuid.uuid4()): now})
        
        # Cleanup old (>60s)
        cutoff = now - 60
        await self.redis.zremrangebyscore(key, 0, cutoff)
        
        # Set expiry (cleanup key after 60s of no activity)
        await self.redis.expire(key, 60)
    
    async def check_limit(self, provider: str, rpm_limit: int) -> bool:
        key = f"window:{provider}"
        now = time.time()
        cutoff = now - 60
        
        # Count requests in last 60s
        count = await self.redis.zcount(key, cutoff, now)
        
        return count < rpm_limit
```

---

### Story 2.3: Combined Token Bucket + Sliding Window

**As a** orquestrador,  
**I want** combinar Token Bucket com Sliding Window,  
**So that** tenho burst support AND precision tracking.

**Acceptance Criteria:**

**Given** both algorithms implementados  
**When** faço request  
**Then** deve passar por AMBOS checks:
- ✅ Token Bucket: Tenho tokens disponíveis?
- ✅ Sliding Window: Count(last 60s) < RPM limit?
- ✅ Both pass → Allow request
- ✅ Either fails → Block request

**And** combined approach previne 429s better que isolated

**Prerequisites:** Stories 2.1, 2.2

**Technical Notes:**
```python
# src/rate_limit/combined.py
class CombinedRateLimiter:
    def __init__(self, redis_client):
        self.token_bucket = RateLimiter(redis_client)
        self.sliding_window = SlidingWindow(redis_client)
    
    async def acquire(self, provider: str):
        """Context manager for rate-limited call"""
        # Check sliding window first (cheaper)
        config = self.get_provider_config(provider)
        
        if not await self.sliding_window.check_limit(provider, config.rpm):
            raise RateLimitExceeded(f"{provider}: Window full")
        
        # Then acquire token bucket
        async with self.token_bucket.limiters[provider].ratelimit(
            f'{provider}_job',
            delay=True
        ):
            # Add to sliding window
            await self.sliding_window.add_request(provider)
            yield
```

---

### Story 2.4: Global Semaphore Implementation

**As a** orquestrador,  
**I want** limitar concorrência total do sistema,  
**So that** nunca overwhelm network ou Redis.

**Acceptance Criteria:**

**Given** max_concurrent = 12 (configurado)  
**When** 15 requests chegam simultaneamente  
**Then** deve:
- ✅ First 12: Execute imediatamente
- ✅ Remaining 3: Queue (FIFO)
- ✅ Quando 1 completa: Next na queue executa
- ✅ Fair queueing (não favorece nenhum provider)

**And** teste valida: 20 concurrent requests → max 12 simultâneos

**Prerequisites:** None (asyncio nativo)

**Technical Notes:**
```python
# src/rate_limit/semaphore.py
import asyncio

class GlobalSemaphore:
    def __init__(self, max_concurrent: int = 12):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent
    
    async def acquire(self):
        """Context manager"""
        async with self.semaphore:
            yield
```

Usage:
```python
async with global_semaphore.acquire():
    async with rate_limiter.acquire(provider):
        response = await provider.call(...)
```

---

### Story 2.5: Retry with Exponential Backoff

**As a** orquestrador,  
**I want** retry logic com exponential backoff,  
**So that** transient errors são recuperados automaticamente.

**Acceptance Criteria:**

**Given** LLM call falha com network error  
**When** sistema retenta  
**Then** deve:
- ✅ Retry delays: 1s, 2s, 4s, 8s, 16s (max 30s)
- ✅ Max retries: 5
- ✅ Jitter: +/- 20% random (prevent thundering herd)
- ✅ Exponential backoff formula: min(2^attempt * base_delay, max_delay)

**And** teste simula 3 failures → 4th attempt succeeds

**Prerequisites:** Story 0.2 (tenacity library)

**Technical Notes:**
```python
# src/providers/retry.py
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(
        multiplier=1,
        min=1,
        max=30
    ),
    reraise=True
)
async def call_with_retry(provider, prompt):
    return await provider.call(prompt)
```

---

### Story 2.6: Retry-After Header Support (429 Responses)

**As a** orquestrador,  
**I want** respeitar Retry-After header em 429 responses,  
**So that** não desperdiço retries e respeito API guidance.

**Acceptance Criteria:**

**Given** LLM API retorna 429 com `Retry-After: 30`  
**When** sistema processa response  
**Then** deve:
- ✅ Parse `Retry-After` header (seconds)
- ✅ Wait exatamente esse tempo (não exponential backoff)
- ✅ Log: "429 from Groq, Retry-After: 30s, waiting..."
- ✅ Retry após 30s
- ✅ Se no Retry-After header: fallback to exponential backoff

**And** teste mock valida comportamento

**Prerequisites:** Story 2.5

**Technical Notes:**
```python
# src/providers/retry_after.py
async def call_with_retry_after(provider, prompt):
    try:
        return await provider.call(prompt)
    except RateLimitError as e:
        retry_after = e.response.headers.get('Retry-After')
        
        if retry_after:
            wait_time = int(retry_after)
            logger.info(f"429 from {provider}, Retry-After: {wait_time}s")
            await asyncio.sleep(wait_time)
            return await provider.call(prompt)
        else:
            # Fallback to exponential
            raise  # Let tenacity handle
```

---

### Story 2.7: Rate Limiter Integration com Agent Orchestrator

**As a** orquestrador,  
**I want** rate limiting integrado em agent execution,  
**So that** todo LLM call passa por rate limiting automaticamente.

**Acceptance Criteria:**

**Given** agent execution request  
**When** sistema chama LLM  
**Then** deve:
- ✅ Global semaphore: Acquire slot
- ✅ Token bucket: Acquire token
- ✅ Sliding window: Check e add timestamp
- ✅ LLM call: Execute
- ✅ Release: Global semaphore released

**And** ordem é importante: semaphore → bucket → window → call

**Prerequisites:** Stories 1.7, 2.3, 2.4

**Technical Notes:**
```python
# src/agents/orchestrator.py (updated)
async def execute(...):
    ...
    
    # Rate limiting wrapper
    async with self.global_semaphore.acquire():
        async with self.rate_limiter.acquire(provider.name):
            response = await provider.call(
                system_prompt=system_prompt,
                user_prompt=request.task
            )
    
    ...
```

---

### Story 2.8: Rate Limiting Metrics (Basic)

**As a** operador,  
**I want** métricas básicas de rate limiting,  
**So that** posso monitorar health.

**Acceptance Criteria:**

**Given** Prometheus configurado  
**When** requests sendo feitos  
**Then** deve expor:
- ✅ `llm_requests_total{provider, status}` - Counter
- ✅ `llm_requests_429_total{provider}` - Counter de 429 errors
- ✅ `llm_bucket_tokens_available{provider}` - Gauge (tokens disponíveis)
- ✅ `llm_window_occupancy{provider}` - Gauge (requests em last 60s)

**And** `/metrics` endpoint retorna essas metrics

**Prerequisites:** Stories 0.5, 2.3

**Technical Notes:**
```python
# src/metrics/rate_limiting.py
from prometheus_client import Counter, Gauge

requests_total = Counter(
    'llm_requests_total',
    'Total requests',
    ['provider', 'status']
)

requests_429 = Counter(
    'llm_requests_429_total',
    '429 errors',
    ['provider']
)

bucket_tokens = Gauge(
    'llm_bucket_tokens_available',
    'Available tokens',
    ['provider']
)
```

**Epic 2 Complete!** 🎉  
**Value Delivered:** Rate limiting funcional - 429 errors < 1%

---

## Epic 3: Provider Wrappers

**Goal:** Wrappers para Groq, Cerebras, Gemini, OpenRouter  
**Timeline:** Semana 4  
**Value:** Multi-provider diversity = throughput agregado (99 RPM)  
**Dependencies:** Epic 2 (Rate Limiting)

---

### Story 3.1: LLMProvider Abstract Interface

**As a** desenvolvedor,  
**I want** interface abstrata para todos providers,  
**So that** posso trocar providers sem mudar código do orquestrador.

**Acceptance Criteria:**

**Given** múltiplos providers (Groq, Cerebras, Gemini, etc.)  
**When** defino interface comum  
**Then** deve incluir:
- ✅ `async def call(system, user, max_tokens, temp) -> LLMResponse`
- ✅ `async def health_check() -> bool`
- ✅ `async def count_tokens(text) -> int`
- ✅ Properties: `name`, `model`, `rpm_limit`

**And** todos providers implementam essa interface

**Prerequisites:** None

**Technical Notes:**
```python
# src/providers/base.py
from abc import ABC, abstractmethod
from typing import Optional

class LLMResponse(BaseModel):
    content: str
    tokens_input: int
    tokens_output: int
    latency_ms: int
    model: str
    finish_reason: str

class LLMProvider(ABC):
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.name = config.name
        self.model = config.model
    
    @abstractmethod
    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> LLMResponse:
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        pass
```

---

### Story 3.2: Groq Provider Implementation

**As a** orquestrador,  
**I want** wrapper para Groq API,  
**So that** posso usar Groq Llama-3-70B como agente Boss.

**Acceptance Criteria:**

**Given** Groq API key configurado  
**When** chamo Groq provider  
**Then** deve:
- ✅ Use `groq` Python SDK
- ✅ Suporte models: `llama-3-70b-8192`, `llama-3-8b-8192`
- ✅ Return LLMResponse com: content, tokens, latency
- ✅ Handle errors: network, timeout, 429
- ✅ Health check: ping API

**And** teste valida call básico funciona

**Prerequisites:** Story 3.1

**Technical Notes:**
```python
# src/providers/groq_provider.py
from groq import AsyncGroq

class GroqProvider(LLMProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.client = AsyncGroq(api_key=config.api_key)
    
    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> LLMResponse:
        start = time.time()
        
        response = await self.client.chat.completions.create(
            model=self.model,  # llama-3-70b-8192
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        latency = int((time.time() - start) * 1000)
        
        return LLMResponse(
            content=response.choices[0].message.content,
            tokens_input=response.usage.prompt_tokens,
            tokens_output=response.usage.completion_tokens,
            latency_ms=latency,
            model=self.model,
            finish_reason=response.choices[0].finish_reason
        )
```

---

### Story 3.3: Cerebras Provider Implementation

**As a** orquestrador,  
**I want** wrapper para Cerebras API,  
**So that** posso usar Cerebras como agente Worker (60 RPM).

**Acceptance Criteria:**

**Given** Cerebras API key configurado  
**When** chamo Cerebras provider  
**Then** deve:
- ✅ Use aiohttp (REST API)
- ✅ Endpoint: `https://api.cerebras.ai/v1/chat/completions`
- ✅ Model: `llama-3-8b`
- ✅ Return LLMResponse
- ✅ Handle Beta instability (timeouts, errors)

**And** teste valida call funciona

**Prerequisites:** Story 3.1

**Technical Notes:**
```python
# src/providers/cerebras_provider.py
import aiohttp

class CerebrasProvider(LLMProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = "https://api.cerebras.ai/v1"
    
    async def call(self, system_prompt, user_prompt, max_tokens=2000, temperature=0.7):
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            headers = {"Authorization": f"Bearer {self.config.api_key}"}
            
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            ) as resp:
                if resp.status == 429:
                    raise RateLimitError(await resp.json())
                
                data = await resp.json()
                return self.parse_response(data)
```

---

### Story 3.4: Gemini Provider Implementation (SDK)

**As a** orquestrador,  
**I want** wrapper para Google Gemini usando SDK oficial,  
**So that** posso usar Gemini Pro como agente Boss-Ultimate.

**Acceptance Criteria:**

**Given** Gemini API key configurado (env var)  
**When** chamo Gemini provider  
**Then** deve:
- ✅ Use `google-genai` SDK (NOT REST)
- ✅ Auto-detecta `GEMINI_API_KEY`
- ✅ Suporte models: `gemini-2.5-flash`, `gemini-2.5-pro`
- ✅ Return LLMResponse
- ✅ Handle Retry-After headers

**And** teste valida SDK integration

**Prerequisites:** Story 3.1

**Technical Notes:**
```python
# src/providers/gemini_provider.py
from google import genai

class GeminiProvider(LLMProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.client = genai.Client()  # Auto-detect API key
    
    async def call(self, system_prompt, user_prompt, max_tokens=2000, temperature=0.7):
        # Gemini combina system + user em single prompt
        combined_prompt = f"{system_prompt}\n\nUser: {user_prompt}"
        
        response = self.client.models.generate_content(
            model=self.model,  # gemini-2.5-flash ou gemini-2.5-pro
            contents=combined_prompt,
            config=genai.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            )
        )
        
        return LLMResponse(
            content=response.text,
            tokens_input=response.usage_metadata.prompt_token_count,
            tokens_output=response.usage_metadata.candidates_token_count,
            latency_ms=latency,
            model=self.model,
            finish_reason=response.candidates[0].finish_reason
        )
```

**Rationale:** ADR-002 escolheu SDK oficial vs REST

---

### Story 3.5: OpenRouter Provider Implementation

**As a** orquestrador,  
**I want** wrapper para OpenRouter free tier,  
**So that** tenho diversidade de providers (12 RPM adicional).

**Acceptance Criteria:**

**Given** OpenRouter API key configurado  
**When** chamo OpenRouter provider  
**Then** deve:
- ✅ Use aiohttp (REST API)
- ✅ Endpoint: `https://openrouter.ai/api/v1/chat/completions`
- ✅ Model: `google/gemma-2b-it:free` ou similar
- ✅ Handle free-tier restrictions
- ✅ Return LLMResponse

**Prerequisites:** Story 3.1

**Technical Notes:**
```python
# src/providers/openrouter_provider.py
class OpenRouterProvider(LLMProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = "https://openrouter.ai/api/v1"
    
    async def call(self, system_prompt, user_prompt, max_tokens=2000, temperature=0.7):
        # Similar to Cerebras (OpenAI-compatible API)
        ...
```

---

### Story 3.6: Together AI Provider Implementation (Optional)

**As a** orquestrador,  
**I want** wrapper para Together AI (tier 1),  
**So that** tenho 60 RPM adicional se $5 investment for aprovado.

**Acceptance Criteria:**

**Given** Together AI API key + $5 payment  
**When** chamo Together provider  
**Then** deve:
- ✅ REST API client
- ✅ Model: `mistralai/Mixtral-8x7B-Instruct-v0.1`
- ✅ Rate limit: 60 RPM
- ✅ Return LLMResponse

**And** only included if `TOGETHER_API_KEY` presente

**Prerequisites:** Story 3.1

**Technical Notes:**
- Conditional dependency: Only if $5 investment
- Otherwise skip (4 providers sufficient para MVP)

---

### Story 3.7: Provider Factory & Registry

**As a** desenvolvedor,  
**I want** factory para criar providers dinamicamente,  
**So that** posso adicionar novos providers sem mudar código.

**Acceptance Criteria:**

**Given** provider configs em YAML  
**When** sistema inicia  
**Then** deve:
- ✅ Load `config/providers.yaml`
- ✅ Create provider instances: Groq, Cerebras, Gemini, OpenRouter
- ✅ Register em registry: `providers['groq']` → GroqProvider instance
- ✅ Validate: API keys presentes

**And** adicionar novo provider = apenas editar YAML + criar class

**Prerequisites:** Stories 3.2, 3.3, 3.4, 3.5

**Technical Notes:**
```python
# src/providers/factory.py
class ProviderFactory:
    PROVIDER_CLASSES = {
        'groq': GroqProvider,
        'cerebras': CerebrasProvider,
        'gemini': GeminiProvider,
        'openrouter': OpenRouterProvider,
        'together': TogetherProvider,
    }
    
    def create_all(self, config_path: str) -> Dict[str, LLMProvider]:
        config = yaml.safe_load(open(config_path))
        providers = {}
        
        for name, cfg in config['providers'].items():
            provider_class = self.PROVIDER_CLASSES[cfg['type']]
            providers[name] = provider_class(cfg)
        
        return providers
```

---

### Story 3.8: Stub Provider for Testing

**As a** developer,  
**I want** stub LLM providers for unit tests,  
**So that** I can test agent orchestration without real API keys or network calls.

**Acceptance Criteria:**

**Given** I'm writing unit tests for agent orchestration  
**When** I use `StubLLMProvider`  
**Then** deve:
- ✅ Implement full `LLMProvider` interface
- ✅ Return configurable fixed responses
- ✅ Track call count and call history
- ✅ Simulate realistic latency (~50-100ms)
- ✅ Work offline (no network)
- ✅ Be deterministic (same input → same output)

**And** CI/CD pipelines não precisam de API keys reais

**Given** I run pytest  
**When** tests use StubLLMProvider  
**Then** deve:
- ✅ Execute fast (<100ms per test)
- ✅ Allow inspection: `stub.call_count`, `stub.call_history`
- ✅ Support reset between tests: `stub.reset()`

**Prerequisites:** Story 3.1 (LLMProvider interface)

**Technical Notes:**

```python
# tests/stubs/stub_provider.py
from src.providers.base import LLMProvider, LLMResponse
from typing import Optional, List, Dict
import asyncio

class StubLLMProvider(LLMProvider):
    """Fake provider for unit tests - no real API calls"""
    
    def __init__(self, fixed_response: Optional[str] = None):
        self.fixed_response = fixed_response or '{"status": "success", "result": "stub response"}'
        self.call_count = 0
        self.call_history: List[Dict] = []
    
    async def call(self, messages: List[Dict], tools: Optional[List] = None) -> LLMResponse:
        """Simulate LLM call with fixed response"""
        self.call_count += 1
        self.call_history.append({
            "messages": messages,
            "tools": tools,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Simulate realistic latency
        await asyncio.sleep(0.05)  # 50ms
        
        return LLMResponse(
            content=self.fixed_response,
            provider="stub",
            model="test-model-v1",
            tokens_input=len(str(messages)),
            tokens_output=len(self.fixed_response),
            latency_ms=50
        )
    
    def reset(self):
        """Reset state between tests"""
        self.call_count = 0
        self.call_history = []
    
    async def health_check(self) -> bool:
        """Always healthy for tests"""
        return True

# Usage example in tests:
import pytest
from tests.stubs.stub_provider import StubLLMProvider
from src.agents.orchestrator import AgentOrchestrator

@pytest.mark.asyncio
async def test_agent_execution():
    # Arrange
    stub = StubLLMProvider(
        fixed_response='{"findings": ["test finding"], "confidence": 0.9}'
    )
    orchestrator = AgentOrchestrator(provider=stub)
    
    # Act
    result = await orchestrator.execute(
        agent="analyst",
        task="Analyze system"
    )
    
    # Assert
    assert stub.call_count == 1
    assert "analyst" in str(stub.call_history[0]["messages"])
    assert result.content is not None
    
    # Cleanup
    stub.reset()
```

**Benefits:**
- ✅ Fast unit tests (no network I/O)
- ✅ Deterministic (no API randomness)
- ✅ Offline development (no internet required)
- ✅ CI/CD friendly (no secrets needed)
- ✅ Cost-free (no API quota consumed)
- ✅ Inspectable (verify prompt construction)

**Test Coverage:**
- Unit tests for `AgentOrchestrator`
- Unit tests for `PromptBuilder`
- Unit tests for `ToolExecutor`
- Unit tests for fallback logic (mock 429 errors)

**Estimated Effort:** 2 hours

---

**Epic 3 Complete!** 🎉  
**Value Delivered:** 4-5 providers funcionais + stub para testes, throughput 99 RPM agregado

---

## Epic 4: Fallback & Resilience

**Goal:** Fallback automático e auto-throttling adaptativo  
**Timeline:** Semana 5  
**Value:** 99.5%+ SLA - Mary sempre disponível  
**Dependencies:** Epic 3 (múltiplos providers)

---

### Story 4.1: Fallback Chain Executor

**As a** orquestrador,  
**I want** executar fallback chain automaticamente,  
**So that** se Groq falha, Mary migra para Cerebras automaticamente.

**Acceptance Criteria:**

**Given** agent chains configurado (analyst: [cerebras, groq])  
**When** cerebras retorna 429 rate limit error  
**Then** sistema deve:
- ✅ Catch RateLimitError
- ✅ Log: "Cerebras rate limited, trying fallback: groq"
- ✅ Retry com groq/llama-3-70b
- ✅ Return response de groq
- ✅ Fallback completo em <5s

**And** se groq também falha → raise AllProvidersFailed

**Prerequisites:** Stories 1.6 (router), 3.7 (factory)

**Technical Notes:**
```python
# src/agents/fallback.py
class FallbackExecutor:
    async def execute_with_fallback(
        self,
        agent_id: str,
        system_prompt: str,
        user_prompt: str
    ) -> LLMResponse:
        chain = self.router.get_fallback_chain(agent_id)
        
        for idx, provider_config in enumerate(chain):
            provider = self.providers[provider_config.name]
            
            try:
                response = await provider.call(system_prompt, user_prompt)
                
                if idx > 0:
                    logger.info(f"✅ Fallback success: {provider.name}")
                
                return response
                
            except RateLimitError:
                if idx < len(chain) - 1:
                    logger.warning(
                        f"⚠️ {provider.name} rate limited, "
                        f"trying fallback {idx+1}/{len(chain)-1}"
                    )
                    continue
                else:
                    raise AllProvidersFailed(agent_id)
```

---

### Story 4.2: Quality Validation & Auto-Escalation

**As a** orquestrador,  
**I want** validar qualidade de response e escalar se baixa,  
**So that** worker ruim escalates para boss automaticamente.

**Acceptance Criteria:**

**Given** response de worker (cerebras/llama-3-8b)  
**When** valido qualidade  
**Then** deve:
- ✅ Check length: >50 chars (não vazio)
- ✅ Check format: válido (não corrupted)
- ✅ Check confidence: parse se resposta tem "low confidence" markers
- ✅ Se quality OK: return response
- ✅ Se quality baixa: escalate para boss tier

**And** teste valida: bad response → auto-escalate

**Prerequisites:** Story 4.1

**Technical Notes:**
```python
# src/agents/quality.py
class QualityValidator:
    def validate(self, response: str, tier: str) -> bool:
        # Basic validation
        if len(response) < 50:
            return False
        
        # Check for error markers
        error_markers = [
            "I cannot", "I don't know", "Unable to",
            "[ERROR]", "Failed to"
        ]
        if any(marker in response for marker in error_markers):
            return False
        
        # Tier-specific validation
        if tier == "worker":
            # Workers: apenas basic check
            return True
        elif tier == "boss":
            # Bosses: expect deeper response
            return len(response) > 200
        
        return True
```

---

### Story 4.3: Auto-Throttling - Spike Detection

**As a** sistema,  
**I want** detectar spikes de 429 errors,  
**So that** posso auto-throttle antes de escalar.

**Acceptance Criteria:**

**Given** requests sendo feitos  
**When** >3 429 errors ocorrem em 1 minuto para mesmo provider  
**Then** deve:
- ✅ Detect spike: count(429s in last 60s) > 3
- ✅ Trigger throttling
- ✅ Log: "⚠️ Spike detected: Groq 5x 429 em 60s, throttling"
- ✅ Metrics: `llm_throttle_events{provider}` counter +1

**And** spike_counter tracked em Redis

**Prerequisites:** Story 2.8 (metrics)

**Technical Notes:**
```python
# src/rate_limit/throttle.py
class SpikeDetector:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def record_429(self, provider: str):
        key = f"spike:{provider}"
        now = time.time()
        
        # Add 429 timestamp
        await self.redis.zadd(key, {str(uuid.uuid4()): now})
        
        # Cleanup old (>60s)
        cutoff = now - 60
        await self.redis.zremrangebyscore(key, 0, cutoff)
        
        # Count 429s in last 60s
        count = await self.redis.zcount(key, cutoff, now)
        
        # Spike if >3 in 60s
        return count > 3
```

---

### Story 4.4: Auto-Throttling - RPM Reduction

**As a** sistema,  
**I want** reduzir RPM em 20% quando spike detectado,  
**So that** sistema se auto-ajusta e previne escalação.

**Acceptance Criteria:**

**Given** spike detected (>3 429s em 60s)  
**When** throttling acionado  
**Then** deve:
- ✅ Current RPM: Groq 12 RPM
- ✅ Reduce 20%: 12 * 0.8 = 9.6 → 9 RPM
- ✅ Min floor: Nunca abaixo de 50% (12 * 0.5 = 6 RPM)
- ✅ Update token bucket rate: 9/60 = 0.15 tokens/sec
- ✅ Log: "Auto-throttle: Groq 12 → 9 RPM"
- ✅ Slack alert: "Auto-throttling ativado: Groq"

**And** restore após 10 min se stable (0 429s)

**Prerequisites:** Story 4.3

**Technical Notes:**
```python
# src/rate_limit/throttle.py
class AdaptiveThrottler:
    def __init__(self, redis_client, rate_limiter):
        self.redis = redis_client
        self.rate_limiter = rate_limiter
        self.base_rpms = {}  # Store original RPMs
    
    async def throttle(self, provider: str, reduction: float = 0.20):
        current_rpm = self.rate_limiter.get_rpm(provider)
        base_rpm = self.base_rpms.get(provider, current_rpm)
        
        new_rpm = int(current_rpm * (1 - reduction))
        min_rpm = int(base_rpm * 0.5)  # Never below 50%
        
        new_rpm = max(new_rpm, min_rpm)
        
        logger.warning(f"Auto-throttle: {provider} {current_rpm} → {new_rpm} RPM")
        
        await self.rate_limiter.update_rpm(provider, new_rpm)
        
        # Schedule restore check in 10 min
        await self.schedule_restore_check(provider, base_rpm)
```

---

### Story 4.5: Auto-Throttling - Restore Logic

**As a** sistema,  
**I want** restaurar RPM original se estável,  
**So that** não fico throttled permanentemente.

**Acceptance Criteria:**

**Given** provider throttled (Groq 12 → 9 RPM)  
**When** 10 minutos passam sem 429 errors  
**Then** deve:
- ✅ Check: 0 429s em last 10 min
- ✅ If stable: Restore RPM original (9 → 12)
- ✅ Log: "Auto-restore: Groq 9 → 12 RPM (stable)"
- ✅ Slack notification: "Groq restored to normal"

**And** se novo spike: não restore

**Prerequisites:** Story 4.4

**Technical Notes:**
- Scheduled task (asyncio.create_task)
- Check stability before restore
- Gradual restore (não immediate full)

---

### Story 4.6: Integration Test - Fallback Scenario

**As a** desenvolvedor,  
**I want** teste que simula fallback completo,  
**So that** sei que Mary migra de Cerebras → Groq corretamente.

**Acceptance Criteria:**

**Given** Cerebras mock retorna 429  
**When** executo agent request (analyst)  
**Then** deve:
- ✅ Try cerebras first → 429 error
- ✅ Fallback to groq automatically
- ✅ Groq succeeds
- ✅ Response returned em <5s
- ✅ Metrics: `llm_fallback_total{agent=analyst}` +1

**And** logs mostram fallback sequence

**Prerequisites:** Stories 4.1, 4.2

**Technical Notes:**
- Mock providers para simular failures
- Validate timing (<5s)
- Check metrics increment

**Epic 4 Complete!** 🎉  
**Value Delivered:** Resiliência completa - 99.5%+ SLA alcançado

---

## Epic 5: Observability Foundation

**Goal:** Prometheus metrics completo e structured logging  
**Timeline:** Semana 5 (paralelo com Epic 4)  
**Value:** Visibilidade - "o que está acontecendo?"  
**Dependencies:** Epic 0 (Prometheus)

---

### Story 5.1: Prometheus Metrics - Request Tracking

**As a** operador,  
**I want** métricas completas de requests,  
**So that** posso monitorar throughput e success rate.

**Acceptance Criteria:**

**Given** Prometheus configurado  
**When** requests sendo executados  
**Then** deve expor:
- ✅ `llm_requests_total{provider, agent, status}` - Total requests
- ✅ `llm_requests_success{provider, agent}` - Successful requests
- ✅ `llm_requests_failure{provider, agent, error_type}` - Failed requests
- ✅ `llm_requests_429_total{provider}` - Rate limit errors

**And** `/metrics` expõe em Prometheus format

**Prerequisites:** Story 0.5

**Technical Notes:**
```python
# src/metrics/requests.py
from prometheus_client import Counter

requests_total = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['provider', 'agent', 'status']
)

# Usage
requests_total.labels(
    provider='groq',
    agent='analyst',
    status='success'
).inc()
```

---

### Story 5.2: Prometheus Metrics - Latency Tracking

**As a** operador,  
**I want** métricas de latência por provider e agent,  
**So that** posso identificar performance issues.

**Acceptance Criteria:**

**Given** requests executando  
**When** coleto latency  
**Then** deve expor:
- ✅ `llm_request_duration_seconds{provider, agent}` - Histogram
- ✅ Buckets: 0.5s, 1s, 2s, 5s, 10s, 30s
- ✅ Permite calcular: P50, P95, P99

**And** query `histogram_quantile(0.95, llm_request_duration_seconds{provider="groq"})` retorna P95

**Prerequisites:** Story 5.1

**Technical Notes:**
```python
# src/metrics/latency.py
from prometheus_client import Histogram

request_duration = Histogram(
    'llm_request_duration_seconds',
    'Request latency in seconds',
    ['provider', 'agent'],
    buckets=(0.5, 1, 2, 5, 10, 30)
)

# Usage
with request_duration.labels(provider='groq', agent='analyst').time():
    response = await provider.call(...)
```

---

### Story 5.3: Prometheus Metrics - Token Consumption

**As a** operador,  
**I want** track tokens consumidos,  
**So that** posso monitorar custo e quota usage.

**Acceptance Criteria:**

**Given** LLM calls retornando token counts  
**When** processo response  
**Then** deve expor:
- ✅ `llm_tokens_consumed{provider, type}` - Histogram (type: input/output)
- ✅ `llm_tokens_total{provider}` - Counter total
- ✅ Permite calcular: tokens/day, tokens/hour

**And** dashboard mostra quota usage (% of free-tier)

**Prerequisites:** Story 5.1

**Technical Notes:**
```python
# src/metrics/tokens.py
tokens_consumed = Histogram(
    'llm_tokens_consumed',
    'Tokens consumed per request',
    ['provider', 'type'],  # input or output
    buckets=(100, 500, 1000, 2000, 5000, 10000)
)

# Usage
tokens_consumed.labels(provider='groq', type='input').observe(2500)
tokens_consumed.labels(provider='groq', type='output').observe(1200)
```

---

### Story 5.4: Structured JSON Logging

**As a** desenvolvedor/operador,  
**I want** logs estruturados em formato JSON,  
**So that** posso facilmente parse e analyze logs.

**Acceptance Criteria:**

**Given** agent execution  
**When** logs são gerados  
**Then** deve:
- ✅ Format: JSON (one object per line)
- ✅ Fields: timestamp, level, message, request_id, agent, provider, status, latency_ms, tokens_in, tokens_out
- ✅ Levels: DEBUG, INFO, WARN, ERROR
- ✅ Rotation: Daily, keep 30 days
- ✅ File: `./logs/squad-api.{date}.log`

**And** easy to grep: `cat logs/*.log | jq '.[] | select(.status=="error")'`

**Prerequisites:** None

**Technical Notes:**
```python
# src/utils/logging.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        
        # Add extra fields
        for key in ['request_id', 'agent', 'provider', 'status', 'latency_ms']:
            if hasattr(record, key):
                log_data[key] = getattr(record, key)
        
        return json.dumps(log_data)
```

---

### Story 5.5: Metrics Integration - Agent Orchestrator

**As a** orquestrador,  
**I want** metrics integradas em agent execution,  
**So that** todo request é tracked automaticamente.

**Acceptance Criteria:**

**Given** agent execution request  
**When** sistema executa  
**Then** deve:
- ✅ Increment: `llm_requests_total`
- ✅ Observe: `llm_request_duration_seconds`
- ✅ Observe: `llm_tokens_consumed` (input + output)
- ✅ If 429: Increment `llm_requests_429_total`
- ✅ If error: Increment `llm_requests_failure`

**And** metrics visíveis em Prometheus UI

**Prerequisites:** Stories 5.1, 5.2, 5.3

**Technical Notes:**
- Wrapper em orchestrator.execute()
- Try/except/finally para garantir metrics sempre registered

**Epic 5 Complete!** 🎉  
**Value Delivered:** Observabilidade foundation - métricas completas

---

## Epic 6: Monitoring Dashboards & Alerts

**Goal:** Grafana dashboards e Slack alerts  
**Timeline:** Semana 6  
**Value:** Observabilidade visual - vejo squad trabalhando  
**Dependencies:** Epic 5 (Prometheus metrics)

---

### Story 6.1: Grafana Dashboard - Request Success Rate

**As a** operador,  
**I want** dashboard de success rate,  
**So that** vejo se sistema está healthy num relance.

**Acceptance Criteria:**

**Given** metrics sendo coletadas  
**When** abro Grafana dashboard "Request Success Rate"  
**Then** deve mostrar:
- ✅ Panel 1: Success rate global (last 5min)
- ✅ Panel 2: Success rate por provider (Groq, Cerebras, Gemini)
- ✅ Panel 3: Success rate por agent (analyst, pm, architect)
- ✅ Panel 4: 429 errors timeline (last 1 hour)

**And** auto-refresh a cada 15s

**Prerequisites:** Story 5.1

**Technical Notes:**
```json
{
  "title": "Request Success Rate",
  "panels": [
    {
      "targets": [
        "rate(llm_requests_total{status='success'}[5m]) / rate(llm_requests_total[5m]) * 100"
      ],
      "title": "Success Rate % (5min)"
    }
  ]
}
```

---

### Story 6.2: Grafana Dashboard - Rate Limiting Health

**As a** operador,  
**I want** dashboard de rate limiting health,  
**So that** vejo token buckets e window occupancy em real-time.

**Acceptance Criteria:**

**Given** rate limiting funcionando  
**When** abro dashboard "Rate Limiting Health"  
**Then** deve mostrar:
- ✅ Token bucket status por provider (gauge)
- ✅ Window occupancy (requests em last 60s)
- ✅ RPM current vs RPM limit
- ✅ 429 errors count (last hour)

**And** red/yellow/green thresholds

**Prerequisites:** Story 5.1

---

### Story 6.3: Grafana Dashboard - Performance Metrics

**As a** operador,  
**I want** dashboard de performance,  
**So that** vejo latências e identify bottlenecks.

**Acceptance Criteria:**

**Given** latency metrics coletadas  
**When** abro dashboard "Performance"  
**Then** deve mostrar:
- ✅ Latency P50/P95/P99 por provider
- ✅ Latency por agent
- ✅ Latency timeline (last 1 hour)
- ✅ Target lines: 2s (potentes), 5s (pequenos)

**And** violations highlighted (red)

**Prerequisites:** Story 5.2

---

### Story 6.4: Grafana Dashboard - Cost & Quota Tracking

**As a** operador,  
**I want** dashboard de custo e quota,  
**So that** não estouro free-tier limits.

**Acceptance Criteria:**

**Given** tokens being tracked  
**When** abro dashboard "Cost Tracking"  
**Then** deve mostrar:
- ✅ Tokens consumed today (por provider)
- ✅ % of free-tier quota used
- ✅ Projected tokens end-of-day
- ✅ Alert if >80% quota

**Prerequisites:** Story 5.3

---

### Story 6.5: Slack Alerts - 429 Spike Alert

**As a** operador,  
**I want** alertas Slack para spikes de 429,  
**So that** sou notificado quando auto-throttling ativa.

**Acceptance Criteria:**

**Given** Slack webhook configurado  
**When** spike de 429s detectado (>5/min)  
**Then** deve:
- ✅ Send Slack message:
  ```
  ⚠️ Auto-Throttling Ativado
  Provider: Groq
  429 Errors: 7 em último minuto
  Action: RPM reduzido de 12 → 9
  Time: 2025-11-12 10:30:45
  ```
- ✅ Channel: #squad-api-alerts
- ✅ Throttle alerts: Max 1 por 5 min (evita spam)

**Prerequisites:** Story 4.4

**Technical Notes:**
```python
# src/alerts/slack.py
async def send_alert(webhook_url: str, message: str):
    async with aiohttp.ClientSession() as session:
        await session.post(webhook_url, json={"text": message})
```

---

### Story 6.6: Slack Alerts - Latency & Health Alerts

**As a** operador,  
**I want** alertas para latência alta e providers unhealthy,  
**So that** posso investigar problemas proativamente.

**Acceptance Criteria:**

**Given** Slack configurado  
**When** latency avg > 2s (potentes) ou provider unhealthy  
**Then** deve:
- ✅ Alert: "Groq latency 3.5s (target: <2s)"
- ✅ Alert: "Cerebras unreachable, fallback ativo"
- ✅ Throttling: Max 1 alert same type por 15 min

**Prerequisites:** Story 6.5

**Epic 6 Complete!** 🎉  
**Value Delivered:** Dashboards e alerts - visibilidade completa

---

## Epic 7: Configuration System

**Goal:** Config-driven, reproduzível, YAML-based  
**Timeline:** Semana 6 (paralelo com Epic 6)  
**Value:** Reutilizável - ajustar sem código  
**Dependencies:** Epics 1-4

---

### Story 7.1: YAML Config Loader

**As a** desenvolvedor,  
**I want** loader centralizado para YAML configs,  
**So that** todos configs carregados consistentemente.

**Acceptance Criteria:**

**Given** config files em `./config/`  
**When** sistema inicia  
**Then** deve:
- ✅ Load `rate_limits.yaml`
- ✅ Load `agent_chains.yaml`
- ✅ Load `providers.yaml`
- ✅ Validate: Pydantic models
- ✅ Error se config inválido: clear message

**And** hot-reload se config muda (watchdog)

**Prerequisites:** None

**Technical Notes:**
```python
# src/config/loader.py
class ConfigLoader:
    def __init__(self, config_dir: str = "./config"):
        self.config_dir = Path(config_dir)
    
    def load_rate_limits(self) -> RateLimitsConfig:
        path = self.config_dir / "rate_limits.yaml"
        data = yaml.safe_load(open(path))
        return RateLimitsConfig(**data)
```

---

### Story 7.2: Environment Variables Validation

**As a** desenvolvedor,  
**I want** validation de environment variables na startup,  
**So that** erro rápido se API keys faltando.

**Acceptance Criteria:**

**Given** `.env` file (ou env vars)  
**When** Squad API inicia  
**Then** deve:
- ✅ Load via `python-dotenv`
- ✅ Check required: `GROQ_API_KEY`, `CEREBRAS_API_KEY`, `GEMINI_API_KEY`
- ✅ Check optional: `SLACK_WEBHOOK_URL`, `TOGETHER_API_KEY`
- ✅ If missing required: Raise error com clear message
- ✅ Log: "Loaded X API keys"

**And** `.env.example` template existe

**Prerequisites:** None

**Technical Notes:**
```python
# src/config/env.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    groq_api_key: str
    cerebras_api_key: str
    gemini_api_key: str
    openrouter_api_key: str
    slack_webhook_url: Optional[str] = None
    
    class Config:
        env_file = '.env'
        case_sensitive = False

# Usage
settings = Settings()  # Raises validation error se missing
```

---

### Story 7.3: Config Validation on Startup

**As a** desenvolvedor,  
**I want** validação completa de configs na startup,  
**So that** erro rápido se configs inválidos.

**Acceptance Criteria:**

**Given** configs loaded  
**When** Squad API inicia  
**Then** deve validar:
- ✅ Rate limits: RPM > 0, burst > 0
- ✅ Agent chains: Todos agents tem ≥1 provider
- ✅ Providers: API keys exist, models valid
- ✅ Cross-validation: Providers em chains existem em providers.yaml

**And** validation errors são descriptive

**Prerequisites:** Stories 7.1, 7.2

---

### Story 7.4: Config Documentation

**As a** usuário (Dani),  
**I want** documentação completa de configs,  
**So that** sei como configurar Squad API.

**Acceptance Criteria:**

**Given** config files examples  
**When** leio documentação  
**Then** deve incluir:
- ✅ `docs/configuration.md` - Guide completo
- ✅ Each config file: commented examples
- ✅ What each field does
- ✅ Valid values e ranges
- ✅ Como adicionar novo provider
- ✅ Como ajustar rate limits

**Prerequisites:** Stories 7.1, 7.2, 7.3

---

### Story 7.5: Config Change Monitoring

**As a** desenvolvedor,  
**I want** monitorar mudanças em config files,  
**So that** posso hot-reload sem restart.

**Acceptance Criteria:**

**Given** Squad API rodando  
**When** edito `config/agent_chains.yaml`  
**Then** deve:
- ✅ Detect change (watchdog)
- ✅ Reload config
- ✅ Validate new config
- ✅ If valid: Apply changes
- ✅ If invalid: Log error, keep old config
- ✅ Log: "Config reloaded: agent_chains.yaml"

**And** no restart necessário

**Prerequisites:** Story 7.1

**Epic 7 Complete!** 🎉  
**Value Delivered:** Sistema config-driven - ajustar sem código

---

## Epic 8: Deployment & Documentation

**Goal:** Docker Compose completo e docs profissionais  
**Timeline:** Semana 7  
**Value:** Reproduzível em 1 comando - `docker-compose up`  
**Dependencies:** Epics 0-7 (todos componentes)

---

### Story 8.1: Docker Compose - Complete Stack

**As a** desenvolvedor,  
**I want** Docker Compose completo com todos services,  
**So that** `docker-compose up` sobe sistema inteiro.

**Acceptance Criteria:**

**Given** todos componentes implementados  
**When** executo `docker-compose up`  
**Then** deve:
- ✅ Redis: healthy em 6379
- ✅ PostgreSQL: healthy em 5432
- ✅ Prometheus: scraping em 9090
- ✅ Grafana: acessível em 3000
- ✅ Squad API: rodando em 8000
- ✅ All healthchecks: passing
- ✅ Logs: Structured JSON output

**And** `docker-compose ps` mostra tudo "Up (healthy)"

**Prerequisites:** Stories 0.3-0.8 (consolidação)

**Technical Notes:**
- Dockerfile otimizado (multi-stage build)
- .dockerignore (exclui venv, __pycache__)
- networks: squad-network (internal)

---

### Story 8.2: README - Quick Start Guide

**As a** usuário novo,  
**I want** README que me deixa rodando em 5 minutos,  
**So that** posso testar Squad API rapidamente.

**Acceptance Criteria:**

**Given** repositório clonado  
**When** sigo README  
**Then** deve ter:
- ✅ Section: Quick Start (5 min)
  ```bash
  # 1. Clone
  git clone https://github.com/dani/squad-api
  cd squad-api
  
  # 2. Configure
  cp .env.example .env
  # Edit .env com suas API keys
  
  # 3. Run
  docker-compose up
  
  # 4. Test
  curl http://localhost:8000/health
  ```
- ✅ Section: Architecture Overview (diagram)
- ✅ Section: Configuration Guide
- ✅ Section: API Usage Examples

**And** someone following README pode rodar Squad API em 5 min

**Prerequisites:** Story 8.1

---

### Story 8.3: Runbook - Deployment Guide

**As a** operador,  
**I want** runbook de deployment,  
**So that** sei como deployar Squad API em produção.

**Acceptance Criteria:**

**Given** Squad API pronto para deploy  
**When** leio `docs/runbooks/deploy.md`  
**Then** deve incluir:
- ✅ Prerequisites (Docker, Docker Compose, API keys)
- ✅ Step-by-step deployment
- ✅ Configuration checklist
- ✅ Health check validation
- ✅ Rollback procedure
- ✅ Common deployment issues

**Prerequisites:** Story 8.1

---

### Story 8.4: Runbook - Troubleshooting Guide

**As a** operador,  
**I want** runbook de troubleshooting,  
**So that** posso resolver issues comuns rapidamente.

**Acceptance Criteria:**

**Given** problema ocorrendo  
**When** consulto `docs/runbooks/troubleshoot.md`  
**Then** deve incluir:
- ✅ Issue: "429 errors frequentes"
  - Diagnose: Check token buckets, window occupancy
  - Solution: Adjust rate limits, enable auto-throttling
- ✅ Issue: "Latência alta"
  - Diagnose: Check Grafana latency dashboard
  - Solution: Check provider health, try fallback
- ✅ Issue: "Redis connection failed"
  - Diagnose: `docker-compose ps redis`
  - Solution: Restart Redis, check network
- ✅ Issue: "Agent not found"
  - Diagnose: Check `.bmad/bmm/agents/` directory
  - Solution: Verify agent files exist, check cache

**Prerequisites:** Stories 8.1, 8.2

---

### Story 8.5: ADRs - Architecture Decision Records

**As a** desenvolvedor futuro,  
**I want** ADRs documentando decisões críticas,  
**So that** entendo "por quê" das escolhas arquiteturais.

**Acceptance Criteria:**

**Given** decisões técnicas feitas  
**When** leio `docs/adrs/`  
**Then** deve ter:
- ✅ `ADR-001-rate-limiting-strategy.md`
  - Decision: pyrate-limiter + Redis (Token Bucket + Sliding Window)
  - Context: Testes mostraram 80% falhas com burst
  - Rationale: Shared state, survives restarts
  
- ✅ `ADR-002-gemini-sdk-vs-rest.md`
  - Decision: Use google-genai SDK oficial
  - Rationale: Código limpo, type safety, mantido por Google
  
- ✅ `ADR-003-worker-boss-hierarchy.md`
  - Decision: Hybrid Worker/Boss + Fallback chains
  - Rationale: Otimiza throughput (Cerebras 60 RPM > Groq 12 RPM)

**Prerequisites:** Technical Research (já existe)

**Technical Notes:**
- ADR format: Status, Context, Decision, Consequences
- Link para Technical Research Report

---

### Story 8.6: API Documentation - OpenAPI/Swagger

**As a** desenvolvedor cliente,  
**I want** documentação completa de API endpoints,  
**So that** sei como usar Squad API.

**Acceptance Criteria:**

**Given** FastAPI rodando  
**When** acesso `/docs` (Swagger UI)  
**Then** deve documentar:
- ✅ `POST /api/v1/agent/execute` - Execute agent
  - Request schema: AgentExecutionRequest
  - Response schema: AgentExecutionResponse
  - Examples: "Pedir Mary para analisar sistema"
  
- ✅ `GET /api/v1/agents/available` - List agents
- ✅ `GET /api/v1/providers/status` - Provider health
- ✅ `GET /health` - System health

**And** Swagger UI permite "Try it out" (interactive)

**Prerequisites:** Stories 1.7, 1.8

**Technical Notes:**
- FastAPI auto-generates OpenAPI
- Add examples e descriptions em Pydantic models

---

### Story 8.7: End-to-End Integration Test

**As a** desenvolvedor,  
**I want** teste E2E que valida sistema completo,  
**So that** sei que tudo funciona together.

**Acceptance Criteria:**

**Given** Docker Compose up (todos services)  
**When** executo E2E test  
**Then** deve:
- ✅ Test 1: List agents → retorna 8 agents
- ✅ Test 2: Execute analyst → Mary responde (via Cerebras)
- ✅ Test 3: Simulate 429 → Fallback funciona (Groq)
- ✅ Test 4: Check metrics → Prometheus tem dados
- ✅ Test 5: Check Grafana → Dashboards renderizam
- ✅ Test 6: Provider status → Mostra healthy

**And** teste passa em CI (future)

**Prerequisites:** All stories Epic 0-7

**Technical Notes:**
```python
# tests/e2e/test_full_system.py
async def test_full_agent_execution():
    # List agents
    agents = await client.get("/api/v1/agents/available")
    assert agents['count'] == 8
    
    # Execute analyst
    response = await client.post("/api/v1/agent/execute", json={
        "agent": "analyst",
        "task": "Olá Mary!"
    })
    assert response['agent_name'] == "Mary"
    assert "provider" in response
```

**Epic 8 Complete!** 🎉  
**Value Delivered:** Sistema documentado e reproduzível

---

## Epic 9: Production Readiness

**Goal:** Security, audit, compliance, launch prep  
**Timeline:** Semana 8  
**Value:** Production-ready - pode deployar com confiança  
**Dependencies:** Epics 0-8 (sistema completo)

---

### Story 9.1: PII Sanitization - Detection

**As a** sistema,  
**I want** detectar PII em user prompts,  
**So that** posso warn antes de enviar para LLM APIs.

**Acceptance Criteria:**

**Given** user prompt contém PII  
**When** sistema valida input  
**Then** deve detectar:
- ✅ Emails: `regex pattern`
- ✅ Phone numbers: BR format
- ✅ CPF: XXX.XXX.XXX-XX pattern
- ✅ Credit cards: básico pattern

**And** warn: "PII detected, sanitize before sending?"

**Prerequisites:** None

**Technical Notes:**
```python
# src/security/pii.py
import re

class PIIDetector:
    PATTERNS = {
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'phone_br': r'\(\d{2}\)\s?\d{4,5}-?\d{4}',
        'cpf': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
    }
    
    def detect(self, text: str) -> List[str]:
        found = []
        for pii_type, pattern in self.PATTERNS.items():
            if re.search(pattern, text):
                found.append(pii_type)
        return found
```

---

### Story 9.2: PII Sanitization - Auto-Redact

**As a** sistema,  
**I want** auto-sanitizar PII se detectado,  
**So that** não leak dados sensíveis para LLM APIs.

**Acceptance Criteria:**

**Given** PII detected em prompt  
**When** auto-sanitize habilitado  
**Then** deve:
- ✅ Replace emails: `user@example.com` → `[EMAIL_REDACTED]`
- ✅ Replace phones: `(11) 99999-9999` → `[PHONE_REDACTED]`
- ✅ Replace CPF: `123.456.789-00` → `[CPF_REDACTED]`
- ✅ Log: "PII sanitized: email, phone"

**And** sanitized prompt enviado para LLM

**Prerequisites:** Story 9.1

---

### Story 9.3: Audit Logging - PostgreSQL Table

**As a** operador,  
**I want** audit logs em PostgreSQL,  
**So that** tenho rastreabilidade completa de ações.

**Acceptance Criteria:**

**Given** agent executions acontecendo  
**When** sistema processa  
**Then** deve:
- ✅ Table: `audit_logs`
- ✅ Columns: id, timestamp, user_id, agent, provider, action, status, latency_ms, tokens_in, tokens_out
- ✅ Index: timestamp, user_id, agent
- ✅ Retention: 90 dias (MVP)

**And** query fácil: "O que Mary fez no dia X?"

**Prerequisites:** Story 0.4

**Technical Notes:**
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id VARCHAR(100),
    agent VARCHAR(50),
    provider VARCHAR(50),
    action TEXT,
    status VARCHAR(20),
    latency_ms INTEGER,
    tokens_in INTEGER,
    tokens_out INTEGER
);

CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
```

---

### Story 9.4: Health Check Endpoint Enhancement

**As a** operador,  
**I want** health check detalhado,  
**So that** posso verificar status de todos componentes.

**Acceptance Criteria:**

**Given** Squad API rodando  
**When** chamo `GET /health`  
**Then** deve retornar:
```json
{
  "status": "healthy",
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

**And** status overall = "degraded" se qualquer component unhealthy

**Prerequisites:** Story 0.7

---

### Story 9.5: Provider Status Endpoint

**As a** usuário,  
**I want** ver status real-time de todos providers,  
**So that** sei quem está disponível antes de fazer request.

**Acceptance Criteria:**

**Given** providers rodando  
**When** chamo `GET /api/v1/providers/status`  
**Then** retorna:
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
    "cerebras": {...},
    "gemini": {...}
  },
  "aggregate": {
    "healthy": 4,
    "degraded": 0,
    "unavailable": 0,
    "total_rpm_available": 87
  }
}
```

**Prerequisites:** Stories 2.3, 3.7

---

### Story 9.6: Load Testing com Locust

**As a** desenvolvedor,  
**I want** load test que valida sistema sob carga,  
**So that** sei que 120-130 RPM é alcançável.

**Acceptance Criteria:**

**Given** Squad API rodando  
**When** executo Locust test (30 req/s distribuídos)  
**Then** deve:
- ✅ Duration: 5 minutos
- ✅ Total requests: 9000 (30 req/s * 300s)
- ✅ Success rate: >99%
- ✅ 429 errors: <1%
- ✅ Latency P95: <2s (potentes), <5s (pequenos)
- ✅ Auto-throttling triggers: <3 events
- ✅ Fallback events: documented

**And** gera report: `load-test-report-{date}.html`

**Prerequisites:** All Epics 0-7

**Technical Notes:**
```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class SquadAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)  # 60% analyst
    def execute_analyst(self):
        self.client.post("/api/v1/agent/execute", json={
            "agent": "analyst",
            "task": "Analise: teste de carga"
        })
    
    @task(2)  # 40% architect
    def execute_architect(self):
        self.client.post("/api/v1/agent/execute", json={
            "agent": "architect",
            "task": "Design: teste"
        })
```

Run: `locust -f tests/load/locustfile.py --host=http://localhost:8000 --users=30 --spawn-rate=5 --run-time=5m`

---

### Story 9.7: Security Review Checklist

**As a** desenvolvedor,  
**I want** security checklist completo,  
**So that** valido que sistema é seguro antes de deploy.

**Acceptance Criteria:**

**Given** sistema pronto para produção  
**When** executo security review  
**Then** deve validar:
- ✅ API keys: Apenas em environment variables (não hardcoded)
- ✅ .env: NOT versionado (.gitignore)
- ✅ HTTPS: All LLM API calls via HTTPS
- ✅ PII: Sanitization habilitado
- ✅ Audit logs: Funcionando
- ✅ Dependencies: No known vulnerabilities (`pip-audit`)
- ✅ Docker: Images de sources confiáveis (official)

**And** checklist em `docs/security-checklist.md`

**Prerequisites:** Stories 9.1, 9.2, 9.3

---

### Story 9.8: Production Go-Live Procedure

**As a** operador,  
**I want** procedimento de go-live,  
**So that** sei exatamente os passos para lançar em produção.

**Acceptance Criteria:**

**Given** tudo testado e pronto  
**When** leio `docs/runbooks/go-live.md`  
**Then** deve incluir:
- ✅ Pre-launch checklist:
  - Load tests passed
  - Security review complete
  - Documentation complete
  - Backup strategy validated
  - Monitoring alerts configured
  
- ✅ Launch steps:
  - Deploy to staging
  - Smoke tests em staging
  - Deploy to production
  - Monitor for 24h
  - Gradual rollout (if multi-user)
  
- ✅ Post-launch:
  - Monitor dashboards
  - Review alerts
  - Document issues
  - Celebrate! 🎉

**Prerequisites:** Stories 9.6, 9.7

**Epic 9 Complete!** 🎉  
**Value Delivered:** Production-ready - pode deployar com confiança!

---

## Epic 10: Simple Agent Status UI

**Goal:** UI humano-friendly mostrando squad trabalhando em tempo real  
**Timeline:** Semana 7 (paralelo com Epic 8)  
**Value:** "Sentir" a squad trabalhando - ver Mary, John, Alex em ação  
**Dependencies:** Epic 1 (agent execution), Epic 5 (metrics)

---

### Story 10.1: WebSocket Server para Real-Time Updates

**As a** desenvolvedor,  
**I want** WebSocket endpoint que envia agent status updates,  
**So that** UI pode mostrar status em tempo real.

**Acceptance Criteria:**

**Given** FastAPI rodando  
**When** client conecta WebSocket  
**Then** deve:
- ✅ Endpoint: `ws://localhost:8000/ws/agent-status`
- ✅ Send initial state: Todos 8 agents com status
- ✅ Send updates: Quando agent muda status (idle → active → idle)
- ✅ Update frequency: Push-based (on change), não polling
- ✅ Disconnect handling: Client reconnect automático

**And** múltiplos clients podem conectar

**Prerequisites:** Story 0.7

**Technical Notes:**
```python
# src/api/websocket.py
from fastapi import WebSocket
from typing import List

class AgentStatusWebSocket:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Send initial state
        await websocket.send_json(await self.get_agent_status())
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

# src/main.py
@app.websocket("/ws/agent-status")
async def agent_status_websocket(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except:
        ws_manager.disconnect(websocket)
```

---

### Story 10.2: Agent Status Data Model

**As a** sistema,  
**I want** modelo de dados para agent status,  
**So that** posso trackear estado de cada agente.

**Acceptance Criteria:**

**Given** agentes sendo executados  
**When** construo status object  
**Then** deve incluir:
```python
{
  "id": "analyst",
  "name": "Mary",
  "title": "Business Analyst",
  "icon": "📊",
  "status": "active",  # idle|active|degraded|failed
  "provider": "groq",
  "model": "llama-3-70b",
  "current_task": "Executing research workflow",
  "uptime": "2h 34min",
  "last_active": "2025-11-12T10:30:45Z",
  "latency_ms": 1850,
  "status_color": "green"  # gray|green|yellow|red
}
```

**And** status atualizado em real-time quando agent executa

**Prerequisites:** Story 1.7

---

### Story 10.3: Status Tracking - Idle/Active/Degraded/Failed

**As a** sistema,  
**I want** trackear status de cada agente automaticamente,  
**So that** UI mostra cores corretas.

**Acceptance Criteria:**

**Given** agentes executando  
**When** sistema atualiza status  
**Then** deve:
- ✅ **Idle (⚪ gray):** Agent não usado nos últimos 5 min
- ✅ **Active (🟢 green):** Agent executando agora, latency < target
- ✅ **Degraded (🟡 yellow):** Agent executando mas latency > target (2s potentes, 5s pequenos)
- ✅ **Failed (🔴 red):** Last execution failed (429, error, timeout)

**And** status muda automaticamente baseado em execution events

**Prerequisites:** Story 10.2

**Technical Notes:**
```python
# src/monitoring/status_tracker.py
class AgentStatusTracker:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def update_status(self, agent_id: str, event: str, metadata: dict):
        key = f"agent_status:{agent_id}"
        
        if event == "execution_start":
            status = {
                "status": "active",
                "status_color": "green",
                "current_task": metadata['task'],
                "last_active": datetime.now().isoformat()
            }
        
        elif event == "execution_success":
            latency = metadata['latency_ms']
            target = metadata['latency_target_ms']
            
            if latency > target:
                status = {"status": "degraded", "status_color": "yellow"}
            else:
                status = {"status": "active", "status_color": "green"}
        
        elif event == "execution_failure":
            status = {"status": "failed", "status_color": "red"}
        
        await self.redis.hset(key, mapping=status)
        
        # Broadcast to WebSocket clients
        await self.ws_manager.broadcast(await self.get_all_status())
```

---

### Story 10.4: Simple HTML/JS Status Board

**As a** usuário (Dani),  
**I want** página web simples mostrando squad status,  
**So that** vejo quem está trabalhando num relance.

**Acceptance Criteria:**

**Given** WebSocket rodando  
**When** abro `http://localhost:8000/status`  
**Then** deve mostrar:
```
┌──────────────────────────────────────────┐
│     Squad API - Agent Status Board       │
├──────────────────────────────────────────┤
│                                          │
│  📊 Mary (Business Analyst)              │
│      🟢 Active - Groq Llama-3-70B       │
│      Working on: Research workflow       │
│      Latency: 1.8s                      │
│                                          │
│  📋 John (Product Manager)               │
│      ⚪ Idle - Cerebras Llama-3-8B      │
│      Last used: 45 min ago              │
│                                          │
│  🏗️ Alex (Software Architect)            │
│      🟡 Degraded - Gemini 2.5 Pro       │
│      Working on: Architecture design     │
│      Latency: 4.2s (target: <2s)        │
│                                          │
│  👨‍💻 Sarah (Developer)                    │
│      🔴 Failed - OpenRouter              │
│      Error: Rate limit exceeded          │
│      Fallback: Trying Cerebras...       │
│                                          │
└──────────────────────────────────────────┘

Legend: ⚪ Idle  🟢 Active  🟡 Degraded  🔴 Failed
```

**And** updates em tempo real (sem refresh)

**Prerequisites:** Stories 10.1, 10.2, 10.3

**Technical Notes:**
```html
<!-- public/status.html -->
<!DOCTYPE html>
<html>
<head>
  <title>Squad API - Agent Status</title>
  <style>
    body { font-family: monospace; background: #1e1e1e; color: #fff; }
    .container { max-width: 800px; margin: 40px auto; padding: 20px; }
    .agent { 
      padding: 20px; 
      margin: 15px 0; 
      border-radius: 8px; 
      border-left: 5px solid;
    }
    .idle { background: #2a2a2a; border-color: #666; }
    .active { background: #1a4d2e; border-color: #4caf50; }
    .degraded { background: #4d3a1a; border-color: #ff9800; }
    .failed { background: #4d1a1a; border-color: #f44336; }
    .agent-header { font-size: 18px; font-weight: bold; margin-bottom: 10px; }
    .agent-info { font-size: 14px; opacity: 0.9; margin: 5px 0; }
  </style>
</head>
<body>
  <div class="container">
    <h1>🚀 Squad API - Agent Status Board</h1>
    <div id="agents"></div>
    <div style="margin-top: 30px; opacity: 0.7;">
      Legend: ⚪ Idle  🟢 Active  🟡 Degraded  🔴 Failed
    </div>
  </div>
  
  <script>
    const ws = new WebSocket('ws://localhost:8000/ws/agent-status');
    
    ws.onmessage = (event) => {
      const agents = JSON.parse(event.data);
      renderAgents(agents);
    };
    
    ws.onclose = () => {
      setTimeout(() => location.reload(), 3000);  // Auto-reconnect
    };
    
    function getStatusEmoji(status) {
      const map = {idle: '⚪', active: '🟢', degraded: '🟡', failed: '🔴'};
      return map[status] || '⚪';
    }
    
    function renderAgents(agents) {
      const container = document.getElementById('agents');
      container.innerHTML = agents.map(a => `
        <div class="agent ${a.status}">
          <div class="agent-header">
            ${a.icon} ${a.name} (${a.title})
          </div>
          <div class="agent-info">
            ${getStatusEmoji(a.status)} ${a.status.toUpperCase()} - ${a.provider} ${a.model}
          </div>
          ${a.current_task ? `<div class="agent-info">📝 ${a.current_task}</div>` : ''}
          ${a.latency_ms ? `<div class="agent-info">⏱️ Latency: ${a.latency_ms}ms</div>` : ''}
          ${a.last_active ? `<div class="agent-info">🕐 ${formatTime(a.last_active)}</div>` : ''}
        </div>
      `).join('');
    }
    
    function formatTime(isoString) {
      const date = new Date(isoString);
      const now = new Date();
      const diff = Math.floor((now - date) / 60000);  // minutes
      if (diff < 1) return "Just now";
      if (diff < 60) return `${diff} min ago`;
      return `${Math.floor(diff/60)}h ${diff%60}min ago`;
    }
  </script>
</body>
</html>
```

---

### Story 10.5: Status Board Static File Serving

**As a** usuário,  
**I want** acessar status board via browser,  
**So that** não preciso setup adicional.

**Acceptance Criteria:**

**Given** FastAPI rodando  
**When** acesso `http://localhost:8000/status`  
**Then** deve:
- ✅ Serve `public/status.html`
- ✅ Static files: CSS, JS (se separados)
- ✅ Auto-reload se HTML muda (dev mode)

**And** browser abre página mostrando squad status

**Prerequisites:** Story 10.4

**Technical Notes:**
```python
# src/main.py
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="public"), name="static")

@app.get("/status")
async def status_page():
    return FileResponse('public/status.html')
```

---

### Story 10.6: Agent Status Integration Test

**As a** desenvolvedor,  
**I want** teste que valida status UI funciona,  
**So that** sei que WebSocket + rendering funcionam.

**Acceptance Criteria:**

**Given** Squad API rodando  
**When** executo teste:
```python
# 1. Connect WebSocket
ws = await websocket_connect("ws://localhost:8000/ws/agent-status")

# 2. Receive initial state
initial = await ws.receive_json()
assert len(initial) == 8  # 8 agents

# 3. Execute agent (trigger status change)
await client.post("/api/v1/agent/execute", json={
    "agent": "analyst",
    "task": "test"
})

# 4. Receive update
update = await ws.receive_json()
assert update[0]['status'] == 'active'  # Mary agora active
```

**Prerequisites:** Stories 10.1, 10.3

**Epic 10 Complete!** 🎉  
**Value Delivered:** UI simples e humana - vejo squad trabalhando em tempo real!

---

## Summary: All Epics Complete (ATUALIZADO)

**Total Breakdown:**

- **Epic 0:** 8 stories (Foundation)
- **Epic 1:** 16 stories (Agent Transformation + Tools - CORE MAGIC) ← **UPDATED!**
- **Epic 2:** 8 stories (Rate Limiting)
- **Epic 3:** 7 stories (Provider Wrappers)
- **Epic 4:** 6 stories (Fallback & Resilience)
- **Epic 5:** 5 stories (Observability Foundation)
- **Epic 6:** 6 stories (Dashboards & Alerts)
- **Epic 7:** 5 stories (Configuration System)
- **Epic 8:** 7 stories (Deployment & Docs)
- **Epic 9:** 8 stories (Production Readiness)
- **Epic 10:** 6 stories (Simple Agent Status UI) ← **NOVO!**

**Grand Total:** 82 stories | 10 semanas

---

**Value Progression:**

```
Week 1 (Epic 0):
  ✅ Infraestrutura rodando

Week 2-3 (Epic 1):
  ✅ CORE MAGIC funciona - LLMs viram Mary, John, Alex

Week 3 (Epic 2):
  ✅ Rate limiting - 429 errors <1%

Week 4 (Epic 3):
  ✅ Multi-provider - 99 RPM agregado

Week 5 (Epics 4-5):
  ✅ Resiliência (99.5%+ SLA) + Observability

Week 6 (Epics 6-7):
  ✅ Dashboards funcionais + Config-driven

Week 7 (Epic 8):
  ✅ Documentado e reproduzível

Week 8 (Epic 9):
  ✅ Production-ready - GO LIVE! 🚀

Weeks 9-10 (Buffer):
  ✅ Polish e ajustes
```

---

**Next Steps:**

1. ✅ **Epic breakdown completo!** `docs/epics.md`
2. ⏭️ **UX Design** (conditional) - Squad API tem UI? Provavelmente apenas API/CLI
3. ⏭️ **Architecture** (required) - System design detalhado
4. ⏭️ **Solutioning Gate Check** - Validar PRD + Architecture alignment
5. ⏭️ **Sprint Planning** - 8 weeks sprint breakdown

---

_Este documento decompõe TODOS os requisitos do PRD em 72 stories implementáveis, organizadas em 10 epics sequenciais._

_Cada story é bite-sized (single-session completion) com acceptance criteria BDD claros._

_Ready para Architecture workflow!_ 🚀

