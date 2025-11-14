#!/usr/bin/env python
"""
Squad API - Quick Start (Bypass strict validation for testing)
Starts the API server with basic configuration
"""

import os
import sys
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Quick start the API"""

    # Check environment
    required_env = ['GROQ_API_KEY', 'GEMINI_API_KEY', 'CEREBRAS_API_KEY', 'OPENROUTER_API_KEY']
    missing = [k for k in required_env if not os.getenv(k)]

    if missing:
        print(f"[WARNING] Missing API keys: {', '.join(missing)}")
        print("[INFO] API will work but these providers will fail")

    # Import after environment check
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn

    app = FastAPI(
        title="Squad API",
        description="Multi-Agent LLM Orchestration Platform",
        version="1.0.0"
    )

    # Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Import routers
    from src.api.agents import router as agents_router
    from src.api.providers import router as providers_router

    # Add routes
    app.include_router(agents_router)
    app.include_router(providers_router)

    # Health check endpoint
    @app.get("/health")
    async def health():
        return {
            "status": "operational",
            "version": "1.0.0",
            "database": "postgresql://localhost:5432/squad_api"
        }

    @app.get("/")
    async def root():
        return {
            "message": "Squad API - Multi-Agent LLM Orchestration",
            "docs": "http://localhost:8000/docs",
            "health": "http://localhost:8000/health"
        }

    # Start server
    print("\n" + "="*60)
    print("Squad API - Starting...")
    print("="*60)
    print("[INFO] API: http://localhost:8000")
    print("[INFO] Docs: http://localhost:8000/docs")
    print("[INFO] Health: http://localhost:8000/health")
    print("="*60 + "\n")

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
