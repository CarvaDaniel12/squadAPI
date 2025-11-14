# Squad API - Multi-Agent LLM Orchestration System

**Iniciado:** 2025-11-12  
**Metodo:** BMAD (Build-Measure-Analyze-Decide)  
**Objetivo:** Sistema de orquestração multi-agente LLM production-ready e reutilizável

---

## Visão Geral

Sistema profissional para orquestrar 11-13 agentes LLM externos (APIs gratuitas/trial) com:
- Rate limiting robusto (Token Bucket + Sliding Window)
- Alta disponibilidade (99.5%+)
- Custo controlado (free-tier maximizado)
- Observabilidade completa (Prometheus + Grafana)
- Compliance (PII sanitization, audit logs)

---

## Conhecimento Base

Todo conhecimento técnico consolidado em:
- **Fonte:** `C:\rl_atomico\research\rate_limits_reference.json`
- **Conteúdo:** 1200+ linhas incluindo:
  - Rate limits REAIS testados (Groq 12 RPM, Cerebras 60 RPM, etc)
  - Patterns comprovados (Token Bucket, Sliding Window, Semaphore)
  - Best practices 2024-2025
  - Arquiteturas de referência
  - Code examples (aiolimiter, pyrate_limiter, tenacity)
  - HuggingFace PRO, Gemini SDK, OpenRouter
  - Throughput máximo: 152 RPM teórico (120-130 real)

---

## Stack Técnica (Definida)

**Backend:**
- Python 3.11+
- FastAPI (API gateway)
- Redis (rate limiting + cache)
- PostgreSQL (persistence + audit)

**Rate Limiting:**
- aiolimiter (local development)
- pyrate-limiter + Redis (production)
- asyncio.Semaphore (global concurrency)

**Retry & Resilience:**
- tenacity (exponential backoff)
- Retry-After aware

**Observability:**
- Prometheus (metrics)
- Grafana (dashboards)
- Slack (alerts)

---

## Próximos Passos (BMAD)

1. **Workflow Init** (agora)
2. **Product Brief** (definir requisitos)
3. **Architecture** (design sistema)
4. **Sprint Planning** (8 semanas)
5. **Implementation** (desenvolvimento)
6. **Testing** (carga, qualidade)
7. **Documentation** (operação)
8. **Go-Live** (staging → production)

---

## Diferencial

Este projeto será **DIFERENTE** do RL Atômico:
- ✅ Foco ÚNICO: orquestração multi-agente
- ✅ Reutilizável (não acoplado a RL)
- ✅ Production-ready desde o início
- ✅ BMAD completo (não shortcuts)
- ✅ Documentação profissional
- ✅ Testes de carga obrigatórios
- ✅ Monitoring desde dia 1

---

**Status:** INICIANDO (workflow-init em andamento)

