# API Keys Setup Guide

**🔑 Como obter e configurar API keys para os providers LLM**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📋 Overview

Squad API suporta 8+ providers (todos com free tier):

| Provider | Model | Free Tier | Qualidade | Velocidade | Prioridade |
|----------|-------|-----------|-----------|------------|------------|
| **Groq** | Llama-3.1-70B | 30 RPM | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | HIGH |
| **Gemini** | Gemini-2.0-Flash | 15 RPM | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | HIGH |
| **OpenRouter-Chimera** | DeepSeek-R1T2 (671B) | 20 RPM | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | HIGH |
| **OpenRouter-GPT-OSS** | GPT-OSS-120B | 20 RPM | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | HIGH |
| **OpenRouter-Qwen3** | Qwen3-Coder | 20 RPM | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | HIGH |
| **OpenRouter-Gemini** | Gemini-2.0-Flash-Exp | 20 RPM | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | HIGH |
| **OpenRouter-R1** | DeepSeek-R1 | 20 RPM | ⭐⭐⭐⭐ | ⭐⭐⭐ | HIGH |
| **Cerebras** | Llama-3.1-8B | 30 RPM | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | MEDIUM |

**Recomendação:** Configure **Groq** + **Gemini** + **OpenRouter** (all free!) para máxima flexibilidade e 7+ modelos diferentes!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🚀 Quick Start (5 minutos)

### 1. Copiar template
```bash
cp .env.example .env
```

### 2. Obter API keys (escolha 1 ou mais)

**Groq (RECOMENDADO)** ⭐
1. Acesse: https://console.groq.com/
2. Login com Google/GitHub
3. Clique em "API Keys"
4. Criar nova key: "squad-api-dev"
5. Copiar key (começa com `gsk_...`)

**Gemini (RECOMENDADO)** ⭐
1. Acesse: https://aistudio.google.com/apikey
2. Login com conta Google
3. Clique em "Get API key"
4. Criar nova key: "squad-api"
5. Copiar key (começa com `AIza...`)

**Cerebras (OPCIONAL)**
1. Acesse: https://cloud.cerebras.ai/
2. Login/Signup (Beta program)
3. Navigate to API Keys
4. Create key: "squad-api"
5. Copiar key

**OpenRouter (RECOMENDADO)** ⭐
1. Acesse: https://openrouter.ai/
2. Login/Signup (30 segundo signup)
3. Settings → API Keys
4. Create key: "squad-api"
5. Copiar key
6. **Bônus:** 2 modelos free extras agora disponíveis!
   - Qwen3-Coder (qwen/qwen3-coder:free)
   - Gemini-2.0-Flash-Exp (google/gemini-2.0-flash-exp:free)

### 3. Configurar `.env`
```bash
# Editar .env e colar suas keys
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AIza...
CEREBRAS_API_KEY=...
OPENROUTER_API_KEY=...
```

### 4. Testar!
```bash
# Ativar venv
venv\Scripts\Activate.ps1

# Rodar script de teste
python scripts/test_providers.py
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📝 Provider Details

### Groq (Llama-3-70B-Versatile)

**Specs:**
- Model: `llama-3.1-70b-versatile`
- RPM Limit: 30 (free tier)
- Context: 8K tokens
- Speed: ⚡ ULTRA-FAST (LPU acceleration)
- Quality: ⭐⭐⭐⭐⭐ (70B parameters)

**Sign Up:**
1. Go to: https://console.groq.com/
2. Click "Sign Up" (GitHub/Google login)
3. Verify email
4. Create API key (free tier auto-enabled)

**Free Tier Limits:**
- 30 requests per minute
- 14,400 requests per day
- 20,000 tokens per minute
- No credit card required ✅

---

### Google Gemini (Gemini 2.0 Flash)

**Specs:**
- Model: `gemini-2.0-flash-exp`
- RPM Limit: 15 (free tier)
- Context: 1M tokens (!)
- Speed: ⚡ VERY FAST
- Quality: ⭐⭐⭐⭐⭐ (multimodal)

**Sign Up:**
1. Go to: https://aistudio.google.com/apikey
2. Login with Google account
3. Click "Get API key"
4. Create key for new/existing project

**Free Tier Limits:**
- 15 requests per minute
- 1,500 requests per day
- 1,000,000 tokens per minute
- No credit card required ✅

---

### Cerebras (Llama-3-8B)

**Specs:**
- Model: `llama3.1-8b`
- RPM Limit: 30 (free tier)
- Context: 8K tokens
- Speed: ⚡⚡⚡ FASTEST (specialized hardware)
- Quality: ⭐⭐⭐ (8B parameters)

**Sign Up:**
1. Go to: https://cloud.cerebras.ai/
2. Sign up for Beta program
3. Wait for approval (usually instant)
4. Create API key

**Free Tier Limits:**
- 30 requests per minute
- 14,400 requests per day
- 180,000 tokens per minute
- Beta access (free) ✅

---

### OpenRouter (Gemma-2-9B)

**Specs:**
- Model: `google/gemma-2-9b-it:free`
- RPM Limit: 20 (free tier)
- Context: 8K tokens
- Speed: ⭐⭐⭐
- Quality: ⭐⭐⭐ (9B parameters)

**Sign Up:**
1. Go to: https://openrouter.ai/
2. Sign up (email or OAuth)
3. Settings → API Keys
4. Create key

**Free Tier Limits:**
- 20 requests per minute
- 200,000 tokens per minute
- Multiple free models available
- No credit card required ✅

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🧪 Testing Your Setup

### Quick Test (CLI)
```bash
# Test Groq
python scripts/test_providers.py --provider groq

# Test Gemini
python scripts/test_providers.py --provider gemini

# Test all configured providers
python scripts/test_providers.py --all
```

### Interactive Test (Chat with Mary)
```bash
# Start interactive session
python scripts/chat_with_mary.py

# Or test specific agent
python scripts/chat_with_mary.py --agent analyst
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🔒 Security Best Practices

### ✅ DO:
- ✅ Keep `.env` in `.gitignore` (already configured)
- ✅ Use separate keys for dev/staging/prod
- ✅ Rotate keys periodically (every 90 days)
- ✅ Monitor API usage in provider dashboards
- ✅ Set rate limit alerts

### ❌ DON'T:
- ❌ Commit `.env` file to Git
- ❌ Share API keys in Slack/email
- ❌ Use production keys in development
- ❌ Hard-code keys in source code
- ❌ Ignore rate limit warnings

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🆘 Troubleshooting

### "API key invalid"
```bash
# Check key format
# Groq: should start with "gsk_"
# Gemini: should start with "AIza"

# Verify .env is loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GROQ_API_KEY'))"
```

### "Rate limit exceeded immediately"
```bash
# Check your daily quota in provider dashboard
# Wait 1 minute and try again
# Consider adding more providers for higher throughput
```

### "Provider timeout"
```bash
# Check internet connection
# Check provider status page
# Try different provider
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📊 Cost Analysis (Free Tier)

| Provider | Free Tier | Cost if Upgrade | Est. Monthly (Free) |
|----------|-----------|-----------------|---------------------|
| Groq | Free forever | N/A | $0 |
| Gemini | Free tier | $0.35/1M input tokens | $0 (under limit) |
| Cerebras | Beta (free) | TBD | $0 |
| OpenRouter (5 modelos!) | Free models | Varies by model | $0 |

**Total Cost (Free Tier):** $0/month ✅ (9+ models available!)

**If Scaling Beyond Free Tier:**
- Groq: Consider paid tier (if available)
- Gemini: ~$10-20/month for moderate usage
- Cerebras: TBD (post-beta pricing)
- Together AI: $5 minimum deposit

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🆕 New: OpenRouter Free Models (November 2025)

**4 novos modelos free agora disponíveis via OpenRouter:**

### 1. DeepSeek R1T2 Chimera (671B MoE - ULTRA POWERFUL!)
```yaml
Model: tngtech/deepseek-r1t2-chimera:free
Provider: openrouter-deepseek-chimera
RPM Limit: 20
Quality: ⭐⭐⭐⭐⭐ (enormous 671B model!)
Speed: ⭐⭐⭐ (slower but most powerful)
Cost: $0/month
Best for: Complex reasoning, high-quality outputs
```

### 2. GPT-OSS-120B (OpenAI Open Source - 117B MoE)
```yaml
Model: openai/gpt-oss-120b:free
Provider: openrouter-gpt-oss
RPM Limit: 20
Quality: ⭐⭐⭐⭐ (strong performance)
Speed: ⭐⭐⭐⭐ (good balance)
Cost: $0/month
Best for: General purpose, balanced performance
```

### 3. Qwen3-Coder (Free)
```yaml
Model: qwen/qwen3-coder:free
Provider: openrouter-qwen3
RPM Limit: 20
Quality: ⭐⭐⭐⭐ (excellent for coding)
Speed: ⭐⭐⭐⭐
Cost: $0/month
Best for: Code generation, technical tasks
```

### 4. Gemini-2.0-Flash-Experimental (Free)
```yaml
Model: google/gemini-2.0-flash-exp:free
Provider: openrouter-gemini-flash
RPM Limit: 20
Quality: ⭐⭐⭐⭐⭐ (latest experimental)
Speed: ⭐⭐⭐⭐
Cost: $0/month
Best for: Fast, high-quality responses

### 5. DeepSeek-R1 (Free - Reasoning Model)
```yaml
Model: deepseek/deepseek-r1:free
Provider: openrouter-deepseek-r1
RPM Limit: 20
Quality: ⭐⭐⭐⭐ (strong reasoning)
Speed: ⭐⭐⭐ (reasoning takes time)
Cost: $0/month
Best for: Problem-solving, step-by-step reasoning
```

**Configuration (already added):**
```yaml
# config/providers.yaml
openrouter-deepseek-chimera:
  model: "tngtech/deepseek-r1t2-chimera:free"
  enabled: true

openrouter-gpt-oss:
  model: "openai/gpt-oss-120b:free"
  enabled: true

openrouter-qwen3:
  model: "qwen/qwen3-coder:free"
  enabled: true

openrouter-gemini-flash:
  model: "google/gemini-2.0-flash-exp:free"
  enabled: true

openrouter-deepseek-r1:
  model: "deepseek/deepseek-r1:free"
  enabled: true
```

**Enable in .env:**
```bash
OPENROUTER_API_KEY=sk-or-...
# That's it! All 5 models are now available
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎯 Recommended Setup

### Minimal (Start Here):
```bash
GROQ_API_KEY=gsk_...        # Best quality + speed
GEMINI_API_KEY=AIza...      # Backup + reliability
```

### Recommended (Production):
```bash
GROQ_API_KEY=gsk_...              # Primary (Boss tier)
CEREBRAS_API_KEY=...              # Worker tier (fast)
GEMINI_API_KEY=AIza...            # Backup (reliable)
OPENROUTER_API_KEY=sk-or-...      # Diversity (5 free models: Chimera, GPT-OSS, Qwen3, Gemini-2.0-Flash-Exp, DeepSeek-R1)
```

### Maximum (All Providers):
```bash
GROQ_API_KEY=gsk_...
CEREBRAS_API_KEY=...
GEMINI_API_KEY=AIza...
OPENROUTER_API_KEY=sk-or-...      # Enables: 5 free models + auto-router
DEEPSEEK_API_KEY=...              # Optional
TOGETHER_API_KEY=...              # Optional (paid)
```

---

## 📊 Provider Comparison Matrix

| Criteria | Groq | Gemini | Chimera | GPT-OSS | Qwen3 | Gemini-Flash-Exp | DeepSeek-R1 | Cerebras |
|----------|------|--------|---------|---------|-------|------------------|-------------|----------|
| Quality | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Speed | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| RPM | 30 | 15 | 20 | 20 | 20 | 20 | 20 | 30 |
| Size | 70B | Varies | 671B | 117B | Large | Varies | Large | 8B |
| Best For | General | Balanced | Heavy reasoning | General | Coding | Fast balanced | Reasoning | Speed |
| Cost | $0 | $0 | $0 | $0 | $0 | $0 | $0 | $0 |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Next:** I'll create the test scripts for you! 🚀

