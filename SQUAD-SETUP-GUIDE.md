# 🚀 Squad API - Setup Guide for Global Usage

## 📋 Overview

This guide shows you how to set up Squad API **once** and use it from **any project** on your machine.

## 🎯 Architecture

```
Your Machine:
├── Squad API (Running in background)
│   └── http://localhost:8000
│
└── Your Projects (Any folder)
    ├── project-1/
    │   └── squad_client.py  ← Copy this file
    ├── project-2/
    │   └── squad_client.py  ← Copy this file
    └── project-3/
        └── squad_client.py  ← Copy this file
```

## ⚡ One-Time Setup

### 1. Install Squad API (Already Done! ✅)

```bash
cd "C:\Users\User\Desktop\squad api"
python scripts/workflow-init.py  # All checks passed!
```

### 2. Start Squad API as Background Service

#### Option A: Keep Terminal Open
```powershell
cd "C:\Users\User\Desktop\squad api"
python src/main.py
```
Leave this terminal running in background.

#### Option B: Windows Service (Recommended)

Create `start-squad.bat`:
```batch
@echo off
cd "C:\Users\User\Desktop\squad api"
start /B python src/main.py
echo Squad API started in background!
```

Create `stop-squad.bat`:
```batch
@echo off
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Squad API*"
echo Squad API stopped!
```

### 3. Verify Squad is Running

```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

## 🎨 Using Squad in Any Project

### Method 1: Copy Client File

```bash
# In any new project:
cp "C:\Users\User\Desktop\squad api\scripts\squad_client.py" .
```

Then use it:

```python
from squad_client import Squad

squad = Squad()

# Generate code
code = squad.ask("dev", "Create a Flask API with user authentication")
print(code)

# System design
architecture = squad.ask("architect", "Design microservices for e-commerce")
print(architecture)

# Code review
review = squad.ask("reviewer", "Review this function: def calc(x): return x*2")
print(review)
```

### Method 2: CLI Usage

```bash
# From any folder:
python squad_client.py dev "Create a REST API endpoint for user login"
python squad_client.py architect "Design a scalable chat system"
python squad_client.py qa "Write tests for a password validator"
```

### Method 3: Add to Python Path (Advanced)

```powershell
# One-time setup - Add to your Python environment
$env:PYTHONPATH += ";C:\Users\User\Desktop\squad api\scripts"
```

Then import from anywhere:
```python
from squad_client import Squad
squad = Squad()
```

## 📊 Available Agents

| Agent | Purpose | Example Use |
|-------|---------|-------------|
| **dev** | Code generation & debugging | "Create a Python class for user management" |
| **analyst** | Research & data analysis | "Analyze pros/cons of PostgreSQL vs MongoDB" |
| **architect** | System design & architecture | "Design a microservices architecture" |
| **reviewer** | Code review & quality | "Review this function and suggest improvements" |
| **qa** | Test design & validation | "Write unit tests for this API endpoint" |
| **pm** | Planning & coordination | "Create sprint plan for authentication feature" |

## 💡 Usage Examples

### Example 1: Generate Full API

```python
from squad_client import Squad

squad = Squad()

# Step 1: Architecture
architecture = squad.ask("architect", """
Design a REST API for a todo application with:
- User authentication
- CRUD operations for todos
- PostgreSQL database
""")

# Step 2: Implementation
code = squad.ask("dev", f"""
Based on this architecture:
{architecture}

Create the FastAPI implementation with:
- User registration and login
- JWT authentication
- Todo CRUD endpoints
""")

# Step 3: Tests
tests = squad.ask("qa", f"""
Generate pytest tests for this API:
{code}
""")

print(code)
print(tests)
```

### Example 2: Code Review Workflow

```python
from squad_client import Squad

squad = Squad()

# Your code
my_code = """
def process_users(users):
    result = []
    for user in users:
        if user['age'] > 18:
            result.append(user)
    return result
"""

# Get review
review = squad.ask("reviewer", f"Review and improve:\n{my_code}")
print(review)

# Get improved version
improved = squad.ask("dev", f"Refactor based on review:\n{my_code}\n\nReview:\n{review}")
print(improved)
```

### Example 3: Multi-Agent Collaboration

```python
from squad_client import Squad

squad = Squad()
conversation_id = "project-xyz-123"

# 1. PM creates plan
plan = squad.ask("pm", "Plan sprint for user authentication feature",
                 conversation_id=conversation_id)

# 2. Architect designs system
design = squad.ask("architect", "Design auth system based on plan",
                   conversation_id=conversation_id)

# 3. Dev implements
code = squad.ask("dev", "Implement auth based on design",
                 conversation_id=conversation_id)

# 4. QA creates tests
tests = squad.ask("qa", "Create tests for implementation",
                  conversation_id=conversation_id)

# 5. Reviewer checks quality
review = squad.ask("reviewer", "Final review before deployment",
                   conversation_id=conversation_id)
```

## 💰 Cost Monitoring

```python
from squad_client import Squad

squad = Squad()

# Check costs anytime
stats = squad.cost_report()
print(f"Cost today: ${stats['total_cost']:.4f}")
print(f"FREE tier: {stats['free_percentage']}%")
print(f"Requests: {stats['request_count']}")
```

## 🔧 Troubleshooting

### Squad API Not Running

```bash
❌ Squad API is not running!
💡 Start it with: cd 'C:\Users\User\Desktop\squad api' && python src/main.py
```

**Solution:**
```bash
cd "C:\Users\User\Desktop\squad api"
python src/main.py
```

### Connection Timeout

```bash
❌ Request timeout (60s). Task might be too complex.
```

**Solution:**
- Break complex tasks into smaller steps
- Use conversation_id to maintain context across requests

### Port Already in Use

```bash
ERROR: Address already in use
```

**Solution:**
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /F /PID <PID>
```

## 🎯 Quick Reference

### Start Squad API
```bash
cd "C:\Users\User\Desktop\squad api"
python src/main.py
```

### Copy Client to New Project
```bash
cp "C:\Users\User\Desktop\squad api\scripts\squad_client.py" .
```

### Use in Python
```python
from squad_client import Squad
squad = Squad()
response = squad.ask("dev", "Your task here")
```

### Use in CLI
```bash
python squad_client.py dev "Your task here"
```

### Check Costs
```python
squad.cost_report()
```

## 🚀 Advanced: Auto-Start on Windows Boot

Create `start-squad-service.vbs`:
```vbscript
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd ""C:\Users\User\Desktop\squad api"" && python src/main.py", 0
Set WshShell = Nothing
```

Add to Windows Startup:
1. Press `Win + R`
2. Type `shell:startup`
3. Copy `start-squad-service.vbs` to this folder

Squad API will start automatically on login!

---

**🎉 You're Ready!**

Squad API is now your permanent AI development assistant. Use it from any project without ever touching the Squad API codebase again.
