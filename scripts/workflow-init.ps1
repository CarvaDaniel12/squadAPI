#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Squad API - Workflow Initialization Script

.DESCRIPTION
    Prepares the complete development environment:
    - Checks Python dependencies
    - Validates .env configuration
    - Tests Redis connection
    - Validates API providers
    - Checks cost optimization config
    - Runs health checks

.EXAMPLE
    .\scripts\workflow-init.ps1
#>

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Colors
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warn { Write-Host $args -ForegroundColor Yellow }
function Write-Fail { Write-Host $args -ForegroundColor Red }
function Write-Header {
    Write-Host ""
    Write-Host "="*80 -ForegroundColor Cyan
    Write-Host "  $args" -ForegroundColor Cyan
    Write-Host "="*80 -ForegroundColor Cyan
}

# Check if running from project root
if (-not (Test-Path ".\src\main.py")) {
    Write-Fail "❌ ERROR: Must run from project root directory"
    Write-Info "   Current directory: $PWD"
    Write-Info "   Expected: squad api/"
    exit 1
}

Write-Header "🚀 SQUAD API - WORKFLOW INITIALIZATION"
Write-Info "Starting environment validation and setup...`n"

# Track errors
$script:errors = @()
$script:warnings = @()

# ============================================================================
# STEP 1: Python Environment
# ============================================================================
Write-Header "1️⃣  PYTHON ENVIRONMENT"

try {
    $pythonVersion = python --version 2>&1
    Write-Success "✅ Python: $pythonVersion"

    # Check version
    if ($pythonVersion -notmatch "Python 3\.(1[0-2]|[9])") {
        Write-Warn "⚠️  Warning: Python 3.9+ recommended (found: $pythonVersion)"
        $script:warnings += "Python version may be incompatible"
    }
} catch {
    Write-Fail "❌ Python not found"
    $script:errors += "Python 3.9+ is required"
}

# ============================================================================
# STEP 2: Dependencies
# ============================================================================
Write-Header "2️⃣  CHECKING DEPENDENCIES"

$requiredPackages = @(
    "fastapi",
    "uvicorn",
    "redis",
    "python-dotenv",
    "aiohttp",
    "pydantic",
    "PyYAML"
)

$missingPackages = @()

foreach ($package in $requiredPackages) {
    try {
        $result = pip show $package 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✅ $package"
        } else {
            $missingPackages += $package
            Write-Fail "❌ $package (not installed)"
        }
    } catch {
        $missingPackages += $package
        Write-Fail "❌ $package (not installed)"
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Warn "`n⚠️  Missing packages detected. Install with:"
    Write-Info "   pip install -r requirements.txt"
    $script:errors += "Missing Python packages"
}

# ============================================================================
# STEP 3: Environment Configuration
# ============================================================================
Write-Header "3️⃣  ENVIRONMENT CONFIGURATION"

if (-not (Test-Path ".env")) {
    Write-Fail "❌ .env file not found"
    Write-Info "   Creating from .env.example..."

    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Success "✅ Created .env from template"
        Write-Warn "⚠️  IMPORTANT: Edit .env and add your API keys!"
    } else {
        Write-Fail "❌ .env.example not found"
        $script:errors += ".env file missing"
    }
} else {
    Write-Success "✅ .env file found"
}

# Check API keys in .env
if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw

    Write-Info "`n📋 API Keys Status:"

    $apiKeys = @{
        "GROQ_API_KEY" = "Groq (Free - 30 RPM)"
        "GEMINI_API_KEY" = "Gemini (Free - 15 RPM)"
        "CEREBRAS_API_KEY" = "Cerebras (Free - 30 RPM)"
        "OPENROUTER_API_KEY" = "OpenRouter (Free - 20 RPM, 46 models!)"
        "OPENAI_API_KEY" = "OpenAI (Paid - GPT-4o)"
        "ANTHROPIC_API_KEY" = "Anthropic (Paid - Claude 3.5)"
    }

    $hasAtLeastOne = $false

    foreach ($key in $apiKeys.Keys) {
        if ($envContent -match "$key=.+") {
            $value = ($envContent | Select-String "$key=(.+)" -AllMatches).Matches[0].Groups[1].Value
            if ($value -and $value -ne "your_key_here" -and $value.Length -gt 10) {
                Write-Success "   ✅ $($apiKeys[$key])"
                $hasAtLeastOne = $true
            } else {
                Write-Warn "   ⚠️  $($apiKeys[$key]) - NOT SET"
            }
        } else {
            Write-Warn "   ⚠️  $($apiKeys[$key]) - MISSING"
        }
    }

    if (-not $hasAtLeastOne) {
        Write-Fail ""
        Write-Fail "❌ No valid API keys found!"
        Write-Info "   Add at least one API key to .env"
        Write-Info "   Recommended: GROQ_API_KEY (free and fast)"
        $script:errors += "No API keys configured"
    }
}

# ============================================================================
# STEP 4: Redis Connection
# ============================================================================
Write-Header "4️⃣  REDIS CONNECTION"

try {
    # Try to connect using redis-cli
    $redisTest = redis-cli ping 2>&1
    if ($redisTest -eq "PONG") {
        Write-Success "✅ Redis is running (localhost:6379)"
    } else {
        throw "Redis not responding"
    }
} catch {
    Write-Fail "❌ Redis is not running"
    Write-Info ""
    Write-Info "   To start Redis:"
    Write-Info "   1. Open new PowerShell terminal"
    Write-Info "   2. Run: redis-server"
    Write-Info "   3. Keep it running in background"
    Write-Info ""
    Write-Info "   Or install Redis:"
    Write-Info "   - Windows: https://github.com/microsoftarchive/redis/releases"
    Write-Info "   - Or use WSL: sudo apt install redis-server"
    $script:errors += "Redis not running"
}

# ============================================================================
# STEP 5: Configuration Files
# ============================================================================
Write-Header "5️⃣  CONFIGURATION FILES"

$configFiles = @(
    "config/providers.yaml",
    "config/rate_limits.yaml",
    "config/agent_routing.yaml",
    "config/cost_optimization.yaml"
)

foreach ($file in $configFiles) {
    if (Test-Path $file) {
        Write-Success "✅ $file"
    } else {
        Write-Fail "❌ $file (missing)"
        $script:errors += "Missing config: $file"
    }
}

# ============================================================================
# STEP 6: Cost Optimization
# ============================================================================
Write-Header "6️⃣  COST OPTIMIZATION"

if (Test-Path "config/cost_optimization.yaml") {
    $costConfig = Get-Content "config/cost_optimization.yaml" -Raw

    if ($costConfig -match "daily_budget:\s*(\d+\.?\d*)") {
        $budget = $Matches[1]
        Write-Success "✅ Daily budget configured: `$$budget"
    }

    Write-Info ""
    Write-Info "💰 Cost Strategy:"
    Write-Info "   - Simple tasks → FREE providers only"
    Write-Info "   - Code tasks → OpenRouter Qwen3 480B (FREE!)"
    Write-Info "   - Complex tasks → OpenRouter DeepSeek 671B (FREE!)"
    Write-Info "   - Critical tasks → Claude 3.5 / GPT-4o (Paid)"
    Write-Info ""
    Write-Info "   Expected savings: 60-95% vs paid-only strategy"
}# ============================================================================
# STEP 7: OpenRouter Models
# ============================================================================
Write-Header "7️⃣  OPENROUTER FREE MODELS"

if (Test-Path "config/openrouter_free_models.json") {
    $models = Get-Content "config/openrouter_free_models.json" -Raw | ConvertFrom-Json
    Write-Success "✅ $($models.Count) FREE models cached"
    Write-Info ""
    Write-Info "   Top 3 models:"
    Write-Info "   1. Gemini 2.0 Flash (1M context)"
    Write-Info "   2. Qwen3 Coder 480B (262K context)"
    Write-Info "   3. KAT-Coder-Pro (256K context)"
    Write-Info ""
    Write-Info "   Auto-discovery: python scripts/discover_openrouter_models.py"
} else {
    Write-Warn "⚠️  OpenRouter models cache not found"
    Write-Info "   Run: python scripts/discover_openrouter_models.py"
}

# ============================================================================
# STEP 8: Agents
# ============================================================================
Write-Header "8️⃣  BMAD AGENTS"

if (Test-Path ".bmad/agents") {
    $agentCount = (Get-ChildItem ".bmad/agents/*.yaml" -ErrorAction SilentlyContinue).Count
    if ($agentCount -gt 0) {
        Write-Success "✅ $agentCount agents found in .bmad/agents/"
    } else {
        Write-Warn "⚠️  No agents found in .bmad/agents/"
        $script:warnings += "No BMAD agents configured"
    }
} else {
    Write-Warn "⚠️  .bmad/agents directory not found"
}

# ============================================================================
# STEP 9: Test Imports
# ============================================================================
Write-Header "9️⃣  PYTHON IMPORTS TEST"

Write-Info "Testing critical imports..."

$imports = @(
    "from src.agents.orchestrator import AgentOrchestrator",
    "from src.utils.cost_optimizer import CostOptimizer",
    "from src.providers.openrouter_provider import OpenRouterProvider",
    "from src.utils.openrouter_fallback import OpenRouterSmartFallback"
)

foreach ($import in $imports) {
    try {
        $result = python -c "$import; print('OK')" 2>&1
        if ($result -match "OK") {
            Write-Success "✅ $($import -replace 'from |import ', '')"
        } else {
            Write-Fail "❌ $($import -replace 'from |import ', '')"
            $script:errors += "Import failed: $import"
        }
    } catch {
        Write-Fail "❌ $($import -replace 'from |import ', '')"
        $script:errors += "Import failed: $import"
    }
}

# ============================================================================
# FINAL REPORT
# ============================================================================
Write-Header "📊 INITIALIZATION REPORT"

if ($script:errors.Count -eq 0) {
    Write-Success ""
    Write-Success "✅ ALL CHECKS PASSED!"
    Write-Info ""
    Write-Info "You're ready to start Squad API:"
    Write-Info ""
    Write-Info "   1. Start Redis (if not running):"
    Write-Info "      redis-server"
    Write-Info ""
    Write-Info "   2. Start API server:"
    Write-Info "      python src/main.py"
    Write-Info ""
    Write-Info "   3. Test providers:"
    Write-Info "      python scripts/test_openrouter_fallback.py"
    Write-Info ""
    Write-Info "   4. Access docs:"
    Write-Info "      http://localhost:8000/docs"

    if ($script:warnings.Count -gt 0) {
        Write-Warn ""
        $warnCount = $script:warnings.Count
        Write-Warn "WARNING: Found $warnCount issues"
        foreach ($warning in $script:warnings) {
            Write-Warn "   - $warning"
        }
    }

    exit 0

} else {
    Write-Fail ""
    $errCount = $script:errors.Count
    Write-Fail "INITIALIZATION FAILED: $errCount errors found"
    Write-Info ""
    Write-Info "Errors found:"
    foreach ($error in $script:errors) {
        Write-Fail "   - $error"
    }

    Write-Info ""
    Write-Info "Fix the errors above and run again"
    Write-Info 'Command: .\scripts\workflow-init.ps1'

    exit 1
}
