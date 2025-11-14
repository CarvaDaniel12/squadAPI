"""
Squad API - Main Application Entry Point
Multi-Agent LLM Orchestration - Transforms external LLMs into specialized BMad agents
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
import redis.asyncio as redis
from dotenv import load_dotenv

# Load environment variables FIRST
# Try to load .env from project root (multiple possible locations)
project_root = Path(__file__).parent.parent
env_paths = [
    project_root / '.env',
    Path.cwd() / '.env',
    Path('.env'),
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path, override=False)  # Don't override existing env vars
        logger = logging.getLogger(__name__)
        logger.info(f"Loaded .env from: {env_path}")
        break
else:
    # If no .env file found, try default location
    load_dotenv(override=False)
    logger = logging.getLogger(__name__)
    logger.warning("No .env file found - using system environment variables only")

from src.api.agents import router as agents_router, set_orchestrator
from src.api.errors import AgentNotFoundException, agent_not_found_handler
from src.api.providers import router as providers_router, set_provider_tracker
from src.agents.loader import AgentLoader
from src.agents.prompt_builder import SystemPromptBuilder
from src.agents.conversation import ConversationManager
from src.agents.router import AgentRouter
from src.agents.orchestrator import AgentOrchestrator
from src.providers.local_prompt_optimizer import LocalPromptOptimizer
from src.config.validation import validate_config, ConfigurationError
from src.metrics.provider_status import ProviderStatusTracker
from src.rate_limit.combined import CombinedRateLimiter
from src.rate_limit.semaphore import GlobalSemaphore

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup: Load configuration with graceful fallback
    print("[INIT] Starting Squad API...")

    # Try to validate config, but continue if there are non-critical issues
    try:
        config = validate_config(config_dir="config")
        logger.info("[OK] Configuration validated successfully")
        settings = config.settings
        rate_limits = config.rate_limits
        agent_chains = config.agent_chains
        providers = config.providers
    except ConfigurationError as e:
        # Log but don't fail - use defaults
        logger.warning(f"[WARN] Configuration validation issue: {e}")
        logger.info("[INFO] Using default configuration - system will start with basic features")
        settings = None
        rate_limits = None
        agent_chains = None
        providers = None

    # Initialize Redis for conversation history and caching (Epic 1.5 + Epic 2)
    redis_client = None
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(redis_url, decode_responses=True)
        await redis_client.ping()
        print("[OK] Redis connected successfully")
    except Exception as e:
        logger.warning(f"[WARN] Redis connection failed: {e}")
        print("[WARN] Continuing with in-memory conversation cache (not persisted)")
        redis_client = None

    # Create components (Redis will be added in Story 0.3 integration)
    agent_loader = AgentLoader(bmad_path=".bmad", redis_client=redis_client)
    prompt_builder = SystemPromptBuilder()
    conversation_manager = ConversationManager(redis_client=redis_client)  # REAL Redis or in-memory fallback
    agent_router = AgentRouter(agent_loader)

    # Load all agents
    agents = await agent_loader.load_all()
    print(f"[OK] Loaded {len(agents)} BMad agents")

    # Initialize rate limiter (use loaded config or default)
    if rate_limits:
        rate_limiter = CombinedRateLimiter(rate_limits)
        print("[OK] Rate limiting initialized from config")
    else:
        rate_limiter = CombinedRateLimiter({})
        print("[WARN] Rate limiting initialized with defaults")

    # Initialize global semaphore for concurrency control
    max_concurrent = 12  # Default max concurrent requests
    global_semaphore = GlobalSemaphore(max_concurrent=max_concurrent)
    print(f"[OK] Global semaphore initialized (max {max_concurrent} concurrent)")

    # Initialize LLM providers (Epic 3)
    from src.providers.factory import ProviderFactory
    from src.utils.cost_optimizer import CostOptimizer

    provider_factory = ProviderFactory()
    llm_providers = {}
    cost_optimizer_instance = None

    try:
        # Create providers from config
        if providers:
            # Build provider instances from config
            all_provider_names = ['groq', 'gemini', 'cerebras', 'openrouter', 'anthropic', 'openai']

            for provider_name in all_provider_names:
                provider_config = getattr(providers, provider_name, None)
                if provider_config and provider_config.enabled:
                    provider_dict = {
                        'name': provider_name,  # Add the missing name field
                        'type': provider_name,
                        'enabled': provider_config.enabled,
                        'model': provider_config.model,
                        'api_key_env': provider_config.api_key_env,
                        'timeout': provider_config.timeout,
                        'rpm_limit': getattr(provider_config, 'rpm_limit', 60),
                        'tpm_limit': getattr(provider_config, 'tpm_limit', 100000),
                    }
                    if hasattr(provider_config, 'base_url') and provider_config.base_url:
                        provider_dict['base_url'] = provider_config.base_url

                    try:
                        provider_instance = provider_factory.create_provider(provider_name, provider_dict)
                        if provider_instance:
                            llm_providers[provider_name] = provider_instance
                    except RuntimeError as e:
                        logger.warning(f"[WARN] Skipping provider '{provider_name}': {e}")
                        print(f"[WARN] Skipping provider '{provider_name}': {e}")

            # Initialize cost optimizer if we have providers
            if llm_providers:
                cost_optimizer_instance = CostOptimizer()
                print("[OK] Cost optimizer initialized")
            else:
                raise RuntimeError(
                    "No working providers could be initialized. "
                    "Please check your API keys and provider configurations. "
                    "See docs/API-KEYS-SETUP.md for setup instructions."
                )
        else:
            raise RuntimeError("No provider config found. Please ensure providers are properly configured.")
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize providers: {e}")
        print(f"[ERROR] Failed to load providers - system will not start: {e}")
        raise

    # Prepare optional local prompt optimizer
    prompt_optimizer = None
    if providers and providers.prompt_optimizer:
        prompt_optimizer = LocalPromptOptimizer(providers.prompt_optimizer)

    # Create orchestrator with rate limiting and semaphore
    orchestrator = AgentOrchestrator(
        agent_loader=agent_loader,
        prompt_builder=prompt_builder,
        conversation_manager=conversation_manager,
        agent_router=agent_router,
        providers=llm_providers,  # Real LLM providers
        rate_limiter=rate_limiter,  # EPIC 2: Rate limiting
        global_semaphore=global_semaphore,  # EPIC 2: Concurrency control
        prompt_optimizer=prompt_optimizer,
        cost_optimizer=cost_optimizer_instance,  # Cost optimization
    )

    # Initialize provider status tracker (Story 9.5)
    provider_tracker = ProviderStatusTracker()
    orchestrator.provider_status_tracker = provider_tracker  # Assign to orchestrator
    set_provider_tracker(provider_tracker, providers)

    # Set global orchestrator
    set_orchestrator(orchestrator)

    print("[OK] Squad API is operational!")
    print("[INFO] API running on http://localhost:8000")
    print("[INFO] Documentation: http://localhost:8000/docs")

    yield

    # Shutdown
    print("[SHUTDOWN] Closing Squad API...")
    if redis_client:
        await redis_client.aclose()
        print("[OK] Redis connections closed")


app = FastAPI(
    title="Squad API",
    version="1.0.0",
    description="""
# Squad API - Multi-Provider LLM Orchestration

**Production-ready LLM orchestration with intelligent fallback, rate limiting, and observability.**

##  Features

-  **Multi-Provider Support:** Groq, Cerebras, Gemini, OpenRouter, Together AI
-  **Intelligent Fallback:** 3-tier fallback chain with quality verification
-  **Rate Limiting:** Per-provider rate limits with auto-throttling
-  **Agent Routing:** 13 specialized agents (code, creative, debug, data, etc.)
-  **Observability:** Prometheus metrics + Grafana dashboards
-  **Hot-Reload:** Update configuration without restart
-  **Conversation Context:** Multi-turn conversations with Redis storage

##  Quick Start

1. **Get API Keys:** Obtain at least one provider key (Groq recommended)
2. **Configure:** Copy `.env.example` to `.env` and add your keys
3. **Start:** Run `docker-compose up -d`
4. **Test:** Make your first request to `/v1/agents/code`

##  Resources

- **Documentation:** [GitHub README](https://github.com/your-org/squad-api)
- **Deployment:** [Deployment Runbook](docs/runbooks/deployment.md)
- **Troubleshooting:** [Troubleshooting Guide](docs/runbooks/troubleshooting.md)
- **Monitoring:** [Grafana Dashboards](http://localhost:3000)
    """,
    lifespan=lifespan,
    contact={
        "name": "Squad API Team",
        "url": "https://github.com/your-org/squad-api",
        "email": "support@squad-api.example.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.squad-api.example.com",
            "description": "Production server"
        }
    ],
    openapi_tags=[
        {
            "name": "agents",
            "description": "Agent execution endpoints - Route requests to specialized LLM agents"
        },
        {
            "name": "health",
            "description": "Health check and system status endpoints"
        },
        {
            "name": "metrics",
            "description": "Prometheus metrics endpoint for monitoring"
        }
    ]
)

# Security Headers Middleware (Story 9.7 - Security Hardening)
@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)

    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Prevent clickjacking attacks
    response.headers["X-Frame-Options"] = "DENY"

    # XSS Protection (legacy browsers)
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    return response

# CORS (development mode - will be restricted in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production: specific origins only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents_router)
app.include_router(providers_router)

# Exception handlers
app.add_exception_handler(AgentNotFoundException, agent_not_found_handler)


@app.get("/health", tags=["health"], summary="Health Check", response_description="Service health status")
async def health():
    """
    ## Health Check Endpoint

    Returns the current health status of Squad API and its dependencies.

    **Use this endpoint to:**
    - Verify Squad API is running
    - Check service readiness
    - Monitor service availability (load balancer health checks)

    **Response Fields:**
    - `status`: "healthy" or "degraded"
    - `service`: Service name
    - `version`: Current API version
    - `dependencies`: Status of Redis, PostgreSQL, etc. (coming soon)

    **Example Response:**
    ```json
    {
      "status": "healthy",
      "service": "squad-api",
      "version": "1.0.0",
      "dependencies": {
        "redis": "connected",
        "postgres": "connected"
      }
    }
    ```
    """
    return {
        "status": "healthy",
        "service": "squad-api",
        "version": "1.0.0"
    }


# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


