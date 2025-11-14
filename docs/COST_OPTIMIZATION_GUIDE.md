# Cost Optimization Setup Guide

## 📋 Overview

Esta estratégia reduz custos em **60-70%** usando providers gratuitos sempre que possível e APIs pagas apenas quando necessário.

## 🔑 API Keys Setup

### Free Providers (Já Configuradas ✅)
```bash
GROQ_API_KEY=gsk_nmw...          # ✅ OK
CEREBRAS_API_KEY=csk_tfe...      # ✅ OK
GEMINI_API_KEY=AIza...           # ✅ OK
OPENROUTER_API_KEY=sk-or-v1...   # ✅ OK
```

### Paid Providers (Para Configurar)
Adicione no arquivo `.env`:

```bash
# OpenAI (para fallback e tarefas complexas)
OPENAI_API_KEY=sk-proj-...

# Anthropic (para tarefas críticas de produção)
ANTHROPIC_API_KEY=sk-ant-...
```

## 💰 Estratégia de Custos

### Routing Automático por Complexidade

| Complexidade | Providers | Custo Esperado |
|--------------|-----------|----------------|
| **Simple** | Groq → Cerebras → Gemini | $0 (100% free) |
| **Medium** | Groq → Gemini → OpenAI Mini | ~$0.001-0.01 |
| **Complex** | Groq → OpenAI Mini → OpenAI | ~$0.01-0.05 |
| **Critical** | Anthropic → OpenAI | ~$0.05-0.20 |

### Savings Reais

Com a demo que rodamos:
- **OpenAI only**: $0.154
- **Anthropic only**: $0.217
- **Nossa estratégia**: $0.060 (61-72% economia!)

## 📊 Budget Control

### Daily Budget: $5.00
Com $5/dia você consegue:
- ✅ **1000+ requests gratuitos** (Groq, Gemini, Cerebras)
- ✅ **50-100 requests pagos** (OpenAI Mini)
- ✅ **~5 requests premium** (Claude/GPT-4)

### Enforcement Automático
- ⚠️  Alerta em 80% do budget ($4.00)
- 🚫 Fallback para free providers ao atingir 100%
- 📊 Tracking por usuário e conversação

## 🎯 Provider Selection Logic

```python
# Simple task (análise, chat básico)
if task == 'simple':
    use_providers = ['groq', 'cerebras', 'gemini']  # FREE only

# Medium task (code generation)
elif task == 'medium':
    use_providers = ['groq', 'gemini', 'openai_mini']  # Try free first

# Complex task (arquitetura, refactoring)
elif task == 'complex':
    use_providers = ['groq', 'openai_mini', 'openai']  # Free → cheap → premium

# Critical task (produção, segurança)
elif task == 'critical':
    use_providers = ['anthropic', 'openai']  # Premium quality
```

## 🔧 Agent-Specific Routing

### Analyst (70% das requests)
- **Default**: Simple tier (FREE only)
- **Allow Premium**: ❌ No
- **Reason**: Análise não precisa de premium

### Architect (10% das requests)
- **Default**: Complex tier
- **Allow Premium**: ✅ Yes
- **Reason**: Arquitetura precisa qualidade

### Dev (15% das requests)
- **Default**: Medium tier
- **Allow Premium**: ❌ No
- **Reason**: Code gen funciona bem em free

### PM (5% das requests)
- **Default**: Simple tier (FREE only)
- **Allow Premium**: ❌ No
- **Reason**: Tasks de PM são diretos

## 📈 Cost Tracking

### Real-time Monitoring
```python
from src.utils.cost_optimizer import CostOptimizer

optimizer = CostOptimizer()

# Após cada request
optimizer.record_usage(
    provider='groq',
    tokens_input=500,
    tokens_output=300,
    user_id='user-123',
    conversation_id='conv-456'
)

# Ver estatísticas
stats = optimizer.get_stats()
print(f"Daily spend: ${stats['daily_spend']:.4f}")
print(f"Budget remaining: ${stats['budget_remaining']:.4f}")
```

### Daily Report
```bash
💰 COST OPTIMIZATION REPORT
============================================================
Daily Budget:     $5.00
Current Spend:    $0.0600
Remaining:        $4.9400
Budget Used:      1.2%

Requests Today:
  Free:           10
  Paid:           1

Costs by Provider:
  groq            $0.0000
  anthropic       $0.0600
```

## 🚀 Integration com Orchestrator

O `CostOptimizer` se integra automaticamente com o `AgentOrchestrator`:

```python
# Em src/agents/orchestrator.py
orchestrator = AgentOrchestrator(
    cost_optimizer=CostOptimizer(),  # ← Add this
    # ... outros params
)

# Durante execution
provider = orchestrator.cost_optimizer.select_provider(
    task_complexity=request.complexity or 'simple',
    agent_id=request.agent,
    user_id=request.user_id
)
```

## 💡 Best Practices

### 1. Use Free Tier ao Máximo
- 90% das tarefas funcionam bem em Groq/Gemini
- Reserve paid APIs para casos realmente necessários

### 2. Configure Complexity Corretamente
```python
request = AgentExecutionRequest(
    agent='analyst',
    task='Analyze this code...',
    complexity='simple'  # ← Força free providers
)
```

### 3. Monitor Custos Diariamente
```bash
# Ver report
python scripts/demo_cost_optimization.py

# Check budget status
curl http://localhost:8000/api/v1/cost/stats
```

### 4. Adjust Budget Baseado em Uso Real
```yaml
# config/cost_optimization.yaml
cost_limits:
  daily_budget: 5.00  # ← Ajuste baseado no seu uso
  alert_at_percent: 80
```

## 🔒 Rate Limiting para Paid APIs

### Protections Adicionais
```yaml
rate_limiting:
  paid_tier_rpm: 10       # Max 10 paid requests/min
  paid_tier_tpm: 50000    # Max 50k tokens/min
  per_user_paid_rpm: 2    # Each user max 2 paid/min
```

Isso previne:
- ✅ Spikes de custo acidentais
- ✅ Abuse de APIs pagas
- ✅ Budget overruns

## 📊 Metrics & Alerts

### Prometheus Metrics
```
# Cost metrics exported
squad_api_cost_total{provider="openai"}
squad_api_budget_remaining
squad_api_requests_paid_total
squad_api_requests_free_total
```

### Grafana Dashboard
- Real-time cost tracking
- Budget usage visualization
- Provider distribution
- Cost per user/conversation

## ✅ Next Steps

1. **Adicione suas API keys** no `.env`:
   ```bash
   OPENAI_API_KEY=sk-proj-...
   ANTHROPIC_API_KEY=sk-ant-...
   ```

2. **Teste a estratégia**:
   ```bash
   python scripts/demo_cost_optimization.py
   ```

3. **Configure budget** em `config/cost_optimization.yaml`

4. **Monitor custos** via `/api/v1/cost/stats`

5. **Ajuste routing** baseado nos seus padrões de uso

## 🎯 Expected Results

Com esta estratégia:
- ✅ **60-70% reduction** nos custos vs usar só OpenAI
- ✅ **90% das requests** usando free tier
- ✅ **Budget enforcement** automático
- ✅ **Quality maintained** para tarefas críticas
- ✅ **Full cost visibility** e tracking

---

**Pronto para começar!** Adicione suas API keys e rode o demo. 🚀
