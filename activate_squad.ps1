# Squad API - PowerShell Activation Script
# This script provides better integration with Windows PowerShell
# Usage: .\activate_squad.ps1 (requires execution policy adjustment)

param(
    [switch]$SkipHealthCheck = $false,
    [switch]$NoClientTest = $false,
    [string]$CustomPort = "8000"
)

# Enable strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Color functions
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$ForegroundColor = "White"
    )
    Write-Host $Message -ForegroundColor $ForegroundColor
}

function Write-Success { Write-ColorOutput $args[0] "Green" }
function Write-Warning { Write-ColorOutput $args[0] "Yellow" }
function Write-Error { Write-ColorOutput $args[0] "Red" }
function Write-Info { Write-ColorOutput $args[0] "Cyan" }

# Main activation logic
try {
    Clear-Host
    Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           🚀 SQUAD API - POWERSHELL ACTIVATION 🚀           ║
║                                                              ║
║  Multi-Agent LLM Orchestration Platform                     ║
║  Enhanced for Windows PowerShell Integration                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"@

    # Step 1: Environment validation
    Write-Info "[CHECK] Validating PowerShell environment..."

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

    # Check Docker
    try {
        $dockerVersion = docker --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✓ $dockerVersion found"
        } else {
            throw "Docker not found"
        }
    } catch {
        Write-Error "✗ Docker not found. Please install Docker Desktop"
        exit 1
    }

    Write-Host ""

    # Step 2: Health check
    if (-not $SkipHealthCheck) {
        Write-Info "[CHECK] Checking Squad API status..."
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:$CustomPort/health" -Method GET -TimeoutSec 2
            if ($response) {
                Write-Success "✓ Squad API already running at http://localhost:$CustomPort"
                $apiRunning = $true
            }
        } catch {
            Write-Info "ℹ Squad API not running, starting services..."
            $apiRunning = $false
        }
    }

    if ($apiRunning) {
        goto :showStatus
    }

    # Step 3: Start Docker services
    Write-Info "[START] Starting Docker Compose services..."
    try {
        docker-compose up -d --remove-orphans
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✓ Docker services started"
        } else {
            throw "Failed to start Docker services"
        }
    } catch {
        Write-Error "✗ Failed to start Docker services: $_"
        exit 1
    }

    # Wait for services
    Write-Info "[WAIT] Waiting for services to initialize..."
    Start-Sleep -Seconds 3

    # Step 4: Install dependencies
    Write-Info "[SETUP] Checking Python dependencies..."
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

    # Step 5: Start Squad API in new PowerShell window
    Write-Info "[START] Starting Squad API server..."
    $startCommand = {
        param($Port)
        Set-Location $PSScriptRoot
        $env:PYTHONPATH = "."
        Write-Host "Starting Squad API on port $Port..." -ForegroundColor Green
        python src/main.py
    }

    Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { $startCommand.invoke($CustomPort) }" -WindowStyle Normal

    # Step 6: Wait for API to be ready
    Write-Info "[WAIT] Waiting for Squad API to be ready..."
    $maxAttempts = 30
    $attempts = 0

    do {
        $attempts++
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:$CustomPort/health" -Method GET -TimeoutSec 2
            if ($response) {
                Write-Success "✓ Squad API is ready!"
                break
            }
        } catch {
            if ($attempts -eq $maxAttempts) {
                Write-Error "✗ Timeout waiting for API to start"
                exit 1
            }
            Write-Info "Waiting for API... ($attempts attempts)"
            Start-Sleep -Seconds 2
        }
    } while ($attempts -lt $maxAttempts)

    Write-Host ""

    # Step 7: Start client interface if requested
    if (-not $NoClientTest) {
        Write-Info "[START] Starting client test interface..."
        $clientCommand = {
            param($ApiPort)
            Set-Location $PSScriptRoot
            Write-Host "Testing Squad API connection..." -ForegroundColor Yellow
            python scripts/squad_client.py analyst "Hello! Are you ready to help me with development tasks?"
            Write-Host "`nPress any key to continue..." -ForegroundColor Gray
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        }

        Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { $clientCommand.invoke($CustomPort) }" -WindowStyle Normal
    }

    :showStatus
    Write-Host ""
    Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║                   ✅ SQUAD API IS READY! ✅                  ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Green

    Write-Host ""
    Write-Info "🌐 API Server:        http://localhost:$CustomPort"
    Write-Info "📚 Documentation:     http://localhost:$CustomPort/docs"
    Write-Info "🤖 Health Check:      curl http://localhost:$CustomPort/health"
    Write-Info "💰 Cost Monitoring:   curl http://localhost:$CustomPort/cost/stats"

    Write-Host ""
    Write-Info "🎯 AVAILABLE AGENTS:"
    Write-Host "  dev        - Code generation & debugging"
    Write-Host "  analyst    - Research & data analysis"
    Write-Host "  architect  - System design & architecture"
    Write-Host "  reviewer   - Code review & quality assurance"
    Write-Host "  qa         - Test design & validation"
    Write-Host "  pm         - Planning & project management"

    Write-Host ""
    Write-Info "📝 USAGE FROM OTHER PROJECTS:"
    Write-Host "  1. Copy squad_client_enhanced.py to your project"
    Write-Host "  2. Import: from squad_client_enhanced import SquadClient"
    Write-Host "  3. Use: squad = SquadClient()"
    Write-Host "  4. Call: response = squad.ask('dev', 'Create a Flask API')"

    Write-Host ""
    Write-Info "🎮 QUICK TESTS:"
    Write-Host "  • Test with: python scripts/squad_client.py dev 'Create a REST API'"
    Write-Host "  • Batch test: python scripts/test_all_agents.py"
    Write-Host "  • Status check: .\squad_status.ps1"

    Write-Host ""
    Write-Info "🛑 TO STOP: Use .\squad_stop.ps1 or stop the PowerShell windows"

    # Step 8: System status
    Write-Host ""
    Write-Info "[STATUS] Current system status:"

    # Check processes
    $pythonProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match "python" -and $_.CommandLine -match "main.py" }
    if ($pythonProcesses) {
        Write-Success "✓ API Server: RUNNING (PID: $($pythonProcesses[0].Id))"
    } else {
        Write-Error "✗ API Server: NOT FOUND"
    }

    # Check health endpoint
    try {
        $health = Invoke-RestMethod -Uri "http://localhost:$CustomPort/health" -Method GET -TimeoutSec 5
        Write-Success "✓ API Health: HEALTHY"
        Write-Info "  Response: $($health | ConvertTo-Json -Compress)"
    } catch {
        Write-Error "✗ API Health: FAILED"
    }

    Write-Host ""
    Write-Success "🚀 Squad API activation complete! Ready for integration with other projects."

} catch {
    Write-Error "Activation failed: $_"
    Write-Error "Check the logs above for details."
    Write-Host ""
    Write-Info "💡 Common solutions:"
    Write-Host "  • Ensure Docker Desktop is running"
    Write-Host "  • Check if ports $CustomPort, 6379, 5432 are available"
    Write-Host "  • Verify all dependencies are installed"
    Write-Host "  • Run as administrator if needed"
    exit 1
}
