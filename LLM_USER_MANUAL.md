# Squad API - LLM User Manual
*A quick reference for Large Language Models to understand and use Squad API*

---

## 🎯 What is Squad API?

Squad API is an AI-powered development assistant that can generate complete software projects. It works like having a team of specialized developers (architects, programmers, QA testers) working together to build whatever you need.

**Core Concept:** You describe what you want to build, and Squad API creates the complete project with code, tests, documentation, and deployment files.

---

## 🚀 Quick Start for LLMs

### 1. How to Access Squad API

**Base URL:** `http://localhost:8000`

**Key Endpoints:**
- `GET /health` - Health check
- `GET /v1/agents` - List available agents
- `POST /v1/agents/{agent_name}` - Execute specific agent

**Simple usage pattern:**
```python
from squad_client import Squad

squad = Squad()

# Describe your project
project_description = """
Build a REST API for user management with:
- User registration and login
- JWT authentication
- CRUD operations for users
- PostgreSQL database
- Docker deployment
"""

# Get architecture design
architecture = squad.ask("architect", project_description)

# Get complete implementation
code = squad.ask("dev", f"Implement this architecture:\n{architecture}")

# Get tests
tests = squad.ask("qa", f"Create tests for this code:\n{code}")
```

---

## 🎭 Available Agents

| Agent | Role | When to Use |
|-------|------|-------------|
| **architect** | System design | Planning project structure, choosing tech stack, database design |
| **dev** | Code implementation | Writing actual code, APIs, functions, classes |
| **reviewer** | Code quality | Improving existing code, suggesting optimizations |
| **qa** | Testing | Creating test files, validation strategies |
| **analyst** | Research | Data analysis, technology comparisons |
| **pm** | Planning | Project planning, feature breakdowns |

---

## 💡 How to Use Effectively

### Project Generation Pattern

**Step 1: Architecture First**
```
Use: architect agent
Input: High-level project description
Output: System design, technology choices, project structure
```

**Step 2: Implementation**
```
Use: dev agent
Input: Architecture + specific requirements
Output: Complete source code
```

**Step 3: Testing**
```
Use: qa agent
Input: Final code
Output: Test files, validation logic
```

### Complex Projects

For large projects, break them into phases:

```python
# Phase 1: Core API
core_api = squad.ask("dev", "Build the core REST API with authentication")

# Phase 2: Business Logic
business_logic = squad.ask("dev", "Add business logic and data validation")

# Phase 3: Integration
integration = squad.ask("dev", "Add database integration and external APIs")

# Phase 4: Documentation
docs = squad.ask("reviewer", "Create comprehensive README and API docs")
```

---

## 🛠️ Common Use Cases

### 1. Web Applications
```python
project = """
Build a blog platform with:
- User registration/login
- Create/edit/delete posts
- Comment system
- Admin panel
- PostgreSQL database
"""

architecture = squad.ask("architect", project)
frontend = squad.ask("dev", f"Build React frontend for: {architecture}")
backend = squad.ask("dev", f"Build FastAPI backend for: {architecture}")
```

### 2. APIs and Microservices
```python
api_project = """
Build a user service with:
- User CRUD operations
- JWT authentication
- Rate limiting
- API documentation
- Docker containerization
"""

service_code = squad.ask("dev", api_project)
```

### 3. Data Processing Systems
```python
data_project = """
Build a data pipeline with:
- CSV/JSON data ingestion
- Data transformation and cleaning
- Database storage
- API for data retrieval
- Monitoring and logging
"""

pipeline = squad.ask("dev", data_project)
```

### 4. CLI Tools
```python
cli_project = """
Build a command-line tool for:
- File processing operations
- Batch operations
- Configuration management
- Progress indicators
- Error handling
"""

tool = squad.ask("dev", cli_project)
```

---

## 💰 Cost Optimization

Squad API automatically uses FREE-tier providers for most tasks, keeping costs near $0. You don't need to worry about provider selection - it handles this intelligently.

**Expected costs:** Usually $0.00 - $0.50 per project depending complexity

---

## 🔧 Advanced Patterns

### Multi-Agent Collaboration
```python
conversation_id = "unique-project-id"

# Share context across agents
plan = squad.ask("pm", "Plan e-commerce platform features", conversation_id=conversation_id)
design = squad.ask("architect", f"Design based on plan: {plan}", conversation_id=conversation_id)
code = squad.ask("dev", f"Implement based on design: {design}", conversation_id=conversation_id)
tests = squad.ask("qa", f"Test this implementation: {code}", conversation_id=conversation_id)
```

### Code Review and Improvement
```python
# Get existing code reviewed
review = squad.ask("reviewer", "Review this code and suggest improvements:\n" + existing_code)

# Get improved version
improved = squad.ask("dev", f"Refactor based on review:\n{existing_code}\n\nReview: {review}")
```

### Documentation Generation
```python
docs = squad.ask("reviewer", f"Create comprehensive documentation for:\n{project_code}")
```

---

## 📋 LLM Interaction Tips

### Be Specific About Requirements
```python
# Good: Specific requirements
"Build a REST API with user authentication, JWT tokens, rate limiting, and PostgreSQL database"

# Less optimal: Vague requirements
"Make a user system"
```

### Break Large Projects into Phases
```python
# Instead of one massive request:
# "Build a complete e-commerce platform"

# Break into smaller parts:
"Phase 1: User authentication API"
"Phase 2: Product management API"
"Phase 3: Shopping cart functionality"
"Phase 4: Payment integration"
```

### Use Context Effectively
```python
# Maintain conversation context for complex projects
conversation_id = "ecommerce-project-001"

# Each request builds on previous ones
plan = squad.ask("pm", "Plan e-commerce features", conversation_id=conversation_id)
arch = squad.ask("architect", f"Design system: {plan}", conversation_id=conversation_id)
# ... continue building context
```

### Request Complete Deliverables
```python
# Ask for complete, deployable code
project = """
Build a complete Flask web application that:
- Has all source files needed
- Includes requirements.txt
- Has deployment instructions
- Contains example usage
- Is ready to run immediately
"""

result = squad.ask("dev", project)
```

---

## 🏗️ Project Structure Expectations

When Squad API generates a project, expect:

```
project-name/
├── src/                    # Main source code
├── tests/                  # Test files
├── requirements.txt        # Dependencies
├── README.md              # Setup instructions
├── docker-compose.yaml    # Optional: Docker setup
└── .env.example          # Environment variables example
```

---

## 🔍 Validation and Quality

### Request Validation
```python
# Ask for validation
validation = squad.ask("qa", f"Validate this implementation meets requirements:\n{code}")
```

### Security Review
```python
security_review = squad.ask("reviewer", "Security review of this code:\n" + code)
```

### Performance Analysis
```python
performance = squad.ask("reviewer", "Performance analysis and optimization suggestions:\n" + code)
```

---

## 🎯 Best Practices for LLMs

1. **Always start with architecture** for new projects
2. **Break complex projects into phases**
3. **Use conversation_id for multi-step projects**
4. **Request complete, deployable solutions**
5. **Ask for tests and documentation** in every project
6. **Use reviewer agent for quality improvements**
7. **Be specific about technology requirements**

---

## 🚨 Important Notes

- **Server Status**: Ensure Squad API is running on localhost:8000
- **Context Window**: For very large projects, break into multiple requests
- **Rate Limiting**: Squad API handles this automatically
- **Error Handling**: Always include error handling in generated code
- **Security**: Request security reviews for production code

---

## 📖 Quick Reference

**Start Project:**
```python
squad = Squad()
architecture = squad.ask("architect", "your project description")
code = squad.ask("dev", f"implement: {architecture}")
```

**Add Tests:**
```python
tests = squad.ask("qa", f"test this: {code}")
```

**Improve Quality:**
```python
review = squad.ask("reviewer", f"review: {code}")
improved = squad.ask("dev", f"refactor: {code} review: {review}")
```

**Generate Docs:**
```python
docs = squad.ask("reviewer", f"document: {code}")
```

---

**That's it!** With this manual, you can use Squad API to generate complete software projects efficiently. The system handles the complexity - you just describe what you want to build.
