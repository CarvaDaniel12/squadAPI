# Squad API - Complete PowerShell Multi-Terminal Activation System
# Enhanced terminal management for Windows PowerShell
# Usage: .\activate_squad_complete.ps1

param(
    [switch]$SkipHealthCheck = $false,
    [switch]$NoClientTest = $false,
    [string]$CustomPort = "8000",
    [switch]$SkipLogTerminal = $false,
    [switch]$FullStack = $false
)

# Enable strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Configuration
$script:SQUAD_PROJECT_DIR = Get-Location
$script:API_PORT = $CustomPort
$script:REDIS_PORT = 6379
$script:GRAFANA_PORT = 3000
$script:PROMETHEUS_PORT = 9090
$script:MAX_RETRIES = 30

# Color functions
function Write-ColorOutput {
    param([string]$Message, [string]$ForegroundColor = "White")
    Write-Host $Message -ForegroundColor $ForegroundColor
}

function Write-Success { Write-ColorOutput $args[0] "Green" }
function Write-Warning { Write-ColorOutput $args[0] "Yellow" }
function Write-Error { Write-ColorOutput $args[0] "Red" }
function Write-Info { Write-ColorOutput $args[0] "Cyan" }
function Write-Banner { Write-ColorOutput $args[0] "Magenta" }

# Terminal management functions
function Start-TerminalWindow {
    param(
        [string]$Title,
        [string]$Command,
        [string]$WorkingDirectory = $script:SQUAD_PROJECT_DIR
    )

    # Collect environment variables from current session
    $envVars = @{}
    $apiKeyVars = @('GROQ_API_KEY', 'CEREBRAS_API_KEY', 'GEMINI_API_KEY', 'OPENROUTER_API_KEY', 'ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'TOGETHER_API_KEY', 'REDIS_URL')
    
    foreach ($var in $apiKeyVars) {
        $value = [Environment]::GetEnvironmentVariable($var, [EnvironmentVariableTarget]::Process)
        if (-not $value) {
            $value = [Environment]::GetEnvironmentVariable($var, [EnvironmentVariableTarget]::User)
        }
        if (-not $value) {
            $value = [Environment]::GetEnvironmentVariable($var, [EnvironmentVariableTarget]::Machine)
        }
        if ($value) {
            $envVars[$var] = $value
        }
    }
    
    # Also check for .env file and load it
    $envFile = Join-Path $WorkingDirectory ".env"
    $envFileContent = ""
    if (Test-Path $envFile) {
        Write-Info "Loading environment variables from .env file..."
        Get-Content $envFile | ForEach-Object {
            if ($_ -match '^\s*([^#][^=]+)\s*=\s*(.+)\s*$') {
                $key = $matches[1].Trim()
                $val = $matches[2].Trim()
                if (-not $envVars.ContainsKey($key)) {
                    $envVars[$key] = $val
                }
            }
        }
    }
    
    # Build environment variable setting commands
    $envSetCommands = ""
    foreach ($key in $envVars.Keys) {
        $val = $envVars[$key] -replace "'", "''"  # Escape single quotes
        $envSetCommands += "[Environment]::SetEnvironmentVariable('$key', '$val', 'Process'); "
    }
    
    # Set PYTHONPATH
    $pythonPath = $WorkingDirectory
    if ($env:PYTHONPATH) {
        $pythonPath = "$env:PYTHONPATH;$WorkingDirectory"
    }
    
    # Build the PowerShell command with proper escaping
    $commandBlock = "Set-Location '$WorkingDirectory'; " +
                    "`$env:PYTHONPATH = '$pythonPath'; " +
                    "$envSetCommands" +
                    "$Command; " +
                    "Write-Host ''; " +
                    "Write-Host 'Press any key to continue...' -ForegroundColor Gray; " +
                    "`$null = `$Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')"
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { $commandBlock }" -WindowStyle Normal
}

function Stop-TerminalWindows {
    Write-Info "[CLEANUP] Stopping Squad terminal windows..."

    # Stop PowerShell windows with Squad in title
    Get-Process -Name "powershell" -ErrorAction SilentlyContinue | Where-Object {
        $_.MainWindowTitle -match "SQUAD"
    } | Stop-Process -Force

    # Stop Cmd windows with Squad in title
    Get-Process -Name "cmd" -ErrorAction SilentlyContinue | Where-Object {
        $_.MainWindowTitle -match "SQUAD"
    } | Stop-Process -Force

    Write-Success "✓ Terminal windows stopped"
}

function Test-ApiHealth {
    param([int]$Port = $script:API_PORT)

    try {
        $response = Invoke-RestMethod -Uri "http://localhost:$Port/health" -Method GET -TimeoutSec 2
        return $response.status -eq "healthy"
    } catch {
        return $false
    }
}

function Test-RedisConnection {
    Write-Info "[CHECK] Testing Redis connection..."
    try {
        $redisTest = Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue
        if ($redisTest.TcpTestSucceeded) {
            Write-Success "✓ Redis is healthy on localhost:6379"
            return $true
        } else {
            Write-Warning "⚠ Redis not reachable on localhost:6379"
            Write-Info "ℹ The API will use in-memory cache (not persisted)"
            return $false
        }
    } catch {
        Write-Warning "⚠ Unable to check Redis connection"
        Write-Info "ℹ The API will use in-memory cache (not persisted)"
        return $false
    }
}

# Main activation logic
try {
    Clear-Host
    Write-Host @"
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║           🚀 SQUAD API - POWERSHELL MULTI-TERMINAL ACTIVATION 🚀                  ║
║                                                                                    ║
║  Complete multi-agent LLM orchestration with enhanced terminal management          ║
║                                                                                    ║
╚════════════════════════════════════════════════════════════════════════════════════╝
"@

    # Step 1: Environment validation
    Write-Info "[1/9] Validating PowerShell environment..."

    # Check Python
    try {
        $pythonVersion = python --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✓ $pythonVersion found"
        } else {
            throw "Python not found"
        }
    } catch {
        Write-Error "✗ Python not found. Please install Python 3.11+ from python.org"
        exit 1
    }

    # Check Redis (local installation)
    Write-Info "Checking Redis connection..."
    try {
        $redisTest = Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue
        if ($redisTest.TcpTestSucceeded) {
            Write-Success "✓ Redis is running on localhost:6379"
        } else {
            Write-Warning "⚠ Redis not reachable on localhost:6379"
            Write-Info "ℹ The API will work with in-memory cache (not persisted)"
            Write-Info "ℹ To enable Redis: install Redis locally or start Redis service"
        }
    } catch {
        Write-Warning "⚠ Unable to check Redis connection"
        Write-Info "ℹ The API will work with in-memory cache (not persisted)"
    }

    Write-Host ""

    # Step 2: Validate API Keys
    Write-Info "[2/9] Validating API keys..."
    $apiKeyVars = @{
        'GROQ_API_KEY' = 'Groq'
        'CEREBRAS_API_KEY' = 'Cerebras'
        'GEMINI_API_KEY' = 'Gemini'
        'OPENROUTER_API_KEY' = 'OpenRouter'
        'ANTHROPIC_API_KEY' = 'Anthropic'
    }
    
    $foundKeys = 0
    $missingKeys = @()
    
    # Check environment variables
    foreach ($key in $apiKeyVars.Keys) {
        $value = [Environment]::GetEnvironmentVariable($key, [EnvironmentVariableTarget]::Process)
        if (-not $value) {
            $value = [Environment]::GetEnvironmentVariable($key, [EnvironmentVariableTarget]::User)
        }
        if (-not $value) {
            $value = [Environment]::GetEnvironmentVariable($key, [EnvironmentVariableTarget]::Machine)
        }
        if ($value) {
            Write-Success "✓ $($apiKeyVars[$key]) API key found"
            $foundKeys++
        } else {
            $missingKeys += $apiKeyVars[$key]
        }
    }
    
    # Check .env file
    $envFile = Join-Path $script:SQUAD_PROJECT_DIR ".env"
    if (Test-Path $envFile) {
        Write-Info "ℹ .env file found at: $envFile"
        $envContent = Get-Content $envFile
        foreach ($key in $apiKeyVars.Keys) {
            $foundInEnv = $envContent | Where-Object { $_ -match "^\s*$key\s*=" }
            if ($foundInEnv -and -not [Environment]::GetEnvironmentVariable($key, [EnvironmentVariableTarget]::Process)) {
                Write-Success "✓ $($apiKeyVars[$key]) API key found in .env file"
                if ($missingKeys -contains $apiKeyVars[$key]) {
                    $foundKeys++
                    $missingKeys = $missingKeys | Where-Object { $_ -ne $apiKeyVars[$key] }
                }
            }
        }
    } else {
        Write-Warning "⚠ No .env file found - using system environment variables only"
    }
    
    if ($foundKeys -eq 0) {
        Write-Error "✗ No API keys found! Please set at least one API key."
        Write-Host ""
        Write-Info "To fix this:"
        Write-Host "  1. Create a .env file in the project root with your API keys:"
        Write-Host "     GROQ_API_KEY=your_key_here"
        Write-Host "     GEMINI_API_KEY=your_key_here"
        Write-Host "     etc."
        Write-Host ""
        Write-Host "  2. OR set environment variables in PowerShell:"
        Write-Host "     `$env:GROQ_API_KEY = 'your_key_here'"
        Write-Host ""
        Write-Host "  3. OR set them as system environment variables"
        Write-Host ""
        Write-Host "  See docs/API-KEYS-SETUP.md for more details"
        exit 1
    } elseif ($foundKeys -lt 2) {
        Write-Warning "⚠ Only $foundKeys API key(s) found. Consider adding more providers for better reliability."
    } else {
        Write-Success "✓ $foundKeys API key(s) found - ready to start"
    }
    
    Write-Host ""

    # Step 3: Health check
    if (-not $SkipHealthCheck) {
        Write-Info "[3/9] Checking Squad API status..."
        if (Test-ApiHealth) {
            Write-Success "✓ Squad API already running at http://localhost:$script:API_PORT"
            $apiRunning = $true
        } else {
            Write-Info "ℹ Starting fresh activation..."
            $apiRunning = $false
        }
    }

    if ($apiRunning) {
        goto :showStatus
    }

    # Step 4: Check Redis connection (optional)
    Write-Info "[4/9] Checking Redis connection..."
    $redisAvailable = Test-RedisConnection
    if (-not $redisAvailable) {
        Write-Info "ℹ Redis not available - API will use in-memory cache"
        Write-Info "ℹ This is fine for development/testing"
    }

    # Step 5: Install dependencies
    Write-Info "[5/9] Checking Python dependencies..."
    try {
        python -c "import uvicorn, fastapi, redis, requests" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✓ Dependencies ready"
        } else {
            Write-Info "Installing dependencies..."
            pip install -r requirements.txt
            Write-Success "✓ Dependencies installed"
        }
    } catch {
        Write-Error "✗ Failed to install dependencies: $_"
        exit 1
    }

    # Step 6: Start Terminal 1 - API Server
    Write-Info "[6/9] Starting Terminal 1 - API Server with Monitoring..."

    $serverCommand = @"
Write-Host 'Starting Squad API Server on port $script:API_PORT...' -ForegroundColor Green
Write-Host 'Press Ctrl+C to stop the server' -ForegroundColor Yellow
Write-Host ''
python src/main.py
"@

    Start-TerminalWindow -Title "SQUAD API - Terminal 1 (Server + Monitor)" -Command $serverCommand

    # Step 7: Wait for API to be ready
    Write-Info "[7/9] Waiting for Squad API to be ready..."
    $attempts = 0

    do {
        $attempts++
        if (Test-ApiHealth) {
            Write-Success "✓ Squad API is ready!"
            break
        }

        if ($attempts -eq $script:MAX_RETRIES) {
            Write-Error "✗ Timeout waiting for API to start"
            exit 1
        }

        Write-Info "Waiting for API... ($attempts/$script:MAX_RETRIES attempts)"
        Start-Sleep -Seconds 2
    } while ($attempts -lt $script:MAX_RETRIES)

    Write-Host ""

    # Step 8: Start Terminal 2 - Client Interface
    if (-not $NoClientTest) {
        Write-Info "[8/9] Starting Terminal 2 - Client Interface..."

        $clientCommand = @"
Write-Host 'Starting Squad Client Interface...' -ForegroundColor Green
Write-Host 'Test agent: analyst' -ForegroundColor Yellow
Write-Host ''
python scripts/squad_client.py analyst 'Hello! Ready for development tasks?'
"@

        Start-TerminalWindow -Title "SQUAD API - Terminal 2 (Client Interface)" -Command $clientCommand
    }

    # Step 9: Start Terminal 3 - Log Monitor
    if (-not $SkipLogTerminal) {
        Write-Info "[9/9] Starting Terminal 3 - Log Monitor & Status..."

        $logCommand = @"
Write-Host '=== SQUAD API LOG MONITOR ===' -ForegroundColor Cyan
Write-Host ''
Write-Host 'API Status:' -ForegroundColor Yellow
try {
    `$response = Invoke-RestMethod -Uri 'http://localhost:$script:API_PORT/health' -Method GET -TimeoutSec 5
    Write-Host (`$response | ConvertTo-Json -Compress)
} catch {
    Write-Host 'Unable to connect to API' -ForegroundColor Red
}
Write-Host ''
Write-Host 'Redis Status:' -ForegroundColor Yellow
try {
    `$redisTest = Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue
    if (`$redisTest.TcpTestSucceeded) {
        Write-Host 'Redis: Connected on localhost:6379' -ForegroundColor Green
    } else {
        Write-Host 'Redis: Not available (using in-memory cache)' -ForegroundColor Yellow
    }
} catch {
    Write-Host 'Redis: Unable to check' -ForegroundColor Gray
}
Write-Host ''
Write-Host 'Press Ctrl+C to exit' -ForegroundColor Gray
"@

        Start-TerminalWindow -Title "SQUAD API - Terminal 3 (Log Monitor)" -Command $logCommand
    }

    # Full stack components (optional - removed for Docker-free setup)
    if ($FullStack) {
        Write-Info "Full Stack Monitoring disabled (Docker-free mode)"
        Start-Sleep -Seconds 3

        Write-Host "🌐 Grafana: http://localhost:$script:GRAFANA_PORT (admin/admin)" -ForegroundColor Green
        Write-Host "📈 Prometheus: http://localhost:$script:PROMETHEUS_PORT" -ForegroundColor Green
    }

    :showStatus
    Write-Host ""
    Write-Banner @"
╔════════════════════════════════════════════════════════════════════════════════════╗
║                        ✅ POWERSHELL ACTIVATION COMPLETE! ✅                      ║
╚════════════════════════════════════════════════════════════════════════════════════╝
"@

    Write-Host ""
    Write-Info "🌐 API Server:         http://localhost:$script:API_PORT"
    Write-Info "📚 API Documentation:  http://localhost:$script:API_PORT/docs"
    Write-Info "🤖 Health Check:       curl http://localhost:$script:API_PORT/health"
    Write-Info "💰 Cost Monitoring:    curl http://localhost:$script:API_PORT/cost/stats"

    Write-Host ""
    Write-Info "📊 SERVICES:"
    Write-Host "  Redis:       localhost:6379 (optional - uses in-memory cache if not available)"

    Write-Host ""
    Write-Info "🖥️ ACTIVE TERMINALS:"
    Write-Host "  Terminal 1: SQUAD API - Server + Monitor"
    Write-Host "  Terminal 2: SQUAD CLIENT - Interactive Interface"
    Write-Host "  Terminal 3: SQUAD LOGS - Log Viewer + Status"

    Write-Host ""
    Write-Info "🎯 AVAILABLE AGENTS:"
    Write-Host "  dev        - Code generation & debugging"
    Write-Host "  analyst    - Research & data analysis"
    Write-Host "  architect  - System design & architecture"
    Write-Host "  reviewer   - Code review & quality assurance"
    Write-Host "  qa         - Test design & validation"
    Write-Host "  pm         - Planning & project management"

    Write-Host ""
    Write-Info "🚀 INTEGRATION FOR OTHER PROJECTS:"
    Write-Host "  1. Copy squad_client_enhanced.py to your project"
    Write-Host "  2. Import: from squad_client_enhanced import SquadClient"
    Write-Host "  3. Use: squad = SquadClient(base_url='http://localhost:$script:API_PORT')"
    Write-Host "  4. Call: response = squad.ask('dev', 'Create a Flask API')"

    Write-Host ""
    Write-Info "🎮 QUICK TESTS:"
    Write-Host "  Test agent:      python scripts/squad_client.py dev 'Create a REST API'"
    Write-Host "  Batch test:      python scripts/test_all_agents.py"
    Write-Host "  Load testing:    python scripts/load_test.py"
    Write-Host "  Integration:     python scripts/test_integration_basic.py"

    Write-Host ""
    Write-Info "🛑 TERMINATION:"
    Write-Host "  Quick stop:      .\squad_stop_complete.ps1"
    Write-Host "  Kill terminals:  Stop-TerminalWindows"
    Write-Host "  Stop API:        Press Ctrl+C in Terminal 1"

    # Final verification
    Write-Host ""
    Write-Info "[STATUS] System verification:"

    # Check processes
    $pythonProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue | Measure-Object
    if ($pythonProcesses.Count -gt 0) {
        Write-Success "Python processes: RUNNING (Count: $($pythonProcesses.Count))"
    } else {
        Write-Warning "Python processes: NOT FOUND"
    }

    # Check API health
    if (Test-ApiHealth) {
        Write-Success "✓ API Health: HEALTHY"
    } else {
        Write-Error "✗ API Health: FAILED"
    }

    # Check Redis connection
    Test-RedisConnection

    Write-Host ""
    Write-Success "🚀 PowerShell multi-terminal Squad API activation complete!"

} catch {
    Write-Error "Activation failed: $_"
    Write-Error "Check the logs above for details."
    Write-Host ""
    Write-Info "Common solutions:"
    Write-Host "  • Check if port $script:API_PORT is available"
    Write-Host "  • Verify all dependencies are installed: pip install -r requirements.txt"
    Write-Host "  • Check if Redis is running (optional): Test-NetConnection localhost -Port 6379"
    Write-Host "  • Run as administrator if needed"
    Write-Host "  • Use -ExecutionPolicy Bypass if execution is blocked"
    exit 1
}
