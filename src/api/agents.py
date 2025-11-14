"""
Agent API Endpoints
Story 1.7: Agent Execution Orchestrator
Story 1.8: Agent List Endpoint
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from src.models.request import AgentExecutionRequest
from src.models.response import AgentExecutionResponse
from src.agents.orchestrator import AgentOrchestrator
from src.agents.router import AgentRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["agents"])

# Global orchestrator (will be initialized on app startup)
_orchestrator: AgentOrchestrator = None


def get_orchestrator() -> AgentOrchestrator:
    """Dependency to get orchestrator instance"""
    if _orchestrator is None:
        raise HTTPException(503, "Orchestrator not initialized")
    return _orchestrator


def set_orchestrator(orchestrator: AgentOrchestrator):
    """Set global orchestrator (called from main.py startup)"""
    global _orchestrator
    _orchestrator = orchestrator


@router.post(
    "/agents/{agent_name}",
    response_model=AgentExecutionResponse,
    summary="Execute Agent Request",
    response_description="Agent execution result with response and metadata",
    responses={
        200: {
            "description": "Successful agent execution",
            "content": {
                "application/json": {
                    "example": {
                        "response": "Here's a Python function to calculate Fibonacci numbers:\\n\\n```python\\ndef fibonacci(n):\\n    if n <= 0:\\n        return 0\\n    elif n == 1:\\n        return 1\\n    else:\\n        return fibonacci(n-1) + fibonacci(n-2)\\n```",
                        "provider": "groq",
                        "model": "llama-3.1-70b-versatile",
                        "conversation_id": "test-123",
                        "metadata": {
                            "fallback_used": False,
                            "processing_time_ms": 234,
                            "tokens_used": 150,
                            "rate_limit_remaining": 45
                        }
                    }
                }
            }
        },
        404: {
            "description": "Agent not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Agent 'invalid-agent' not found. Available agents: code, creative, debug, data, ..."
                    }
                }
            }
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Rate limit exceeded for provider groq. Try again in 30 seconds."
                    }
                }
            }
        },
        500: {
            "description": "All providers failed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "All providers failed. Last error: Timeout connecting to gemini"
                    }
                }
            }
        }
    }
)
async def execute_agent(
    agent_name: str,
    request: AgentExecutionRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    ## Execute Agent Request

    Route a request to a specialized LLM agent with intelligent fallback and rate limiting.

    ### Available Agents

    | Agent | Best For | Example Use Case |
    |-------|----------|------------------|
    | `code` | Programming tasks | "Write a Python function to parse JSON" |
    | `creative` | Content creation | "Write a marketing email" |
    | `debug` | Troubleshooting | "Why is my API returning 500 errors?" |
    | `data` | Data analysis | "Analyze this CSV and find trends" |
    | `architect` | System design | "Design a microservices architecture" |
    | `pm` | Project planning | "Create a sprint plan for this feature" |
    | `analyst` | Business analysis | "Analyze market trends for this product" |
    | `tech-writer` | Documentation | "Write API documentation for this endpoint" |

    ### Request Body

    ```json
    {
      "prompt": "Write a Python function to calculate Fibonacci numbers",
      "conversation_id": "optional-conversation-id",
      "metadata": {
        "user_id": "john@example.com",
        "session": "abc123"
      }
    }
    ```

    ### Response Fields

    - **response** (string): LLM-generated response
    - **provider** (string): Provider used (groq, cerebras, gemini, etc.)
    - **model** (string): LLM model used
    - **conversation_id** (string): Conversation ID for multi-turn dialogs
    - **metadata** (object):
      - **fallback_used** (bool): Whether fallback was triggered
      - **processing_time_ms** (int): Response time in milliseconds
      - **tokens_used** (int): Tokens consumed
      - **rate_limit_remaining** (int): Remaining requests before rate limit

    ### Multi-Turn Conversations

    Use the same `conversation_id` to maintain context across requests:

    ```bash
    # First request
    curl -X POST http://localhost:8000/v1/agents/code \\
      -H "Content-Type: application/json" \\
      -d '{
        "prompt": "Write a hello world function",
        "conversation_id": "conv-123"
      }'

    # Follow-up request (remembers previous context)
    curl -X POST http://localhost:8000/v1/agents/code \\
      -H "Content-Type: application/json" \\
      -d '{
        "prompt": "Now add error handling",
        "conversation_id": "conv-123"
      }'
    ```

    ### Fallback Chain

    If the primary provider fails (rate limit, timeout, error), the request automatically
    falls back to alternative providers:

    1. **Primary:** Groq (fast, cost-effective)
    2. **Secondary:** Cerebras (high quality)
    3. **Tertiary:** Gemini (reliable fallback)

    ### Rate Limiting

    Rate limits are enforced per provider:
    - **Groq:** 60 requests/min, 60,000 tokens/min
    - **Cerebras:** 30 requests/min, 900,000 tokens/min
    - **Gemini:** 60 requests/min, 32,000 tokens/min

    Auto-throttling activates at 80% of limit to prevent hard failures.
    """
    try:
        # Set agent from URL path parameter
        request.agent = agent_name

        # Set default user_id if not provided
        if not request.user_id:
            request.user_id = "anonymous"

        # Route to correct agent endpoint based on agent_name
        # This is a simplified version - full routing logic in AgentOrchestrator
        response = await orchestrator.execute(request)
        return response

    except ValueError as e:
        # Agent not found
        raise HTTPException(404, str(e))

    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        raise HTTPException(500, f"Agent execution failed: {str(e)}")


@router.get(
    "/agents",
    summary="List Available Agents",
    response_description="List of all available agents with their capabilities",
    responses={
        200: {
            "description": "Successful response with agent list",
            "content": {
                "application/json": {
                    "example": {
                        "count": 13,
                        "agents": [
                            {
                                "id": "code",
                                "name": "CodeMaster",
                                "description": "Expert in programming, debugging, and code review",
                                "capabilities": ["Python", "JavaScript", "Java", "Code Review", "Debugging"],
                                "icon": ""
                            },
                            {
                                "id": "creative",
                                "name": "CreativeGenius",
                                "description": "Specialized in content creation and creative writing",
                                "capabilities": ["Marketing Copy", "Blog Posts", "Social Media", "Storytelling"],
                                "icon": ""
                            },
                            {
                                "id": "analyst",
                                "name": "Mary",
                                "description": "Business analyst expert in market research and data analysis",
                                "capabilities": ["Market Research", "Data Analysis", "Business Strategy"],
                                "icon": ""
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def list_agents(
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    ## List All Available Agents

    Returns a comprehensive list of all available agents with their capabilities,
    specializations, and metadata.

    ### Response Fields

    - **count** (int): Total number of available agents
    - **agents** (array): List of agent objects
      - **id** (string): Agent identifier (use this in `/v1/agents/{agent_name}`)
      - **name** (string): Human-friendly agent name
      - **description** (string): What the agent specializes in
      - **capabilities** (array): List of agent capabilities
      - **icon** (string): Visual icon for the agent

    ### Agent Categories

    **Development Agents:**
    - `code` - Programming and code generation
    - `debug` - Troubleshooting and debugging
    - `architect` - System architecture and design
    - `tech-writer` - Technical documentation

    **Business Agents:**
    - `analyst` - Business analysis and research
    - `pm` - Project management and planning
    - `sm` - Scrum master and agile practices

    **Creative Agents:**
    - `creative` - Content creation and copywriting
    - `ux-designer` - User experience design

    **Data Agents:**
    - `data` - Data analysis and visualization
    - `tea` - Technical excellence architect

    ### Example Usage

    ```bash
    curl http://localhost:8000/v1/agents
    ```

    Use the returned agent IDs to make requests to `/v1/agents/{agent_name}`.
    """
    agents = orchestrator.router.list_available_agents()

    return {
        "count": len(agents),
        "agents": agents
    }


