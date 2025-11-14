# Product Brief: Squad API

**Date:** 2025-11-12  
**Author:** Dani  
**Context:** Personal Empowerment + Professional Tool

---

## Executive Summary

Squad API é uma infraestrutura de orquestração multi-agente LLM que permite a pessoas **não-programadoras criar soluções de software** usando agentes especializados. É uma ferramenta de empowerment que transforma a barreira entre "ter ideias" e "executar soluções" em uma ponte acessível.

Construído com metodologia BMad e arquitetura production-ready, Squad API é uma **base reutilizável** que, uma vez construída, pode ser aplicada em múltiplos projetos futuros - efetivamente multiplicando a capacidade criativa do usuário.

---

## Core Vision

### Problem Statement

**A Barreira Entre Ideias e Execução**

Muitas pessoas têm a paixão por criar soluções - frameworks, ferramentas, sistemas que resolvem problemas reais. Elas entendem lógica, processos, qualidade e metodologia. Mas existe uma barreira técnica: a necessidade de saber programar.

Durante anos, isso forçou uma escolha: ou você aprende a programar (investimento massivo de tempo), ou abandona a criação de software e foca em áreas adjacentes (QA, estratégia, gestão). Essa escolha cria uma frustração permanente - a sensação de **ter ideias mas não ter as mãos para executá-las**.

**O Momento de Transformação:**

Agentes LLM modernos (2024-2025) mudaram essa equação. Eles conseguem:
- Escrever código de qualidade
- Seguir metodologias estruturadas (como BMad)
- Trabalhar como especialistas (architect, dev, QA, PM)
- Iterar com feedback humano

Mas usar LLMs diretamente ainda tem problemas:
- **Rate limits esgotam rápido** (429 errors em 80% dos requests)
- **Contexto se perde** entre conversas
- **Qualidade varia** (precisa de retry, fallback, validação)
- **Não é reutilizável** (cada projeto recomeça do zero)

### Proposed Solution

**Squad API: Sua Equipe de Especialistas Sempre Disponível**

Squad API é uma infraestrutura que:

1. **Orquestra 11-13 agentes LLM especializados** - Cada um age como um profissional BMad (analyst, architect, PM, dev, QA, etc.)

2. **Gerencia rate limits inteligentemente** - Auto-throttling, fallback chains, burst interleaving garantem que você nunca pare por 429 errors

3. **Mantém contexto e qualidade** - Dedup cache, Worker/Boss hierarchy, retry com backoff garantem resultados consistentes

4. **É reutilizável por design** - Config-driven, modular, production-ready. Construa uma vez, use em dezenas de projetos.

**O Resultado:**

Você **recupera a capacidade de criar soluções**. Não como programador, mas como **orquestrador de uma squad especializada**. Você define o "o quê" e o "por quê", e a squad executa o "como".

### Key Differentiators

**1. Foco em Empowerment, não apenas Automação**

Não é "mais uma ferramenta de automação". É uma ferramenta que **remove a barreira entre ideias e execução** para pessoas que entendem problemas mas não sabem codar.

**2. Production-Ready desde o Início**

Não é um protótipo. É construído com:
- 99.5%+ SLA (fallback automático, auto-throttling)
- Observabilidade completa (Prometheus + Grafana)
- Rate limiting robusto (Token Bucket + Sliding Window)
- Arquitetura battle-tested (patterns 2024-2025)

**3. Reutilizável por Design**

Uma vez construído, serve para **múltiplos projetos futuros**:
- Novo projeto? Mesma infraestrutura
- Nova ideia? Mesma squad
- Novo problema? Mesmas capacidades

**4. Metodologia BMad Embarcada**

Os agentes não são "chatbots genéricos". São **especialistas BMad** que seguem workflows estruturados, garantindo qualidade e completude.

---

## Target Users

### Primary Users

**Pessoas com Mentalidade de Criador + Barreira Técnica**

**Perfil:**
- **Background:** QA, Product Management, Business Analysis, Strategy
- **Experiência:** 5-10+ anos em tech, entendem processos e qualidade
- **Frustração:** "Sei O QUÊ precisa ser feito, mas não SEI codar"
- **Desejo:** Ter "nas mãos" a capacidade de criar soluções
- **Descoberta:** LLMs + metodologias estruturadas (BMad) permitem isso

**Situação Atual:**
- Dependem de devs para executar ideias
- Ou pagam por soluções custom (caro, lento)
- Ou usam no-code/low-code (limitado, não escalável)
- Sentem que "perderam a chance" de ser criadores

**O que Squad API permite:**
- **Autonomia:** Executar suas próprias ideias
- **Velocidade:** Não esperar por devs disponíveis
- **Qualidade:** BMad + production-ready garante resultado profissional
- **Multiplicação:** Uma base reutilizável para N projetos

**Exemplo concreto (Dani):**
- 8 anos como QA, entende qualidade e metodologia
- Escolheu estratégia de qualidade em vez de código (sem arrependimentos!)
- Mas sente falta de criar frameworks e soluções com as próprias mãos
- Descobriu que LLMs + BMad permitem isso agora
- Squad API é a infraestrutura que multiplica essa capacidade

**Projetos que quer criar:**
- **RL's atômicos pra caçar bugs** - Automação de testes com reinforcement learning
- **Frameworks que unificam testes** - Dashboard user-friendly que consolida múltiplos testes numa tela
- **App de VTT (Virtual Tabletop)** - Sistema para jogar RPG online com amigos
- **E muito mais** - A lista é longa quando você tem ideias mas não tinha como executá-las

**O Pattern:**
- Range completo: profissional (RL's, frameworks) + pessoal (VTT)
- QA background transparece: qualidade, automação, user experience
- Sem Squad API: cada projeto reinicia infraestrutura do zero
- Com Squad API: mesma base, foco no problema específico

### Secondary Users

**Desenvolvedores que querem multiplicar produtividade**

**Perfil:**
- Sabem codar, mas querem **acelerar** desenvolvimento
- Trabalham sozinhos ou em times pequenos
- Precisam de "squad virtual" para projetos paralelos

**O que ganham:**
- Worker/Boss hierarchy: LLMs fazem tasks rotineiras
- Eles focam em decisões arquiteturais e code review
- 5-10x productivity boost

---

## Success Metrics

### Para o Criador (Dani)

**Sucesso é quando:**

1. **Autonomia Recuperada**
   - Consegue iniciar e executar projetos sozinho
   - Não precisa esperar ou depender de outros devs
   - Vai da ideia ao MVP funcional em semanas (não meses)

2. **Reutilização Comprovada**
   - Squad API é usado em 3+ projetos diferentes
   - Cada novo projeto começa mais rápido que o anterior
   - "Build once, use everywhere" é realidade

3. **Qualidade Mantida**
   - 99.5%+ SLA alcançado (measured em 1 semana)
   - <1% de 429 errors (rate limiting funciona)
   - Código gerado passa em code review
   - Deployments não quebram em produção

4. **Orgulho Pessoal**
   - "Eu CRIEI isso" (não apenas gerenciei ou especifiquei)
   - Outras pessoas usam e se beneficiam
   - É uma peça de portfolio técnico sólida

### Métricas Técnicas (Objetivas)

**MVP Success Criteria:**

```yaml
functional:
  - ✅ Orquestra 11-13 agentes especializados
  - ✅ Rate limiting: <1% de 429 errors
  - ✅ Fallback funciona em <5s
  - ✅ Dedup cache: >20% hit rate

non_functional:
  - ✅ Disponibilidade: ≥99.5% (medido em 1 semana)
  - ✅ Throughput: 120-130 RPM sustained
  - ✅ Latência P95: <2s (potentes), <5s (pequenos)
  - ✅ Custo: 100% free-tier (zero custos de API)

operational:
  - ✅ Dashboards Grafana funcionais
  - ✅ Deploy reproduzível (Docker Compose)
  - ✅ Documentação completa (README + runbooks)
```

**Milestone de Reutilização:**

- ✅ Projeto 1 (Squad API): 8-10 semanas build
- ✅ Projeto 2 (usando Squad API): <2 semanas do zero ao MVP
- ✅ Projeto 3+: <1 semana do zero ao MVP

### Business Objectives

**Para Dani (Pessoal + Profissional):**

1. **Curto prazo (3 meses):**
   - Squad API funcional e reutilizável
   - 1 projeto adicional usando Squad API
   - Portfolio técnico sólido

2. **Médio prazo (6-12 meses):**
   - 3-5 projetos usando Squad API:
     - RL Atômicos (bug hunting automation)
     - Test Dashboard Framework
     - VTT App (RPG online)
     - +2 outros projetos
   - Casos de uso validados (profissional + pessoal)
   - Possivelmente contribuir para comunidade (open-source?)

3. **Longo prazo (1-2 anos):**
   - Squad API como "superpoder" pessoal
   - Transição de carreira? (QA + Builder híbrido)
   - Potencial de monetizar soluções criadas

---

## MVP Scope

### Core Features

**1. Multi-Agent Orchestration**
- Instruir LLMs de APIs externas a agirem como agentes BMad especializados
- Coordenar 11-13 agentes simultaneamente
- Gestão de contexto/personas BMad

**2. Rate Limiting Robusto**
- Token Bucket + Sliding Window (60s)
- Auto-throttling adaptativo (reduz 20% em spikes)
- Burst interleaving (distribui carga uniformemente)
- **Resultado:** <1% de 429 errors

**3. Resiliência & Fallback**
- Fallback chains config-driven (worker → boss → boss-ultimate)
- Retry exponential backoff + Retry-After aware
- Worker/Boss hierarchy (otimiza throughput)
- **Resultado:** 99.5%+ disponibilidade

**4. Observabilidade Completa**
- Prometheus metrics (requests, 429s, latency, tokens)
- Grafana dashboards real-time
- Slack alerts automáticos
- **Resultado:** Visibilidade total do sistema

**5. Base Reutilizável**
- Config-driven (YAML configs para agents, chains, limits)
- Modular (cada componente independente)
- Documented (README + runbooks + ADRs)
- **Resultado:** Reutilizar em projetos futuros

### Out of Scope for MVP

**Não fazer no MVP (pode vir depois):**

1. **UI/Dashboard web** - CLI + Grafana é suficiente inicialmente
2. **Multi-tenancy** - Single-user é OK para MVP
3. **Auth/Security complexa** - API keys simples
4. **Hosted service** - Self-hosted Docker Compose
5. **Monetização** - Foco é uso pessoal primeiro
6. **Suporte a TODOS providers** - 4-5 providers principais (Groq, Cerebras, Gemini, OpenRouter, Together AI)
7. **Advanced features:**
   - A/B testing de modelos
   - Scraper automático de pricing
   - Credential rotation automático
   - Advanced PII sanitization

### MVP Success Criteria

**"MVP está pronto quando:"**

1. ✅ Consigo usar Squad API para iniciar um NOVO projeto
2. ✅ LLMs agem como agentes BMad (seguem workflows, geram artifacts)
3. ✅ Rate limits NÃO são problema (sistema funciona 99.5%+ do tempo)
4. ✅ Posso ver o que está acontecendo (Grafana dashboards)
5. ✅ Documentação permite eu reproduzir setup em outra máquina

**"MVP falhou se:"**

- ❌ 429 errors ainda ocorrem >1% das vezes
- ❌ Sistema para por >1 hora em 1 semana
- ❌ Não consigo reutilizar em outro projeto
- ❌ Documentação está incompleta (não consigo redeployar)

### Future Vision Features

**Post-MVP (quando base está sólida):**

**Phase 2: Primeiros Projetos Reais**
- **RL Atômicos pra Bug Hunting** - Sistema de reinforcement learning que automaticamente testa e encontra bugs
- **Test Dashboard Framework** - Interface user-friendly que unifica múltiplos frameworks de teste numa única tela
- **VTT (Virtual Tabletop) App** - Sistema para jogar RPG online com gerenciamento de personagens, mapas, dados

**Phase 3: Expand Capabilities**
- Mais providers (HuggingFace PRO, Claude, etc.)
- Multimodal (imagens, áudio) - útil para VTT (mapas, tokens)
- Advanced context management (RAG, vector DB)

**Phase 4: Share & Collaborate**
- Multi-user support (VTT precisa disso!)
- Shared squads (collaborate com outros creators)
- Web UI (mais acessível para non-tech)

**Phase 5: Community & Ecosystem**
- Open-source (?) - Ajudar outras pessoas na mesma situação
- Plugin system (custom agents)
- Marketplace de workflows BMad

**Phase 6: Monetization (Maybe)**
- Hosted service
- Enterprise features (sell to QA teams?)
- Premium agents/workflows

---

## Technical Preferences

**From Technical Research (já decidido):**

```yaml
core:
  language: Python 3.11+
  api_framework: FastAPI
  
rate_limiting:
  library: pyrate-limiter
  backend: Redis 7.0+
  algorithm: Token Bucket + Sliding Window (60s)
  
async:
  http_client: aiohttp
  retry: tenacity
  concurrency: asyncio.Semaphore(10-12 global)

persistence:
  database: PostgreSQL 15+
  cache: Redis (shared)
  
observability:
  metrics: Prometheus
  visualization: Grafana
  alerts: Slack webhooks
  
providers:
  primary: Groq, Cerebras, Gemini (SDK), OpenRouter, Together AI
  future: HuggingFace PRO, Claude, others
```

**Architecture Decision (ADR):**
- Option 3: Complete Multi-Agent Architecture
- Confidence: HIGH (100% alignment)
- Investment: 8 weeks + 2 buffer

**Deployment:**
- Local dev: Docker Compose
- Production: Same Docker Compose (self-hosted)
- Future: Kubernetes (if needed)

---

## Timeline Constraints

**Realistic Timeline:**

```yaml
Phase 1: Foundation (Weeks 1-2)
  - Redis, PostgreSQL, Prometheus/Grafana setup
  - FastAPI base + rate limiter core
  - Config system (YAML)

Phase 2: Core Features (Weeks 3-4)
  - Provider wrappers (5 providers)
  - Agent router + fallback chains
  - Worker/Boss tier mapping

Phase 3: Advanced (Weeks 5-6)
  - Auto-throttling adaptativo
  - Burst scheduler
  - Dedup cache
  - Metrics completo

Phase 4: Production Ready (Weeks 7-8)
  - PII sanitization
  - Audit logging
  - Slack alerts
  - Documentation (runbooks)

Buffer: Weeks 9-10 (ajustes, testes)

Total: 10 semanas (2.5 meses)
```

**Trade-off:** 
- Investir 10 semanas AGORA
- Economizar 6-8 semanas em CADA projeto futuro
- Breakeven: Após 2 projetos
- ROI real: Após 3+ projetos (tempo economizado >>> tempo investido)

---

## Risks and Assumptions

### Key Assumptions

1. **LLMs continuarão melhorando** - GPT-5, Claude 4, Gemini 3 virão
2. **Free-tiers continuarão existindo** - Pelo menos para 1-2 anos
3. **BMad Method é sólido** - Workflows estruturados funcionam
4. **Dani tem 10 semanas disponíveis** - Tempo para build completo

### Key Risks

| **Risco** | **Prob** | **Impacto** | **Mitigação** |
|-----------|----------|-------------|---------------|
| **Dani perde motivação** | Média | Alto | MVP iterativo, quick wins cedo |
| **LLMs degradam qualidade** | Baixa | Alto | Fallback chains, múltiplos providers |
| **Free-tiers acabam** | Baixa | Médio | Já terá valor criado, migrar para paid |
| **Complexidade overwhelm** | Alta | Médio | BMad Method guia, checkpoints frequentes |
| **10 semanas não suficiente** | Média | Alto | Buffer 2 semanas, MVP reducionista |
| **Não reutiliza em outros projetos** | Baixa | Alto | Design modular desde início |

---

## Supporting Materials

**References:**

1. **Technical Research Report:** `docs/research-technical-2025-11-12.md`
   - Análise completa de 3 opções arquiteturais
   - Recomendação: Complete Multi-Agent Architecture
   - Roadmap detalhado 8 semanas
   - ADRs e risk mitigation

2. **BMad Method Documentation:** `.bmad/bmm/`
   - Workflows estruturados
   - Agent personas
   - Best practices

3. **Rate Limits Research:** `rate_limits_reference.json`
   - 1200+ linhas de research testado
   - Rate limits reais verificados
   - Patterns comprovados

---

_Este Product Brief captura a visão e requisitos para Squad API._

_Ele foi criado através de descoberta colaborativa e reflete as necessidades únicas deste projeto de empowerment pessoal + ferramenta profissional._

_Próximo: PRD (Product Requirements Document) vai transformar esta visão em requisitos detalhados e epics/stories._

