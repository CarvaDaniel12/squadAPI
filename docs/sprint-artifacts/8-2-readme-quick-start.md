# Story 8.2: README Quick Start Guide

**Epic:** 8 - Deployment & Documentation
**Story:** 8.2
**Status:** In Progress
**Created:** 2025-11-13
**Priority:** HIGH

## Story Description

As a **new developer joining the Squad API project**,
I want **a clear, concise README with quick start instructions**,
So that **I can get the system running locally in under 30 minutes**.

## Business Value

- **Onboarding Efficiency:** Reduce new developer onboarding from 4+ hours to <30 minutes
- **Self-Service Documentation:** Enable developers to get started without team assistance
- **First Impression:** Professional README attracts contributors and demonstrates project maturity
- **Reduced Support Load:** Clear quick start reduces repetitive setup questions

## Current State Analysis

**Existing Documentation:**
- `README.md`: Exists but minimal (needs expansion)
- `docs/PRD.md`: Product Requirements Document (comprehensive but not quick start)
- `docs/architecture.md`: Technical architecture (detailed but not beginner-friendly)
- `docs/API-KEYS-SETUP.md`: API key instructions (good, needs linking)

**Gaps:**
1. No 5-step quick start guide
2. No visual flow of "first request" example
3. No prerequisites checklist
4. No links to deeper documentation
5. No screenshots of Grafana dashboards
6. No "What is Squad API?" overview section

## Target State

**README.md Structure:**
1. **Header:** Project name, tagline, badges (build status, license)
2. **Overview:** 2-3 paragraphs explaining what Squad API does
3. **Key Features:** Bullet list (multi-provider, rate limiting, observability)
4. **Prerequisites:** Docker, API keys checklist
5. **Quick Start:** 5 exact steps to first request
6. **First Request Example:** cURL command with expected response
7. **What's Inside:** Architecture diagram or component list
8. **Observability:** Screenshots of Grafana dashboards
9. **Documentation Links:** Runbooks, API docs, ADRs
10. **Contributing:** Link to SAFE-DEVELOPMENT-WORKFLOW.md
11. **License:** MIT or appropriate

## Acceptance Criteria

### AC1: Project Overview Section
- [ ] 2-3 paragraph explanation of Squad API purpose
- [ ] "Why Squad API?" value proposition (multi-provider resilience)
- [ ] Key features bullet list (6-8 items)
- [ ] Technology stack mentioned (FastAPI, Redis, PostgreSQL, Prometheus, Grafana)

### AC2: Prerequisites Checklist
- [ ] Docker Desktop 4.x+ (or Docker Engine + Docker Compose)
- [ ] At least 1 LLM provider API key (Groq recommended for free tier)
- [ ] 4GB RAM available
- [ ] Port requirements listed (8000, 3000, 5432, 6379, 9090)

### AC3: Quick Start (5 Steps)
- [ ] Step 1: Clone repository
- [ ] Step 2: Copy `.env.example` to `.env`
- [ ] Step 3: Add API keys to `.env`
- [ ] Step 4: Run `docker-compose up -d`
- [ ] Step 5: Test with first request
- [ ] Each step has exact command + expected output

### AC4: First Request Example
- [ ] cURL command to `/v1/agents/code` with example prompt
- [ ] Expected JSON response shown (truncated for readability)
- [ ] Alternative: Python requests example
- [ ] Links to full API documentation

### AC5: Observability Screenshots
- [ ] Screenshot of Grafana dashboard (Provider Performance)
- [ ] Screenshot of rate limit metrics
- [ ] Screenshot of fallback chain visualization
- [ ] Instructions to access Grafana (http://localhost:3000, admin/admin)

### AC6: Documentation Navigation
- [ ] Link to Deployment Runbook (Story 8.3)
- [ ] Link to Troubleshooting Runbook (Story 8.4)
- [ ] Link to API Documentation (Story 8.6)
- [ ] Link to Architecture Decision Records (Story 8.5)
- [ ] Link to SAFE-DEVELOPMENT-WORKFLOW.md

### AC7: Professional Presentation
- [ ] Badges at top (build status, license, version)
- [ ] Table of contents for long README
- [ ] Code blocks properly formatted with syntax highlighting
- [ ] Emoji used sparingly for visual breaks (optional)
- [ ] Markdown lint passes (no broken links, consistent formatting)

## Implementation Design

### README.md Structure (Detailed)

```markdown
# Squad API 🚀

> Multi-provider LLM orchestration with intelligent fallback, rate limiting, and observability

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()
[![Python](https://img.shields.io/badge/python-3.12+-blue)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)]()

---

## Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [First Request](#first-request)
- [Observability](#observability)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**Squad API** is a production-ready LLM orchestration system that routes requests across multiple AI providers (Groq, Cerebras, Gemini, OpenRouter, Together AI) with intelligent fallback and comprehensive observability.

Built for resilience, Squad API ensures your AI-powered applications stay online even when individual providers face rate limits or outages. Every request is routed to the optimal provider based on real-time availability, with automatic fallback to alternatives if needed.

Perfect for:
- **Production AI applications** requiring 99.9% uptime
- **Cost optimization** across multiple LLM providers
- **Rate limit management** with automatic throttling
- **Observability-first** teams using Prometheus + Grafana

---

## Key Features

- ✅ **Multi-Provider Support:** Groq, Cerebras, Gemini, OpenRouter, Together AI
- ✅ **Intelligent Fallback:** 3-tier fallback chain with quality verification
- ✅ **Rate Limiting:** Per-provider rate limits with auto-throttling
- ✅ **Agent Routing:** 13 specialized agents (code, creative, debug, data, etc.)
- ✅ **Observability:** Prometheus metrics + 4 pre-built Grafana dashboards
- ✅ **Hot-Reload Config:** Update rate limits without restart (watchdog)
- ✅ **Conversation Context:** Multi-turn conversations with Redis storage
- ✅ **One-Command Deployment:** `docker-compose up -d` starts everything

---

## Prerequisites

Before starting, ensure you have:

- [ ] **Docker Desktop 4.x+** (or Docker Engine 20.10+ + Docker Compose 2.x)
- [ ] **4GB RAM available** (6GB recommended)
- [ ] **At least 1 LLM Provider API Key** (see [API Keys Setup](docs/API-KEYS-SETUP.md))
  - Recommended: [Groq](https://console.groq.com/keys) (free tier, fast inference)
- [ ] **Ports available:** 8000, 3000, 5432, 6379, 9090

---

## Quick Start

Get Squad API running locally in 5 minutes:

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/squad-api.git
cd squad-api
```

### Step 2: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# Minimum: Add at least one provider key
GROQ_API_KEY=gsk_your_groq_key_here

# Optional: Add more providers for fallback
CEREBRAS_API_KEY=your_cerebras_key_here
GEMINI_API_KEY=your_gemini_key_here
```

See [API Keys Setup Guide](docs/API-KEYS-SETUP.md) for detailed instructions.

### Step 3: Start All Services

```bash
docker-compose up -d
```

Expected output:
```
Creating network "squad-api_backend" with driver "bridge"
Creating network "squad-api_frontend" with driver "bridge"
Creating volume "squad-api_redis_data" with driver "local"
Creating volume "squad-api_postgres_data" with driver "local"
Creating squad-api-redis-1 ... done
Creating squad-api-postgres-1 ... done
Creating squad-api-prometheus-1 ... done
Creating squad-api-grafana-1 ... done
Creating squad-api-squad-api-1 ... done
```

### Step 4: Verify Health

```bash
docker-compose ps
```

All services should show "healthy" status within 60 seconds.

### Step 5: Make Your First Request

See [First Request](#first-request) below.

---

## First Request

### Using cURL

```bash
curl -X POST http://localhost:8000/v1/agents/code \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a Python function to calculate Fibonacci numbers",
    "conversation_id": "test-123"
  }'
```

### Expected Response

```json
{
  "response": "Here's a Python function to calculate Fibonacci numbers:\n\n```python\ndef fibonacci(n):\n    if n <= 0:\n        return 0\n    elif n == 1:\n        return 1\n    else:\n        return fibonacci(n-1) + fibonacci(n-2)\n```",
  "provider": "groq",
  "model": "llama-3.1-70b-versatile",
  "conversation_id": "test-123",
  "metadata": {
    "fallback_used": false,
    "processing_time_ms": 234
  }
}
```

### Using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/v1/agents/code",
    json={
        "prompt": "Write a Python function to calculate Fibonacci numbers",
        "conversation_id": "test-123"
    }
)

print(response.json()["response"])
```

See [API Documentation](http://localhost:8000/docs) for all endpoints.

---

## Observability

Squad API includes comprehensive observability with Prometheus + Grafana:

### Access Grafana

1. Open http://localhost:3000
2. Login: `admin` / `admin` (change on first login)
3. Navigate to Dashboards

### Pre-Built Dashboards

**Provider Performance Dashboard:**
![Provider Performance](docs/images/grafana-provider-performance.png)
- Request volume by provider
- Success/error rates
- Latency percentiles (p50, p95, p99)
- Provider availability

**Rate Limiting Dashboard:**
![Rate Limiting](docs/images/grafana-rate-limits.png)
- Current usage vs. limits
- Throttling events
- Queue depths
- Auto-throttle adjustments

**Fallback Chain Dashboard:**
![Fallback Chain](docs/images/grafana-fallback.png)
- Fallback trigger rate
- Fallback success rate
- Provider health scores
- Chain traversal depth

**System Health Dashboard:**
![System Health](docs/images/grafana-system.png)
- Request throughput
- Error rates
- Redis/PostgreSQL health
- Resource utilization

---

## Documentation

### Core Documentation

- **[Deployment Runbook](docs/runbooks/deployment.md):** Production deployment guide
- **[Troubleshooting Runbook](docs/runbooks/troubleshooting.md):** Common issues and fixes
- **[API Documentation](http://localhost:8000/docs):** Interactive OpenAPI/Swagger docs
- **[Architecture](docs/architecture.md):** System design and components

### Advanced Topics

- **[Architecture Decision Records (ADRs)](docs/adrs/):** Design decisions explained
- **[PRD](docs/PRD.md):** Product Requirements Document
- **[Epic Documentation](docs/epics.md):** Feature development roadmap

---

## What's Inside

Squad API consists of 5 core services:

| Service | Purpose | Port |
|---------|---------|------|
| **Squad API** | FastAPI application with agent routing | 8000 |
| **Redis** | Conversation context storage | 6379 |
| **PostgreSQL** | Rate limit state persistence | 5432 |
| **Prometheus** | Metrics collection and alerting | 9090 |
| **Grafana** | Metrics visualization dashboards | 3000 |

### Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│      Squad API (FastAPI)        │
│  ┌───────────────────────────┐  │
│  │   Agent Router (13)       │  │
│  ├───────────────────────────┤  │
│  │   Provider Factory        │  │
│  │   ├─ Groq                 │  │
│  │   ├─ Cerebras             │  │
│  │   ├─ Gemini               │  │
│  │   ├─ OpenRouter           │  │
│  │   └─ Together AI          │  │
│  ├───────────────────────────┤  │
│  │   Fallback Orchestrator   │  │
│  ├───────────────────────────┤  │
│  │   Rate Limiter            │  │
│  └───────────────────────────┘  │
└────┬──────────────────────┬─────┘
     │                      │
     ▼                      ▼
┌─────────┐          ┌──────────────┐
│  Redis  │          │  PostgreSQL  │
└─────────┘          └──────────────┘
     ▲                      ▲
     │                      │
     └──────────┬───────────┘
                │
         ┌──────▼──────┐
         │ Prometheus  │
         └──────┬──────┘
                │
         ┌──────▼──────┐
         │   Grafana   │
         └─────────────┘
```

---

## Contributing

We follow the **BMAD Method** (Business-Meaningful Atomic Deliverables) for all development:

1. Read [SAFE Development Workflow](docs/SAFE-DEVELOPMENT-WORKFLOW.md)
2. Check current sprint status in `.bmad-ephemeral/sprint-status.yaml`
3. Follow the Epic → Story → Artifact → Implementation → Testing flow
4. All PRs require tests and documentation updates

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Support

- **Issues:** [GitHub Issues](https://github.com/your-org/squad-api/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-org/squad-api/discussions)
- **Docs:** [Full Documentation](docs/)

---

**Made with ❤️ by the Squad API Team**
```

### Screenshots Needed

1. **Provider Performance Dashboard:**
   - File: `docs/images/grafana-provider-performance.png`
   - Content: Request volume, success rates, latency heatmap
   - Grafana panel: Epic 6 dashboard

2. **Rate Limiting Dashboard:**
   - File: `docs/images/grafana-rate-limits.png`
   - Content: Usage vs. limits gauge, throttling events
   - Grafana panel: Epic 6 dashboard

3. **Fallback Chain Dashboard:**
   - File: `docs/images/grafana-fallback.png`
   - Content: Fallback trigger rate, provider health scores
   - Grafana panel: Epic 6 dashboard

4. **System Health Dashboard:**
   - File: `docs/images/grafana-system.png`
   - Content: Request throughput, error rates, resource usage
   - Grafana panel: Epic 6 dashboard

### Badge Sources

- Build Status: GitHub Actions (if configured)
- License: Static badge from shields.io
- Python Version: Static badge `3.12+`
- FastAPI Version: Static badge `0.104+`

## Testing Checklist

### Content Completeness

- [ ] All sections present (Overview, Features, Prerequisites, Quick Start, etc.)
- [ ] Code blocks use correct syntax highlighting (bash, json, python)
- [ ] All links functional (internal docs, external API key signup)
- [ ] Screenshots embedded with alt text
- [ ] Table of contents matches headings

### Technical Accuracy

- [ ] Quick start commands execute successfully
- [ ] First request cURL command works
- [ ] Python example runs without errors
- [ ] Port numbers match docker-compose.yaml
- [ ] Service names match actual containers
- [ ] Environment variables match .env.example

### User Testing

- [ ] New developer follows README from scratch
- [ ] Onboarding completes in <30 minutes
- [ ] No confusion or missing steps
- [ ] Screenshots load correctly
- [ ] Links navigate to correct pages

### Markdown Quality

- [ ] Markdown lint passes (no warnings)
- [ ] Headings hierarchical (H1 → H2 → H3)
- [ ] Code blocks properly closed
- [ ] No broken internal links
- [ ] Consistent formatting (lists, emphasis)

## Definition of Done

- [ ] Story artifact created with AC1-AC7
- [ ] README.md created with all sections
- [ ] All 7 acceptance criteria met
- [ ] Screenshots captured and embedded (4 images)
- [ ] Badges added at top
- [ ] Code examples tested and working
- [ ] Links verified (internal + external)
- [ ] New developer onboarding test passed (<30 min)
- [ ] Markdown lint clean
- [ ] Sprint status updated: 8-2 → done

## Dependencies

- Story 8.1: Docker Compose Complete Stack (DONE)
- Epic 6: Grafana dashboards must exist for screenshots
- API-KEYS-SETUP.md: Must exist for linking

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Screenshots become outdated | Medium | Store Grafana dashboard JSON, regenerate screenshots |
| Links break over time | Medium | Automated link checker in CI |
| README becomes too long | Low | Use table of contents, consider multi-page docs |
| Quick start fails for edge cases | Medium | Test on fresh Windows/Mac/Linux environments |

## Notes

- README is first impression for all developers
- Balance detail with conciseness (aim for 5-minute read)
- Screenshots make observability tangible
- Clear quick start reduces onboarding friction
- Link to deeper docs instead of duplicating content

## References

- Epic 8 Technical Context: `.bmad-ephemeral/epics/8-deployment-documentation-context.md`
- Existing README: `README.md`
- API Keys Setup: `docs/API-KEYS-SETUP.md`
- Architecture: `docs/architecture.md`
- Grafana Dashboards: `config/grafana/dashboards/`
