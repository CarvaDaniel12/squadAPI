"""
Quick test for Gemini provider (Windows-friendly)
"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.providers.gemini_provider import GeminiProvider
from src.models.provider import ProviderConfig


async def test_gemini():
    """Test Gemini provider"""
    print("=" * 60)
    print("  TESTING GEMINI PROVIDER")
    print("=" * 60)
    print()
    
    # Load .env
    load_dotenv()
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY not found in .env")
        sys.exit(1)
    
    print(f"[OK] API key found: {api_key[:20]}...")
    print()
    
    # Create provider
    config = ProviderConfig(
        name="gemini",
        type="gemini",
        model="gemini-2.0-flash-exp",
        api_key=api_key,
        rpm_limit=15,
        tpm_limit=1000000
    )
    
    print("[*] Creating Gemini provider...")
    provider = GeminiProvider(config)
    print(f"[OK] Provider created: {provider.model}")
    print()
    
    # Test 1: Health check
    print("[*] Test 1: Health Check...")
    try:
        is_healthy = await provider.health_check()
        if is_healthy:
            print("[OK] Health check PASSED")
        else:
            print("[FAIL] Health check returned False")
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Health check failed: {e}")
        sys.exit(1)
    
    print()
    
    # Test 2: Real LLM call
    print("[*] Test 2: Real LLM Call...")
    print("    Prompt: 'Say Hello from Squad API!'")
    print()
    
    try:
        import time
        start = time.time()
        
        response = await provider.call(
            system_prompt="You are a helpful assistant. Respond concisely.",
            user_prompt="Say 'Hello from Squad API!' and nothing else.",
            max_tokens=50,
            temperature=0.7
        )
        
        elapsed_ms = int((time.time() - start) * 1000)
        
        print("[OK] Call SUCCESSFUL!")
        print()
        print("=" * 60)
        print("  RESPONSE FROM GEMINI")
        print("=" * 60)
        print()
        print(response.content)
        print()
        print("=" * 60)
        print()
        print(f"Provider: {response.provider}")
        print(f"Model: {response.model}")
        print(f"Latency: {response.latency_ms}ms (actual: {elapsed_ms}ms)")
        print(f"Tokens: {response.tokens_input} input -> {response.tokens_output} output")
        print(f"Finish Reason: {response.finish_reason}")
        print()
        print("[SUCCESS] GEMINI IS WORKING!")
        
    except Exception as e:
        print(f"[ERROR] LLM call failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(test_gemini())
    except KeyboardInterrupt:
        print("\n[WARN] Interrupted by user")
        sys.exit(0)

