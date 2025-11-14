# Scripts - Testing & Utilities

## 🧪 Testing Real Providers

### 1. Pre-Commit Safety Check ⭐ **USE SEMPRE!**

**Windows:**
```powershell
.\scripts\pre-commit-check.ps1
```

**Linux/Mac:**
```bash
./scripts/pre-commit-check.sh
```

**What it does:**
- ✅ Runs linting (ruff)
- ✅ Checks formatting (black)
- ✅ Type checking (mypy)
- ✅ Runs unit tests
- ✅ Validates coverage >= 70%

**When to use:** Before EVERY commit!

---

### 2. Test LLM Providers

**Test all providers:**
```bash
python scripts/test_providers.py --all
```

**Test specific provider:**
```bash
python scripts/test_providers.py --provider groq
python scripts/test_providers.py --provider gemini
python scripts/test_providers.py --provider cerebras
```

**What it does:**
- ✅ Checks API key configuration
- ✅ Runs health check
- ✅ Makes test LLM call
- ✅ Measures latency
- ✅ Validates response

**When to use:** After configuring API keys, before first real usage

---

### 3. Chat with Mary (Interactive)

**Chat with default agent (Analyst/Mary):**
```bash
python scripts/chat_with_mary.py
```

**Chat with specific agent:**
```bash
python scripts/chat_with_mary.py --agent pm
python scripts/chat_with_mary.py --agent dev
python scripts/chat_with_mary.py --agent architect
```

**Custom user name:**
```bash
python scripts/chat_with_mary.py --user "Your Name"
```

**What it does:**
- ✅ Loads agent from `.bmad/bmm/agents/`
- ✅ Builds system prompt (persona + rules)
- ✅ Connects to real LLM providers
- ✅ Maintains conversation history
- ✅ Shows latency and token usage

**Commands in chat:**
- `/help` - Show help
- `/agents` - List all agents
- `/stats` - Show conversation stats
- `/quit` - Exit chat

**When to use:** To test agent transformation with real LLMs

---

## 📋 Complete Setup Checklist

### Step 1: Configure API Keys (5 min)

```bash
# 1. Copy template
cp .env.example .env

# 2. Edit .env and add your API keys
# Get keys from:
#   - Groq: https://console.groq.com/
#   - Gemini: https://aistudio.google.com/apikey
#   - Cerebras: https://cloud.cerebras.ai/
#   - OpenRouter: https://openrouter.ai/

# 3. Verify keys are set
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Groq:', 'OK' if os.getenv('GROQ_API_KEY') else 'NOT SET')"
```

### Step 2: Test Providers (2 min)

```bash
# Activate venv
venv\Scripts\Activate.ps1  # Windows
# source venv/bin/activate  # Linux/Mac

# Test all providers
python scripts/test_providers.py --all
```

**Expected output:**
```
Testing: groq
✅ Health check passed (1234ms)
✅ Call successful (2345ms)

Testing: gemini
✅ Health check passed (1500ms)
✅ Call successful (2100ms)

TEST SUMMARY
✅ 2/2 providers working
🎉 ALL PROVIDERS WORKING!
```

### Step 3: Chat with Mary! (∞)

```bash
# Start interactive session
python scripts/chat_with_mary.py

# Chat with Mary (Analyst agent)
Dani> Hello Mary! Can you help me analyze this codebase?

🤖 Mary> [Agent responds via Groq Llama-3-70B...]

Dani> /quit
```

---

## 🔧 Troubleshooting

### "ModuleNotFoundError: No module named 'dotenv'"
```bash
# Install dependencies
pip install -r requirements.txt
```

### "No providers configured"
```bash
# Check .env file exists
ls .env

# Verify API keys are set
cat .env | grep API_KEY

# If .env doesn't exist
cp .env.example .env
# Then edit .env and add your keys
```

### "API key invalid"
```bash
# Check key format:
# Groq: starts with "gsk_"
# Gemini: starts with "AIza"

# Test in provider dashboard
# Groq: https://console.groq.com/playground
# Gemini: https://aistudio.google.com/
```

### "Rate limit exceeded immediately"
```bash
# Check daily quota in provider dashboard
# Wait 1 minute and try again
# Consider adding more providers
```

---

## 📊 Script Output Examples

### Successful Provider Test
```
🔍 PRE-COMMIT SAFETY CHECK
==========================

📝 Step 1/5: Running linters...
✅ Linting passed

🎨 Step 2/5: Checking code formatting...
✅ Formatting OK

🔬 Step 3/5: Type checking...
⚠️  Type check warnings (non-blocking)

🧪 Step 4/5: Running unit tests...
✅ Unit tests passed

📊 Step 5/5: Checking test coverage...
✅ Coverage OK

✨ ALL CHECKS PASSED! Safe to commit.
```

### Chat Session Example
```
╔══════════════════════════════════════════════════════════╗
║         🤖 SQUAD API - Chat with Mary & Team            ║
╚══════════════════════════════════════════════════════════╝

You are chatting with: Mary - Business Analyst
Agent: analyst
Providers: ['groq', 'gemini', 'cerebras']

Dani> What is the current sprint status?

🤖 analyst is thinking...

Mary> Based on the workflow status, we have completed Epic 0, 1, 2, 3, and 4...

[groq/llama-3.1-70b-versatile • 2340ms • 450→120 tokens]
```

---

## 🚀 Development Workflow

### Daily Development
```bash
# 1. Write tests
pytest tests/unit/test_new_feature.py -v -x

# 2. Implement feature
# ... code ...

# 3. Run pre-commit check
.\scripts\pre-commit-check.ps1

# 4. Commit
git add .
git commit -m "feat: Add new feature"
```

### Testing New Provider
```bash
# 1. Add API key to .env
echo "NEW_PROVIDER_API_KEY=xxx" >> .env

# 2. Update config/providers.yaml
# ... add provider config ...

# 3. Test provider
python scripts/test_providers.py --provider new_provider

# 4. Chat test
python scripts/chat_with_mary.py
```

---

## 📚 References

- **API Keys Setup:** `docs/API-KEYS-SETUP.md`
- **Safe Workflow:** `docs/SAFE-DEVELOPMENT-WORKFLOW.md`
- **Visual Guide:** `docs/WORKFLOW-VISUAL-GUIDE.md`
- **Architecture:** `docs/architecture.md`

---

**🎯 Quick Links:**
- Get Groq Key: https://console.groq.com/
- Get Gemini Key: https://aistudio.google.com/apikey
- Get Cerebras Key: https://cloud.cerebras.ai/
- Get OpenRouter Key: https://openrouter.ai/

