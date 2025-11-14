# Squad API - Endpoints Reference

## 🎯 Base URL
```
http://localhost:8000
```

---

## 🔥 Core Endpoints

### Health Check
```http
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "service": "squad-api",
  "version": "1.0.0"
}
```

### List Available Agents
```http
GET /v1/agents
```
**Response:**
```json
{
  "count": 13,
  "agents": [
    {
      "id": "code",
      "name": "CodeMaster",
      "description": "Expert in programming, debugging, and code review",
      "capabilities": ["Python", "JavaScript", "Java", "Code Review", "Debugging"]
    },
    {
      "id": "architect",
      "name": "Architecture Expert",
      "description": "System architecture and design specialist",
      "capabilities": ["System Design", "Architecture", "Scalability"]
    }
    // ... more agents
  ]
}
```

---

## 🚀 Agent Execution Endpoints

### Execute Specific Agent
```http
POST /v1/agents/{agent_name}
```

**Available Agents:**
- `code` - Programming and code generation
- `architect` - System design and architecture
- `analyst` - Business analysis and research
- `creative` - Content creation and copywriting
- `debug` - Troubleshooting and debugging
- `data` - Data analysis and visualization
- `pm` - Project management and planning
- `tech-writer` - Technical documentation

**Request Body:**
```json
{
  "prompt": "Write a Python function to calculate fibonacci numbers",
  "conversation_id": "optional-conversation-id",
  "metadata": {
    "user_id": "user@example.com"
  }
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:8000/v1/agents/code \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a Python function to calculate fibonacci numbers",
    "conversation_id": "test-123"
  }'
```

**Success Response:**
```json
{
  "response": "Here's a Python function to calculate Fibonacci numbers:\n\n```python\ndef fibonacci(n):\n    if n <= 0:\n        return 0\n    elif n == 1:\n        return 1\n    else:\n        return fibonacci(n-1) + fibonacci(n-2)\n```",
  "provider": "groq",
  "model": "llama-3.1-70b-versatile",
  "conversation_id": "test-123",
  "metadata": {
    "fallback_used": false,
    "processing_time_ms": 234,
    "tokens_used": 150,
    "rate_limit_remaining": 45
  }
}
```

---

## 📊 Additional Endpoints

### Metrics (Prometheus)
```http
GET /metrics
```

### API Documentation
```http
GET /docs
```
Interactive Swagger UI with all endpoints

---

## 🛠️ Common Usage Patterns

### Simple Request
```bash
curl -X POST http://localhost:8000/v1/agents/dev \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a REST API for user management"}'
```

### Multi-Turn Conversation
```bash
# First request
curl -X POST http://localhost:8000/v1/agents/code \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a hello world function",
    "conversation_id": "conv-123"
  }'

# Follow-up request (maintains context)
curl -X POST http://localhost:8000/v1/agents/code \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Now add error handling",
    "conversation_id": "conv-123"
  }'
```

### List Agents First
```bash
# Get available agents
curl http://localhost:8000/v1/agents

# Use specific agent
curl -X POST http://localhost:8000/v1/agents/architect \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Design a microservices architecture"}'
```

---

## 🔧 Error Responses

### Agent Not Found (404)
```json
{
  "detail": "Agent 'invalid-agent' not found. Available agents: code, creative, debug, data, architect, pm, analyst, tech-writer"
}
```

### Rate Limit Exceeded (429)
```json
{
  "detail": "Rate limit exceeded for provider groq. Try again in 30 seconds."
}
```

### All Providers Failed (500)
```json
{
  "detail": "All providers failed. Last error: Timeout connecting to gemini"
}
```

---

## 💡 Quick Test Commands

### Test Health
```bash
curl http://localhost:8000/health
```

### Test Agent List
```bash
curl http://localhost:8000/v1/agents
```

### Test Code Generation
```bash
curl -X POST http://localhost:8000/v1/agents/code \
  -H "Content-Type: application/json" \
  -d '{"prompt": "print(\"Hello World\")"}'
```

### Test Architecture
```bash
curl -X POST http://localhost:8000/v1/agents/architect \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Design a simple web application"}'
```

---

## 🎯 LLM Integration Example

```python
import requests

# Base configuration
BASE_URL = "http://localhost:8000"
headers = {"Content-Type": "application/json"}

def ask_agent(agent_name, prompt, conversation_id=None):
    """Ask a specific agent"""
    data = {
        "prompt": prompt,
        "conversation_id": conversation_id
    }

    response = requests.post(
        f"{BASE_URL}/v1/agents/{agent_name}",
        json=data,
        headers=headers
    )

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error: {response.status_code} - {response.json()}")

# Usage examples
result = ask_agent("code", "Create a Flask API")
result = ask_agent("architect", "Design a database schema")
result = ask_agent("analyst", "Analyze this data: [1,2,3,4,5]")
```

---

## ⚠️ Important Notes

- **Always use `/v1/agents/{agent_name}`** (not `/api/chat` or other paths)
- **Required field:** `prompt` in request body
- **Optional fields:** `conversation_id`, `metadata`
- **Rate limiting:** Automatic per-provider throttling
- **Fallback:** Automatic provider switching on failures
- **Cost tracking:** Built-in cost optimization

---

**Full API documentation available at:** http://localhost:8000/docs
