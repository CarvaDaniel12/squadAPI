# Soluções para Race Conditions - Sistema de Rate Limiting

## 1. **Rate Limiter Combinado - TOCTOU** (CRÍTICO)

### **Problema**: Operação não-atômica entre check_limit() e add_request()

### **Solução**: Implementar operação atômica com Lua Script no Redis

```lua
-- Arquivo: src/rate_limit/atomic_sliding_window.lua

-- Script Lua para operação atômica
local key = KEYS[1]
local window_size = tonumber(ARGV[1])
local rpm_limit = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local request_id = ARGV[4]

-- Limpar entradas antigas
local cutoff = now - window_size
redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)

-- Contar requests atuais
local count = redis.call('ZCARD', key)

-- Verificar se podemos adicionar (atômico)
if count < rpm_limit then
    -- Adicionar novo request
    redis.call('ZADD', key, now, request_id)
    -- Configurar expiry
    redis.call('EXPIRE', key, window_size)
    return 1  -- Sucesso
else
    return 0  -- Falha (rate limit)
end
```

### **Implementação em Python**:
```python
# src/rate_limit/atomic_operations.py
import asyncio
import aioredis

class AtomicRateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.lua_script = None

    async def _load_script(self):
        """Carregar script Lua para Redis"""
        lua_code = """
        local key = KEYS[1]
        local window_size = tonumber(ARGV[1])
        local rpm_limit = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        local request_id = ARGV[4]

        local cutoff = now - window_size
        redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)

        local count = redis.call('ZCARD', key)

        if count < rpm_limit then
            redis.call('ZADD', key, now, request_id)
            redis.call('EXPIRE', key, window_size)
            return 1
        else
            return 0
        end
        """
        self.lua_script = await self.redis.script_load(lua_code)

    async def acquire_slot_atomic(self, provider: str, window_size: int, rpm_limit: int) -> bool:
        """Operação atômica para adquirir slot no rate limiter"""
        if self.lua_script is None:
            await self._load_script()

        key = f"window:{provider}"
        now = time.time()
        request_id = str(uuid.uuid4())

        try:
            result = await self.redis.evalsha(
                self.lua_script,
                1,  # número de keys
                key,  # key
                window_size,  # argv[1]
                rpm_limit,    # argv[2]
                now,          # argv[3]
                request_id    # argv[4]
            )
            return bool(result)
        except aioredis.errors.NoScriptError:
            # Fallback se script não estiver carregado
            await self._load_script()
            return await self.acquire_slot_atomic(provider, window_size, rpm_limit)
```

### **Uso no CombinedRateLimiter**:
```python
# src/rate_limit/combined.py - linha 136
@asynccontextmanager
async def acquire(self, provider: str):
    # Substituir operação não-atômica por atômica
    config = self.get_provider_config(provider)

    # Usar operação atômica em vez de check_limit + add_request
    atomic_limiter = AtomicRateLimiter(self.redis)

    if not await atomic_limiter.acquire_slot_atomic(
        provider=provider,
        window_size=config.window_size,
        rpm_limit=config.rpm
    ):
        raise RateLimitError(
            provider=provider,
            message="Rate limit exceeded - operation would exceed atomic bounds"
        )

    # Resto da lógica...
```

---

## 2. **Token Bucket In-Memory - Thread Safety** (ALTO)

### **Problema**: Acesso a `self.last_refill` fora do lock

### **Solução**: Encapsular todos os acessos ao estado dentro do lock

```python
# src/rate_limit/token_bucket.py
@dataclass
class _InMemoryTokenBucket:
    capacity: float
    tokens: float
    refill_rate: float  # tokens per second
    window_size: int
    last_refill: float = field(default_factory=time.monotonic)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def _refill(self) -> None:
        """Refill method MUST be called within lock context"""
        now = time.monotonic()
        elapsed = now - self.last_refill
        if elapsed <= 0:
            return
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    async def request_delay(self) -> float:
        """Return 0 when token granted, or seconds to wait"""
        async with self.lock:
            # TODAS as operações de estado dentro do lock
            self._refill()  # Safe - called within lock

            if self.tokens >= 1:
                self.tokens -= 1
                return 0.0

            if self.refill_rate <= 0:
                return math.inf

            needed = 1 - self.tokens
            return needed / self.refill_rate

    async def get_available_tokens(self) -> int:
        """Thread-safe method to get available tokens"""
        async with self.lock:
            self._refill()
            return int(self.tokens)

    async def reset(self) -> None:
        """Thread-safe reset method"""
        async with self.lock:
            self.tokens = self.capacity
            self.last_refill = time.monotonic()
```

---

## 3. **Redis Operations - Consistency** (CRÍTICO)

### **Problema**: Operações Redis não atômicas

### **Solução**: Usar Redis Pipeline para operações atômicas

```python
# src/rate_limit/sliding_window.py
class SlidingWindowRateLimiter:
    async def add_request_atomic(self, provider: str, window_size: int = 60) -> bool:
        """
        Add request with atomic operation using Redis pipeline

        Returns:
            True if request was added, False if rate limit exceeded
        """
        key = f"window:{provider}"
        now = time.time()
        request_id = str(uuid.uuid4())

        # Usar pipeline para atomicidade
        pipe = self.redis.pipeline()
        pipe.multi()

        # Limpar entradas antigas
        cutoff = now - window_size
        pipe.zremrangebyscore(key, '-inf', cutoff)

        # Contar requests atuais
        pipe.zcard(key)

        # Adicionar novo request (executará depois do multi)
        pipe.zadd(key, {request_id: now})
        pipe.expire(key, window_size)

        try:
            results = await pipe.execute()
            # results[0] = cleanup count, results[1] = current count
            current_count = results[1]
            return current_count < self.rpm_limit  # Assuming rpm_limit is stored
        except Exception as e:
            logger.error(f"Atomic operation failed for {provider}: {e}")
            return False

    async def check_and_add_atomic(self, provider: str, rpm_limit: int, window_size: int = 60) -> bool:
        """Combined check and add operation - atomic"""
        if not self.redis:
            # Fallback to thread-safe memory implementation
            return await self._memory_check_and_add(provider, rpm_limit, window_size)

        return await self.add_request_atomic(provider, window_size)
```

---

## 4. **GlobalSemaphore Counters** (MÉDIO)

### **Problema**: Contadores não thread-safe

### **Solução**: Usar thread-safe counter e finally guarantee

```python
# src/rate_limit/semaphore.py
import threading
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class SemaphoreStats:
    active_count: int = 0
    total_acquired: int = 0
    total_queued: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)

class GlobalSemaphore:
    def __init__(self, max_concurrent: int = 12):
        if max_concurrent < 1:
            raise ValueError("max_concurrent must be >= 1")

        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.stats = SemaphoreStats()  # Thread-safe stats object

    @asynccontextmanager
    async def acquire(self):
        # Check if we'll need to wait
        if self.semaphore.locked():
            with self.stats.lock:
                self.stats.total_queued += 1
            logger.debug(f"Request queued, {self.stats.active_count}/{self.max_concurrent} slots in use")

        # Acquire semaphore (will block if at capacity)
        async with self.semaphore:
            # Use thread-safe counter increment
            with self.stats.lock:
                self.stats.active_count += 1
                self.stats.total_acquired += 1

            logger.debug(
                f"Semaphore acquired: {self.stats.active_count}/{self.max_concurrent} active"
            )

            try:
                yield
            except Exception as e:
                logger.error(f"Exception in semaphore context: {e}")
                raise
            finally:
                # GUARANTEED cleanup - never skip this
                with self.stats.lock:
                    self.stats.active_count -= 1
                logger.debug(
                    f"Semaphore released: {self.stats.active_count}/{self.max_concurrent} active"
                )

    def get_stats(self) -> dict:
        """Thread-safe stats access"""
        with self.stats.lock:
            return {
                'max_concurrent': self.max_concurrent,
                'active_count': self.stats.active_count,
                'available_slots': self.max_concurrent - self.stats.active_count,
                'total_acquired': self.stats.total_acquired,
                'total_queued': self.stats.total_queued,
                'is_at_capacity': self.stats.active_count >= self.max_concurrent
            }
```

---

## 5. **Provider Factory Thread Safety** (ALTO)

### **Problema**: Dictionary operations não thread-safe

### **Solução**: Usar threading.Lock para operações críticas

```python
# src/providers/factory.py
class ProviderFactory:
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self._lock = threading.RLock()  # Reentrant lock
        logger.info(f"Provider factory initialized with {len(self.PROVIDER_CLASSES)} provider types")

    def _get_providers_snapshot(self) -> Dict[str, LLMProvider]:
        """Thread-safe snapshot of providers"""
        with self._lock:
            return self.providers.copy()

    def get_provider(self, name: str) -> Optional[LLMProvider]:
        """Thread-safe provider access"""
        with self._lock:
            return self.providers.get(name)

    def _add_provider_locked(self, name: str, provider: LLMProvider):
        """Internal method called with lock held"""
        self.providers[name] = provider

    def create_provider(self, name: str, config_dict: dict) -> Optional[LLMProvider]:
        """Thread-safe provider creation"""
        with self._lock:  # Acquire lock for entire creation process
            try:
                # Build config
                config = ProviderConfig(name=name, **config_dict)

                # Check if provider is enabled
                if not config.enabled:
                    logger.info(f"Provider '{name}' is disabled, skipping")
                    return None

                # Get provider class
                provider_type = config.type
                provider_class = self.PROVIDER_CLASSES.get(provider_type)

                if not provider_class:
                    logger.warning(f"Unknown provider type '{provider_type}' for '{name}'")
                    return None

                # Create provider instance
                provider = provider_class(config)

                # Add to registry atomically
                self._add_provider_locked(name, provider)

                logger.info(f"Created provider: {name} ({provider_type}, model={config.model})")
                return provider

            except Exception as e:
                logger.error(f"Failed to create provider '{name}': {e}")
                return None
```

---

## 6. **Métricas Thread Safety** (MÉDIO)

### **Problema**: Operações de métricas concorrentes

### **Solução**: Usar queue-based ou async-safe metrics

```python
# src/metrics/thread_safe.py
import asyncio
from typing import Dict, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading

@dataclass
class ThreadSafeMetrics:
    """Thread-safe metrics collector using asyncio Queue"""

    metrics: Dict[str, Any] = field(default_factory=lambda: defaultdict(deque))
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)

    async def record_request_success(self, provider: str, agent: str):
        """Record success metric thread-safely"""
        await self.queue.put(('success', {'provider': provider, 'agent': agent}))

    async def record_latency(self, provider: str, agent: str, latency: float):
        """Record latency metric thread-safely"""
        await self.queue.put(('latency', {'provider': provider, 'agent': agent, 'latency': latency}))

    async def process_metrics_batch(self):
        """Background processor for metrics"""
        while True:
            try:
                batch = []
                # Collect batch (limit to avoid memory issues)
                for _ in range(100):  # Process up to 100 metrics at once
                    try:
                        item = await asyncio.wait_for(self.queue.get(), timeout=0.1)
                        batch.append(item)
                    except asyncio.TimeoutError:
                        break

                if batch:
                    await self._process_batch(batch)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing metrics batch: {e}")

    async def _process_batch(self, batch):
        """Process batch of metrics atomically"""
        async with self.lock:
            for metric_type, data in batch:
                if metric_type == 'success':
                    # Process success metric
                    key = f"success_{data['provider']}_{data['agent']}"
                    self.metrics[key].append(1)

                elif metric_type == 'latency':
                    # Process latency metric
                    key = f"latency_{data['provider']}_{data['agent']}"
                    self.metrics[key].append(data['latency'])

                    # Keep only last 1000 entries to prevent memory leaks
                    if len(self.metrics[key]) > 1000:
                        self.metrics[key] = deque(
                            list(self.metrics[key])[-1000:],
                            maxlen=1000
                        )

# Usage in orchestrator
class ThreadSafeOrchestratorMetrics:
    def __init__(self):
        self.metrics = ThreadSafeMetrics()
        # Start background processor
        asyncio.create_task(self.metrics.process_metrics_batch())

    async def record_execution_success(self, provider: str, agent: str, latency_ms: int):
        """Record success with multiple metrics atomically"""
        await asyncio.gather(
            self.metrics.record_request_success(provider, agent),
            self.metrics.record_latency(provider, agent, latency_ms / 1000.0),
            # Add more metrics as needed
        )
```

---

## 7. **Memory Store Thread Safety** (MÉDIO)

### **Problema**: Lista modifications não thread-safe

### **Solução**: Usar asyncio.Lock por provider

```python
# src/rate_limit/sliding_window.py
from dataclasses import dataclass, field
from typing import Dict, List
import asyncio

@dataclass
class MemoryWindowStore:
    """Thread-safe in-memory sliding window store"""

    stores: Dict[str, List[float]] = field(default_factory=dict)
    locks: Dict[str, asyncio.Lock] = field(default_factory=dict)

    async def _get_lock(self, provider: str) -> asyncio.Lock:
        """Get or create lock for provider"""
        if provider not in self.locks:
            self.locks[provider] = asyncio.Lock()
        return self.locks[provider]

    async def add_request(self, provider: str, timestamp: float, window_size: int):
        """Thread-safe add request"""
        lock = await self._get_lock(provider)

        async with lock:
            if provider not in self.stores:
                self.stores[provider] = []

            # Cleanup old entries
            cutoff = timestamp - window_size
            self.stores[provider] = [
                ts for ts in self.stores[provider] if ts > cutoff
            ]

            # Add new request
            self.stores[provider].append(timestamp)

    async def get_count(self, provider: str, window_size: int) -> int:
        """Thread-safe get count"""
        lock = await self._get_lock(provider)

        async with lock:
            if provider not in self.stores:
                return 0

            now = time.time()
            cutoff = now - window_size
            recent = [ts for ts in self.stores[provider] if ts > cutoff]
            return len(recent)

    async def reset(self, provider: str = None):
        """Thread-safe reset"""
        if provider:
            lock = await self._get_lock(provider)
            async with lock:
                self.stores.pop(provider, None)
        else:
            # Reset all - need to acquire all locks
            locks_to_reset = list(self.locks.values())
            await asyncio.gather(*[lock.acquire() for lock in locks_to_reset])

            try:
                self.stores.clear()
                self.locks.clear()
            finally:
                # Release all locks
                for lock in locks_to_reset:
                    lock.release()

class SlidingWindowRateLimiter:
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._use_memory = redis_client is None

        if self._use_memory:
            self.memory_store = MemoryWindowStore()
            logger.warning("Sliding window using thread-safe in-memory storage")
```

---

## **Resumo de Implementação**

### **Prioridade CRÍTICA** (Implementar primeiro):
1. ✅ **Rate Limiter Combinado** - Lua Script para operação atômica
2. ✅ **Redis Operations** - Pipeline para atomicidade

### **Prioridade ALTA** (Implementar segundo):
3. ✅ **Token Bucket** - Encapsular estado no lock
4. ✅ **Provider Factory** - Thread-safe operations

### **Prioridade MÉDIA** (Implementar terceiro):
5. ✅ **GlobalSemaphore** - Thread-safe counters
6. ✅ **Métricas** - Queue-based processing
7. ✅ **Memory Store** - Per-provider locks

### **Testing Strategy**:
```python
# tests/integration/test_race_conditions.py
import asyncio
import pytest

@pytest.mark.asyncio
async def test_concurrent_rate_limiting():
    """Test race conditions in rate limiting"""
    # Simular múltiplas threads fazendo requests simultâneos
    tasks = []
    for i in range(100):
        task = asyncio.create_task(make_request(f"user-{i}"))
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    # Verificar se rate limits foram respeitados
    assert all(result.success for result in results)

async def make_request(user_id: str):
    """Simular request que usa rate limiter"""
    # Implementar lógica de teste
    pass
```

### **Monitoring**:
- Adicionar métricas de race condition detections
- Logging especial para debugging
- Health checks para consistency

### **Rollback Plan**:
- Implementar feature flags para gradual deployment
- Manter versão original como fallback
- Monitoring intensivo durante rollout
