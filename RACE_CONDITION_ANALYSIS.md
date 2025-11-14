# Análise de Race Conditions - Sistema de Rate Limiting

## Problemas Identificados

### 1. **Race Condition no Rate Limiter Combinado** (CRÍTICO)

**Arquivo**: `src/rate_limit/combined.py:158-177`

**Problema**: Entre a verificação do limite e a adição do request, múltiplas threads podem passar na verificação e todas tentam adicionar requests, fazendo a sliding window exceder os limites.

```python
# Step 1: Check sliding window (fast rejection if over limit)
if not await self.sliding_window.check_limit(...):
    await self.sliding_window.wait_for_capacity(...)

# Step 2: Acquire token bucket (may delay for refill)
async with self.token_bucket.acquire(provider):
    # Step 3: Add to sliding window
    await self.sliding_window.add_request(provider, window_size=config.window_size)
```

**Impacto**: Race condition TOCTOU (Time-of-Check-Time-of-Use) pode permitir mais requests que o limite configurado.

**Likelihood**: ALTA
**Impact**: CRÍTICO

---

### 2. **Race Condition no Token Bucket In-Memory** (ALTO)

**Arquivo**: `src/rate_limit/token_bucket.py:52-70`

**Problema**: Mesmo com lock, a função `_refill()` acessa `self.last_refill` fora do lock, causando inconsistência entre múltiplas instâncias.

```python
async def request_delay(self) -> float:
    async with self.lock:
        self._refill()  # _refill() acessa self.last_refill sem lock
        if self.tokens >= 1:
            self.tokens -= 1
            return 0.0
```

**Impacto**: Pode causar cálculos incorretos de tokens disponíveis.

**Likelihood**: MÉDIA
**Impact**: ALTO

---

### 3. **Race Condition nas Operações Redis** (CRÍTICO)

**Arquivo**: `src/rate_limit/sliding_window.py:114-146`

**Problema**: As operações `check_limit()` e `add_request()` no Redis não são atômicas, permitindo que múltiplas threads leiam o estado e modifiquem simultaneamente.

```python
# Thread A: check_limit() - vê count = 5
count = await self.redis.zcount(key, cutoff, now)
return count < rpm_limit  # Thread A passa

# Thread B: check_limit() - vê count = 5
count = await self.redis.zcount(key, cutoff, now)
return count < rpm_limit  # Thread B passa

# Thread A: add_request() - adiciona
await self.redis.zadd(key, {request_id: now})

# Thread B: add_request() - adiciona
await self.redis.zadd(key, {request_id: now})

# Resultado: count = 7 (excede limite!)
```

**Impacto**: Pode violar completamente os rate limits.

**Likelihood**: ALTA
**Impact**: CRÍTICO

---

### 4. **Race Condition no Contador do GlobalSemaphore** (MÉDIO)

**Arquivo**: `src/rate_limit/semaphore.py:62-76`

**Problema**: Os contadores customizados `_active_count` e `_total_acquired` podem ser atualizados incorretamente em caso de exceptions.

```python
async with self.semaphore:
    self._active_count += 1  # Pode não ser decrementado se exception
    self._total_acquired += 1
    try:
        yield
    finally:
        self._active_count -= 1
```

**Impacto**: Contadores incorretos podem afectar decisões de rate limiting.

**Likelihood**: MÉDIA
**Impact**: MÉDIO

---

### 5. **Race Condition na Factory de Providers** (ALTO)

**Arquivo**: `src/providers/factory.py:158-164`

**Problema**: Operações no dicionário `self.providers` não são thread-safe.

```python
providers[name] = provider  # Escrita não-atômica
return self.providers.get(name)  # Leitura não-atômica
```

**Impacto**: Provider pode não estar disponível para uma thread mesmo após criação.

**Likelihood**: MÉDIA
**Impact**: ALTO

---

### 6. **Race Conditions em Métricas** (MÉDIO)

**Arquivo**: `src/agents/orchestrator.py:291-294`

**Problema**: Múltiplas operações de métricas simultâneas podem causar corrupção de dados.

```python
record_request_success(provider=provider_name, agent=agent_id)
record_latency(provider_name, request.agent, latency_ms / 1000.0)
record_tokens(provider_name, tokens_in, tokens_out)
```

**Impacto**: Métricas incorretas podem afectar monitoramento.

**Likelihood**: MÉDIA
**Impact**: MÉDIO

---

### 7. **Race Condition no Memory Store** (MÉDIO)

**Arquivo**: `src/rate_limit/sliding_window.py:73-84`

**Problema**: Lista em `_memory_store[key]` é modificada sem sincronização.

```python
self._memory_store[key].append(now)  # Thread-unsafe
self._memory_store[key] = [...]      # Thread-unsafe
```

**Impacto**: Pode causar corruption da lista em memória.

**Likelihood**: MÉDIA
**Impact**: MÉDIO

---

## Resumo de Priorização

| Problema | Likelihood | Impact | Prioridade |
|----------|------------|--------|------------|
| Rate Limiter Combinado | ALTA | CRÍTICO | 🔴 **CRÍTICO** |
| Operações Redis | ALTA | CRÍTICO | 🔴 **CRÍTICO** |
| Token Bucket In-Memory | MÉDIA | ALTO | 🟡 **ALTO** |
| Factory de Providers | MÉDIA | ALTO | 🟡 **ALTO** |
| GlobalSemaphore Counters | MÉDIA | MÉDIO | 🟠 **MÉDIO** |
| Métricas | MÉDIA | MÉDIO | 🟠 **MÉDIO** |
| Memory Store | MÉDIA | MÉDIO | 🟠 **MÉDIO** |

## Proximos Passos

1. **Confirmar diagnóstico** com o usuário
2. **Propor soluções** para cada race condition
3. **Implementar fixes** de forma prioritizada
4. **Adicionar testes** de concorrência
5. **Monitorar** efetividade das correções
