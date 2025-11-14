# Testing Real LLM Providers - Complete Guide

**🎯 Goal:** Validate that Squad API works with real LLM providers (Groq, Gemini, etc.)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ⏱️ Time Required: 15-30 minutes

- API Key Setup: 10 min
- Provider Testing: 5 min
- Chat with Mary: 5-15 min

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📋 Prerequisites

✅ Python 3.11+ installed  
✅ Virtual environment activated  
✅ Dependencies installed (`pip install -r requirements.txt`)  
✅ Internet connection  
✅ Free LLM provider accounts (Groq, Gemini, etc.)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🚀 Step-by-Step Guide

### Step 1: Get API Keys (10 min)

**1.1 Groq (RECOMENDADO - Mais rápido!)** ⭐

1. Acesse: https://console.groq.com/
2. Click "Sign Up" ou "Log In" (pode usar Google/GitHub)
3. Após login, vá para "API Keys"
4. Click "Create API Key"
5. Nome: "squad-api-dev"
6. Click "Submit"
7. **COPIE A KEY!** (começa com `gsk_...`)
8. ⚠️ **Guarde em local seguro** (só mostra uma vez!)

**1.2 Google Gemini (RECOMENDADO - Mais versátil!)** ⭐

1. Acesse: https://aistudio.google.com/apikey
2. Login com sua conta Google
3. Click "Get API key" ou "Create API key"
4. Escolha um projeto Google Cloud (ou crie novo)
5. **COPIE A KEY!** (começa com `AIza...`)

**1.3 Cerebras (OPCIONAL - Ultra rápido!)** 

1. Acesse: https://cloud.cerebras.ai/
2. Sign up for Beta
3. Aguarde aprovação (geralmente instantânea)
4. Navigate to API Keys
5. Create key
6. **COPIE A KEY!**

**1.4 OpenRouter (OPCIONAL - Diversidade!)** 

1. Acesse: https://openrouter.ai/
2. Sign up
3. Settings → API Keys
4. Create new key
5. **COPIE A KEY!**

---

### Step 2: Configure `.env` File (2 min)

```bash
# 1. Copy template
cp .env.example .env

# 2. Edit .env with your favorite editor
code .env  # VS Code
notepad .env  # Notepad
vim .env  # Vim
```

**Paste your keys:**
```bash
# Minimal setup (2 providers)
GROQ_API_KEY=gsk_YOUR_KEY_HERE
GEMINI_API_KEY=AIzaYOUR_KEY_HERE

# Full setup (4 providers)
GROQ_API_KEY=gsk_YOUR_KEY_HERE
CEREBRAS_API_KEY=YOUR_KEY_HERE
GEMINI_API_KEY=AIzaYOUR_KEY_HERE
OPENROUTER_API_KEY=YOUR_KEY_HERE
```

**3. Verify keys are loaded:**
```powershell
# Windows PowerShell
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Groq:', 'OK' if os.getenv('GROQ_API_KEY') else 'NOT SET'); print('Gemini:', 'OK' if os.getenv('GEMINI_API_KEY') else 'NOT SET')"
```

**Expected output:**
```
Groq: OK
Gemini: OK
```

---

### Step 3: Test Providers (3 min)

**3.1 Test all configured providers:**
```bash
# Activate venv first!
venv\Scripts\Activate.ps1  # Windows

# Run provider tests
python scripts/test_providers.py --all
```

**Expected output:**
```
============================================================
        SQUAD API - PROVIDER TEST SUITE
============================================================

✅ Loaded 4 providers from config

Testing: groq
----------------------------------------
ℹ️  API key found: GROQ_API_KEY
ℹ️  Model: llama-3.1-70b-versatile
ℹ️  RPM Limit: 30

Test 1: Health Check...
✅ Health check passed (1234ms)

Test 2: Simple LLM Call...
✅ Call successful (2345ms)
ℹ️  Response: Hello from Squad API!
ℹ️  Tokens: 25 in, 8 out
ℹ️  Finish Reason: stop

Testing: gemini
----------------------------------------
[... similar output ...]

============================================================
                    TEST SUMMARY
============================================================

Providers tested: 4
  ✅ Configured: 4
  ✅ Healthy: 4
  ✅ Tests passed: 4

🎉 ALL PROVIDERS WORKING!
ℹ️  You're ready to use Squad API!

Provider Details:
  ✅ groq         - Latency: 2345ms
  ✅ cerebras     - Latency: 891ms
  ✅ gemini       - Latency: 1567ms
  ✅ openrouter   - Latency: 2100ms
```

**3.2 Test specific provider (faster):**
```bash
python scripts/test_providers.py --provider groq
```

---

### Step 4: Chat with Mary! (Interactive) 🎉

**4.1 Start chat session:**
```bash
python scripts/chat_with_mary.py
```

**4.2 Expected output:**
```
╔══════════════════════════════════════════════════════════╗
║         🤖 SQUAD API - Chat with Mary & Team            ║
╚══════════════════════════════════════════════════════════╝

🔧 Initializing Squad API...
  → Loading agents from .bmad/...
    ✓ 8 agents loaded
  → Loading LLM providers...
    ✓ 2 providers configured: ['groq', 'gemini']
  → Setting up rate limiting...
    ✓ Rate limiting configured
  → Setting up fallback chains...
    ✓ Fallback chains ready

✅ Squad API initialized!

You are chatting with: Mary - Business Analyst
Agent: analyst
Persona: Expert business analyst focused on requirements...
Providers: ['groq', 'gemini']

Commands:
  /help    - Show help
  /agents  - List all agents
  /stats   - Show conversation stats
  /quit    - Exit chat

Start chatting! (Press Ctrl+C or type '/quit' to exit)
────────────────────────────────────────────────────────────

Dani> Hello Mary! What can you help me with?

🤖 analyst is thinking...

Mary> Hello Dani! I'm Mary, your Business Analyst. I can help you with:
1. Requirements analysis and elicitation
2. Stakeholder identification
3. User story creation
4. Acceptance criteria definition
5. PRD and technical specification review
...

[groq/llama-3.1-70b-versatile • 2340ms • 450→187 tokens]
────────────────────────────────────────────────────────────

Dani> Can you review our current sprint status?

🤖 analyst is thinking...

Mary> Let me analyze the current sprint status...
[Response from Mary analyzing the sprint...]

[groq/llama-3.1-70b-versatile • 1890ms • 520→234 tokens]
────────────────────────────────────────────────────────────

Dani> /quit

Goodbye! 👋
```

**4.3 Chat with different agents:**
```bash
# Chat with John (Dev agent)
python scripts/chat_with_mary.py --agent dev

# Chat with Alex (Architect)
python scripts/chat_with_mary.py --agent architect

# Chat with PM
python scripts/chat_with_mary.py --agent pm
```

---

## 🧪 Test Scenarios

### Scenario 1: Basic Functionality
```
Goal: Verify agent responds correctly

Steps:
1. python scripts/chat_with_mary.py
2. Dani> "What is your name and role?"
3. Verify Mary responds with analyst persona
4. /quit

Expected: ✅ Mary responds as Business Analyst
```

### Scenario 2: Fallback Chain
```
Goal: Verify fallback works when primary fails

Steps:
1. Temporarily disable Groq (comment out GROQ_API_KEY in .env)
2. python scripts/chat_with_mary.py
3. Ask Mary a question
4. Verify response comes from Gemini (fallback provider)

Expected: ✅ Fallback to Gemini works automatically
```

### Scenario 3: Rate Limiting
```
Goal: Verify rate limiting prevents 429 errors

Steps:
1. Make 35 rapid requests (exceed 30 RPM limit)
2. Observe rate limiting delays
3. Verify no 429 errors in logs

Expected: ✅ Requests delayed, no 429 errors
```

### Scenario 4: Multi-Turn Conversation
```
Goal: Verify conversation history works

Steps:
1. python scripts/chat_with_mary.py
2. Dani> "Remember my name is Dani"
3. Mary> "Of course, Dani! ..."
4. Dani> "What's my name?"
5. Mary> "Your name is Dani" (remembers!)

Expected: ✅ Conversation history maintained
```

---

## 📊 Performance Expectations

### Latency (with real providers)
- **Groq (70B):** 1.5-3s (very fast for 70B!)
- **Cerebras (8B):** 0.5-1.5s (ultra-fast!)
- **Gemini (Flash):** 1-2.5s (balanced)
- **OpenRouter (9B):** 2-4s (varies)

### With Rate Limiting Overhead
- **Additional:** +50-100ms (negligible)
- **With Fallback:** +1-2s (only if primary fails)

### Throughput (Aggregated)
- **Single Provider:** 15-30 RPM
- **Multi-Provider:** 95 RPM (2 providers minimum)
- **With Fallback:** 99.5%+ availability

---

## ✅ Success Criteria

After completing this guide, you should have:

- ✅ At least 2 providers working (Groq + Gemini recommended)
- ✅ Successfully chatted with Mary (analyst agent)
- ✅ Verified conversation history works
- ✅ Observed rate limiting in action
- ✅ Tested fallback chain (optional)

---

## 🆘 Common Issues

### Issue: "API key not found"
**Solution:** 
```bash
# Verify .env exists
ls .env

# Check it's loaded
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('GROQ_API_KEY'))"

# If empty, edit .env and add your key
```

### Issue: "Provider timeout"
**Solution:**
```bash
# Check internet connection
# Try different provider
python scripts/test_providers.py --provider gemini
```

### Issue: "All providers failed"
**Solution:**
```bash
# Check all API keys are valid
# Verify provider dashboards are accessible
# Check rate limits not exceeded
# Wait 1 minute and retry
```

---

## 🎯 Next Steps

After successful testing:

1. **Production Setup:**
   - Get production API keys (separate from dev)
   - Configure rate limits for production
   - Setup monitoring alerts

2. **Advanced Features:**
   - Test fallback chains with multiple agents
   - Test quality escalation (worker → boss)
   - Test auto-throttling (simulate 429 errors)

3. **Integration:**
   - Connect to real Redis (not in-memory)
   - Setup PostgreSQL for audit logs
   - Configure Grafana dashboards

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**🎊 Congratulations!**

You've successfully configured and tested Squad API with real LLM providers!

**Mary is now ALIVE! 🤖✨**

