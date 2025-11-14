"""
Squad API - Workflow Initialization Script
Validates environment and prepares project for execution
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple
import codecs

# Set UTF-8 encoding for Windows compatibility
if sys.platform.startswith('win'):
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Colors for terminal output (with fallback for Windows)
class Colors:
    GREEN = '\033[92m' if not sys.platform.startswith('win') else '[92m'
    CYAN = '\033[96m' if not sys.platform.startswith('win') else '[96m'
    YELLOW = '\033[93m' if not sys.platform.startswith('win') else '[93m'
    RED = '\033[91m' if not sys.platform.startswith('win') else '[91m'
    BOLD = '\033[1m' if not sys.platform.startswith('win') else '[1m'
    END = '\033[0m' if not sys.platform.startswith('win') else '[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}{msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.CYAN}{msg}{Colors.END}")

def print_warn(msg: str):
    print(f"{Colors.YELLOW}{msg}{Colors.END}")

def print_fail(msg: str):
    print(f"{Colors.RED}{msg}{Colors.END}")

def print_header(msg: str):
    print()
    print("=" * 80)
    print(f"  {msg}")
    print("=" * 80)

# Track issues
errors: List[str] = []
warnings: List[str] = []

def check_python() -> bool:
    """Check Python version"""
    print_header("1️⃣  PYTHON ENVIRONMENT")

    version = sys.version.split()[0]
    print_success(f"✅ Python: {version}")

    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 9):
        print_warn(f"⚠️  Warning: Python 3.9+ recommended (found: {version})")
        warnings.append("Python version may be incompatible")

    return True

def check_dependencies() -> bool:
    """Check required Python packages"""
    print_header("2️⃣  CHECKING DEPENDENCIES")

    required = [
        "fastapi", "uvicorn", "redis", "python-dotenv",
        "aiohttp", "pydantic", "PyYAML"
    ]

    missing = []

    for package in required:
        try:
            result = subprocess.run(
                ["pip", "show", package],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print_success(f"✅ {package}")
            else:
                print_fail(f"❌ {package} (not installed)")
                missing.append(package)
        except:
            print_fail(f"❌ {package} (not installed)")
            missing.append(package)

    if missing:
        print_warn("\n⚠️  Missing packages. Install with:")
        print_info("   pip install -r requirements.txt")
        errors.append("Missing Python packages")

    return len(missing) == 0

def check_env() -> bool:
    """Check .env configuration"""
    print_header("3️⃣  ENVIRONMENT CONFIGURATION")

    env_path = Path(".env")

    if not env_path.exists():
        print_fail("❌ .env file not found")

        example_path = Path(".env.example")
        if example_path.exists():
            print_info("   Creating from .env.example...")
            example_path.read_text()  # Just check it exists
            env_path.write_text(example_path.read_text())
            print_success("✅ Created .env from template")
            print_warn("⚠️  IMPORTANT: Edit .env and add your API keys!")
        else:
            print_fail("❌ .env.example not found")
            errors.append(".env file missing")
            return False
    else:
        print_success("✅ .env file found")

    # Check API keys
    print_info("\n📋 API Keys Status:")

    api_keys = {
        "GROQ_API_KEY": "Groq (Free - 30 RPM)",
        "GEMINI_API_KEY": "Gemini (Free - 15 RPM)",
        "CEREBRAS_API_KEY": "Cerebras (Free - 30 RPM)",
        "OPENROUTER_API_KEY": "OpenRouter (Free - 20 RPM, 46 models!)",
        "OPENAI_API_KEY": "OpenAI (Paid - GPT-4o)",
        "ANTHROPIC_API_KEY": "Anthropic (Paid - Claude 3.5)"
    }

    env_content = env_path.read_text()
    has_at_least_one = False

    for key, desc in api_keys.items():
        if key in env_content:
            # Extract value
            for line in env_content.split('\n'):
                if line.startswith(f"{key}="):
                    value = line.split('=', 1)[1].strip()
                    if value and value != "your_key_here" and len(value) > 10:
                        print_success(f"   ✅ {desc}")
                        has_at_least_one = True
                    else:
                        print_warn(f"   ⚠️  {desc} - NOT SET")
                    break
        else:
            print_warn(f"   ⚠️  {desc} - MISSING")

    if not has_at_least_one:
        print_fail("\n❌ No valid API keys found!")
        print_info("   Add at least one API key to .env")
        print_info("   Recommended: GROQ_API_KEY (free and fast)")
        errors.append("No API keys configured")
        return False

    return True

def check_redis() -> bool:
    """Check Redis connection"""
    print_header("4️⃣  REDIS CONNECTION")

    try:
        # Try using Python redis client
        import redis as redis_module
        r = redis_module.Redis(host='localhost', port=6379, socket_connect_timeout=2)
        r.ping()
        print_success("✅ Redis is running (localhost:6379)")
        return True
    except ImportError:
        # redis-py not installed, try redis-cli
        try:
            result = subprocess.run(
                ["redis-cli", "ping"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0 and "PONG" in result.stdout:
                print_success("✅ Redis is running (localhost:6379)")
                return True
        except:
            pass
    except:
        pass

    print_fail("❌ Redis is not running")
    print_info("\n   To start Redis:")
    print_info("   1. Open new terminal")
    print_info("   2. Run: redis-server")
    print_info("   3. Keep it running in background")
    errors.append("Redis not running")
    return False

def check_config_files() -> bool:
    """Check configuration files"""
    print_header("5️⃣  CONFIGURATION FILES")

    config_files = [
        "config/providers.yaml",
        "config/rate_limits.yaml",
        "config/agent_routing.yaml",
        "config/cost_optimization.yaml"
    ]

    all_ok = True

    for file_path in config_files:
        if Path(file_path).exists():
            print_success(f"✅ {file_path}")
        else:
            print_fail(f"❌ {file_path} (missing)")
            errors.append(f"Missing config: {file_path}")
            all_ok = False

    return all_ok

def check_cost_optimization():
    """Check cost optimization config"""
    print_header("6️⃣  COST OPTIMIZATION")

    config_path = Path("config/cost_optimization.yaml")
    if config_path.exists():
        content = config_path.read_text()

        # Extract budget
        for line in content.split('\n'):
            if 'daily_budget:' in line:
                budget = line.split(':')[1].strip()
                print_success(f"✅ Daily budget configured: ${budget}")
                break

        print_info("\n💰 Cost Strategy:")
        print_info("   - Simple tasks → FREE providers only")
        print_info("   - Code tasks → OpenRouter Qwen3 480B (FREE!)")
        print_info("   - Complex tasks → OpenRouter DeepSeek 671B (FREE!)")
        print_info("   - Critical tasks → Claude 3.5 / GPT-4o (Paid)")
        print_info("\n   Expected savings: 60-95% vs paid-only strategy")

def check_openrouter_models():
    """Check OpenRouter models cache"""
    print_header("7️⃣  OPENROUTER FREE MODELS")

    models_path = Path("config/openrouter_free_models.json")
    if models_path.exists():
        import json
        models = json.loads(models_path.read_text())
        print_success(f"✅ {len(models)} FREE models cached")
        print_info("\n   Top 3 models:")
        print_info("   1. Gemini 2.0 Flash (1M context)")
        print_info("   2. Qwen3 Coder 480B (262K context)")
        print_info("   3. KAT-Coder-Pro (256K context)")
        print_info("\n   Auto-discovery: python scripts/discover_openrouter_models.py")
    else:
        print_warn("⚠️  OpenRouter models cache not found")
        print_info("   Run: python scripts/discover_openrouter_models.py")

def check_agents():
    """Check BMAD agents"""
    print_header("8️⃣  BMAD AGENTS")

    agents_path = Path(".bmad/agents")
    if agents_path.exists():
        agent_files = list(agents_path.glob("*.yaml"))
        if agent_files:
            print_success(f"✅ {len(agent_files)} agents found in .bmad/agents/")
        else:
            print_warn("⚠️  No agents found in .bmad/agents/")
            warnings.append("No BMAD agents configured")
    else:
        print_warn("⚠️  .bmad/agents directory not found")

def check_imports():
    """Test critical imports"""
    print_header("9️⃣  PYTHON IMPORTS TEST")

    print_info("Testing critical imports...")

    imports = [
        "src.agents.orchestrator",
        "src.utils.cost_optimizer",
        "src.providers.openrouter_provider",
        "src.utils.openrouter_fallback"
    ]

    all_ok = True

    for module in imports:
        try:
            result = subprocess.run(
                ["python", "-c", f"import {module}; print('OK')"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if "OK" in result.stdout:
                print_success(f"✅ {module}")
            else:
                print_fail(f"❌ {module}")
                errors.append(f"Import failed: {module}")
                all_ok = False
        except:
            print_fail(f"❌ {module}")
            errors.append(f"Import failed: {module}")
            all_ok = False

    return all_ok

def check_ollama():
    """Check Ollama installation and model availability (optional)"""
    print_header("🔟 OLLAMA LOCAL MODEL (Optional)")

    print_info("Checking Ollama availability...")

    try:
        # Check if Ollama is running
        result = subprocess.run(
            ["python", "-c",
             "import asyncio, aiohttp; "
             "async def check(): "
             "  async with aiohttp.ClientSession() as s: "
             "    async with s.get('http://localhost:11434/api/tags', timeout=aiohttp.ClientTimeout(total=3)) as r: "
             "      return r.status == 200; "
             "print(asyncio.run(check()))"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if "True" in result.stdout:
            print_success("✅ Ollama service is running")

            # Check for recommended models
            result = subprocess.run(
                ["python", "-c",
                 "import asyncio, aiohttp, json; "
                 "async def get_models(): "
                 "  async with aiohttp.ClientSession() as s: "
                 "    async with s.get('http://localhost:11434/api/tags') as r: "
                 "      data = await r.json(); "
                 "      return [m['name'] for m in data.get('models', [])]; "
                 "print(json.dumps(asyncio.run(get_models())))"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.stdout:
                import json
                models = json.loads(result.stdout.strip())
                print_info(f"   Found {len(models)} Ollama models")

                # Check for recommended models
                has_llama32 = any("llama3.2" in m for m in models)
                has_phi3 = any("phi3" in m for m in models)

                if has_llama32:
                    print_success("   ✅ llama3.2 model available (recommended)")
                elif has_phi3:
                    print_success("   ✅ phi3 model available (alternative)")
                else:
                    print_warn("   ⚠️  No recommended model found")
                    print_info("   💡 Run: ollama pull llama3.2:3b")
                    warnings.append("Ollama model not found - prompt optimization disabled")

            return True
        else:
            print_warn("⚠️  Ollama service not running")
            print_info("   💡 Optional: Start Ollama for local prompt optimization")
            print_info("   💡 Download from: https://ollama.ai")
            warnings.append("Ollama not running - prompt optimization disabled")
            return True  # Not a critical error

    except Exception as exc:
        print_warn("⚠️  Ollama not installed")
        print_info("   💡 Optional: Install Ollama for local prompt optimization")
        print_info("   💡 Download from: https://ollama.ai")
        warnings.append("Ollama not installed - prompt optimization disabled")
        return True  # Not a critical error


def print_final_report():
    """Print final initialization report"""
    print_header("📊 INITIALIZATION REPORT")

    if not errors:
        print_success("\n✅ ALL CHECKS PASSED!")
        print_info("\nYou're ready to start Squad API:\n")
        print_info("   1. Start Redis (if not running):")
        print_info("      redis-server\n")
        print_info("   2. Start API server:")
        print_info("      python src/main.py\n")
        print_info("   3. Test providers:")
        print_info("      python scripts/test_openrouter_fallback.py\n")
        print_info("   4. Access docs:")
        print_info("      http://localhost:8000/docs")

        if warnings:
            print_warn(f"\n⚠️  WARNINGS ({len(warnings)}):")
            for warning in warnings:
                print_warn(f"   - {warning}")

        return 0
    else:
        print_fail(f"\n❌ INITIALIZATION FAILED ({len(errors)} errors)")
        print_info("\nErrors found:")
        for error in errors:
            print_fail(f"   - {error}")

        print_info("\nFix the errors above and run again:")
        print_info("   python scripts/workflow-init.py")

        return 1

def main():
    """Main initialization workflow"""

    # Check if running from project root
    if not Path("src/main.py").exists():
        print_fail("❌ ERROR: Must run from project root directory")
        print_info(f"   Current directory: {Path.cwd()}")
        print_info("   Expected: squad api/")
        return 1

    print_header("🚀 SQUAD API - WORKFLOW INITIALIZATION")
    print_info("Starting environment validation and setup...\n")

    # Run all checks
    check_python()
    check_dependencies()
    check_env()
    check_redis()
    check_config_files()
    check_cost_optimization()
    check_openrouter_models()
    check_agents()
    check_imports()
    check_ollama()

    # Print final report
    return print_final_report()

if __name__ == "__main__":
    sys.exit(main())
