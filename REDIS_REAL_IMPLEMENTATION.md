# Redis - De MOCKADO para REAL

## O PROBLEMA

**ANTES:** Redis estava passando como `None` em todos os componentes:
```python
# src/main.py (ERRADO)
agent_loader = AgentLoader(bmad_path=".bmad", redis_client=None)        # ❌ Mock!
conversation_manager = ConversationManager(redis_client=None)            # ❌ Mock!
```

### Por quê estava mockado?
1. **Falta de Redis rodando** - Não havia servidor Redis ativo
2. **Não era inicializado** - Código não tentava conectar ao Redis
3. **Design permissivo** - Era opcional ("para testing"), mas deveria ser padrão

### Impacto:
- ❌ Conversation history NÃO era persistida
- ❌ Multi-turn conversations perdiam contexto
- ❌ Cache de agents não funcionava
- ❌ In-memory only (perdido ao reiniciar)

---

## A SOLUÇÃO

### 1️⃣ Adicionar import Redis
```python
import redis.asyncio as redis
```

### 2️⃣ Inicializar Redis no startup
```python
redis_client = None
try:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    await redis_client.ping()
    print("[OK] Redis connected successfully")
except Exception as e:
    logger.warning(f"[WARN] Redis connection failed: {e}")
    print("[WARN] Continuing with in-memory conversation cache")
    redis_client = None
```

### 3️⃣ Passar Redis REAL para componentes
```python
# ANTES (MOCKADO):
agent_loader = AgentLoader(bmad_path=".bmad", redis_client=None)
conversation_manager = ConversationManager(redis_client=None)

# DEPOIS (REAL):
agent_loader = AgentLoader(bmad_path=".bmad", redis_client=redis_client)
conversation_manager = ConversationManager(redis_client=redis_client)
```

### 4️⃣ Fechar Redis no shutdown
```python
# Shutdown
if redis_client:
    await redis_client.close()
    print("[OK] Redis connections closed")
```

---

## ATIVANDO REDIS

### Opção 1: Docker (Recomendado - Produção)
```bash
docker-compose up -d redis
# Verificar: docker ps | grep redis
```

### Opção 2: Redis Local (Desenvolvimento Windows)
```bash
# Via Windows Subsystem for Linux (WSL)
wsl sudo service redis-server start

# Ou via Chocolatey
choco install redis-64

# Ou compilar do Windows Native
# https://github.com/microsoftarchive/redis/releases
```

### Opção 3: Variável de ambiente customizada
```bash
set REDIS_URL=redis://username:password@hostname:port/db
```

---

## VERIFICANDO SE REDIS ESTÁ RODANDO

```python
python -c "
import redis.asyncio as redis
import asyncio

async def test():
    r = redis.from_url('redis://localhost:6379')
    await r.ping()
    print('[OK] Redis is running!')
    await r.close()

asyncio.run(test())
"
```

---

## COMPONENTES AGORA REAIS

| Componente | Status | O que faz |
|-----------|--------|----------|
| AgentLoader | ✅ REAL | Carrega agents do .bmad com cache Redis |
| ConversationManager | ✅ REAL | Persiste histórico de conversas no Redis |
| Rate Limiter | ✅ REAL | Armazena estado em Redis |
| PostgreSQL | ✅ REAL | Audit logging |
| Provider Calls | ✅ REAL (com API keys) | Chamar APIs reais (Groq, Gemini, etc) |

---

## PRÓXIMOS PASSOS

1. **Iniciar Redis:**
   - Via Docker: `docker-compose up -d redis`
   - Ou nativo no sistema

2. **Reiniciar Squad API:**
   - Verá `[OK] Redis connected successfully`

3. **Testar conversation persistence:**
   - Fazer multi-turn com mesmo user_id
   - Histórico será mantido através de requisições

---

## DETALHES TÉCNICOS

### Redis Configuration
- **Host:** localhost (ou variável `REDIS_URL`)
- **Port:** 6379 (padrão)
- **DB:** 0 (default)
- **TTL:** 1 hora inatividade (configurável em ConversationManager)
- **Max Messages:** 50 por conversa (sliding window)

### Fallback Behavior
Se Redis falhar:
1. Tenta conectar
2. Se falhar, continua com **in-memory only**
3. Aviso é printado
4. Conversas perdidas ao reiniciar

### Memory Strategy
- Redis é usado para:
  - Histórico de conversas (chave: `conv:{user_id}:{agent_id}`)
  - Cache de agents (chave: `agent:{agent_id}`)
  - State de rate limiting (chave: `rl:{provider}:{time_window}`)

---

## MUDANÇAS NO CÓDIGO

### Arquivo: `src/main.py`

1. **Line 12:** Adicionado `import redis.asyncio as redis`
2. **Lines 73-84:** Novo bloco de inicialização Redis
3. **Line 86:** Changed: `redis_client=redis_client` (não mais `None`)
4. **Line 88:** Changed: `redis_client=redis_client` (não mais `None`)
5. **Lines 143-145:** Novo bloco de shutdown Redis

---

## PRÓXIMAS ÉPICAS

- **Epic 1.5:** Conversation State Manager (AGORA REAL!)
- **Epic 2.x:** Rate Limiting com Redis (AGORA REAL!)
- **Epic 3.x:** Provider failover com estado compartilhado
