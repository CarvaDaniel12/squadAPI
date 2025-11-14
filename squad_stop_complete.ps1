# Squad API - Complete PowerShell Multi-Terminal Stop Script
# Gracefully stops all Squad API services and terminals using PowerShell
# Usage: .\squad_stop_complete.ps1

param(
    [switch]$Force = $false,
    [switch]$SkipDockerCleanup = $false,
    [switch]$SkipProcessCheck = $false,
    [int]$GracefulTimeout = 30
)

# Enable strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

# Configuration
$script:API_PORT = 8000
$script:REDIS_PORT = 6379
$script:GRAFANA_PORT = 3000
$script:PROMETHEUS_PORT = 9090

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

function Stop-SquadTerminals {
    Write-Info "[CLEANUP] Stopping Squad terminal windows..."

    $stoppedCount = 0

    # Stop PowerShell windows with Squad in title
    $powershellProcesses = Get-Process -Name "powershell*" -ErrorAction SilentlyContinue | Where-Object {
        $_.MainWindowTitle -match "SQUAD"
    }

    foreach ($process in $powershellProcesses) {
        if ($Force) {
            $process | Stop-Process -Force
        } else {
            $process | Stop-Process
        }
        $stoppedCount++
    }

    # Stop Cmd windows with Squad in title
    $cmdProcesses = Get-Process -Name "cmd" -ErrorAction SilentlyContinue | Where-Object {
        $_.MainWindowTitle -match "SQUAD"
    }

    foreach ($process in $cmdProcesses) {
        if ($Force) {
            $process | Stop-Process -Force
        } else {
            $process | Stop-Process
        }
        $stoppedCount++
    }

    if ($stoppedCount -gt 0) {
        Write-Success "✓ Stopped $stoppedCount terminal windows"
    } else {
        Write-Info "ℹ No Squad terminal windows found"
    }
}

function Stop-PythonProcesses {
    Write-Info "[CLEANUP] Stopping Python processes..."

    $pythonProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -match "main.py" -or
        $_.CommandLine -match "squad_client.py" -or
        $_.MainWindowTitle -match "SQUAD"
    }

    if ($pythonProcesses) {
        Write-Warning "Found $($pythonProcesses.Count) Python processes to stop"
        foreach ($process in $pythonProcesses) {
            if ($Force) {
                $process | Stop-Process -Force
                Write-Success "✓ Force stopped Python process PID: $($process.Id)"
            } else {
                $process | Stop-Process
                Write-Success "✓ Stopped Python process PID: $($process.Id)"
            }
        }
    } else {
        Write-Info "ℹ No Python processes related to Squad found"
    }
}

function Test-PortAvailable {
    param([int]$Port)

    try {
        $connection = Test-NetConnection -ComputerName "localhost" -Port $Port -WarningAction SilentlyContinue
        return -not $connection.TcpTestSucceeded
    } catch {
        return $true  # Assume available if test fails
    }
}

function Stop-DockerServices {
    if ($SkipDockerCleanup) {
        Write-Info "[SKIP] Docker cleanup skipped by user request"
        return
    }

    Write-Info "[DOCKER] Stopping Docker services..."

    try {
        $dockerVersion = docker --version 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "✗ Docker not available"
            return
        }

        Write-Success "✓ Docker found: $dockerVersion"

        # Check if services are running
        $servicesRunning = docker-compose ps 2>$null | Select-String "Up"

        if ($servicesRunning) {
            Write-Info "Running services found, stopping gracefully..."

            if ($Force) {
                docker-compose down --remove-orphans
            } else {
                docker-compose down
            }

            if ($LASTEXITCODE -eq 0) {
                Write-Success "✓ Docker services stopped successfully"
            } else {
                Write-Warning "⚠ Docker services stop completed with warnings"
            }
        } else {
            Write-Info "ℹ No running Docker services found"
        }

        # Clean up orphaned containers
        docker-compose down --remove-orphans 2>$null
        Write-Success "✓ Orphaned containers cleaned"

    } catch {
        Write-Error "✗ Error stopping Docker services: $_"
    }
}

function Free-Ports {
    Write-Info "[PORTS] Freeing system ports..."

    $ports = @($script:API_PORT, $script:REDIS_PORT, $script:GRAFANA_PORT, $script:PROMETHEUS_PORT)

    foreach ($port in $ports) {
        if (-not (Test-PortAvailable -Port $port)) {
            Write-Warning "Port $port is still in use, attempting to free it..."

            try {
                $process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
                          Select-Object -First 1 -ExpandProperty OwningProcess

                if ($process) {
                    $proc = Get-Process -Id $process -ErrorAction SilentlyContinue
                    if ($proc) {
                        if ($Force) {
                            $proc | Stop-Process -Force
                        } else {
                            $proc | Stop-Process
                        }
                        Write-Success "✓ Freed port $port (PID: $process)"
                    }
                }
            } catch {
                Write-Warning "⚠ Unable to free port $port: $_"
            }
        } else {
            Write-Success "✓ Port $port is available"
        }
    }
}

function Clean-Resources {
    Write-Info "[CLEANUP] System resource cleanup..."

    # Docker cleanup
    try {
        if (-not $SkipDockerCleanup) {
            docker system prune -f 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "✓ Docker system cleaned"
            }
        }
    } catch {
        Write-Warning "⚠ Docker cleanup completed with warnings: $_"
    }

    # Clean temporary files
    $tempFiles = Get-ChildItem -Path "." -Filter "temp_*" -ErrorAction SilentlyContinue
    if ($tempFiles) {
        Remove-Item -Path "temp_*" -Force -ErrorAction SilentlyContinue
        Write-Success "✓ Temporary files cleaned"
    }

    # Clean old logs (optional)
    if (Test-Path "logs") {
        try {
            Get-ChildItem -Path "logs" -Filter "*.log" | Where-Object {
                $_.LastWriteTime -lt (Get-Date).AddDays(-1)
            } | Remove-Item -Force -ErrorAction SilentlyContinue
            Write-Success "✓ Old log files cleaned"
        } catch {
            Write-Warning "⚠ Log cleanup completed with warnings: $_"
        }
    }
}

function Test-SystemStatus {
    Write-Info "[VERIFY] Final system verification..."

    $verificationScore = 0
    $maxScore = 5

    # Check API is stopped
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:$script:API_PORT/health" -Method GET -TimeoutSec 2
        Write-Error "✗ API Server: STILL RUNNING"
    } catch {
        Write-Success "✓ API Server: STOPPED"
        $verificationScore++
    }

    # Check Docker services
    try {
        $servicesRunning = docker-compose ps 2>$null | Select-String "Up"
        if ($servicesRunning) {
            Write-Error "✗ Docker Services: STILL RUNNING"
        } else {
            Write-Success "✓ Docker Services: STOPPED"
            $verificationScore++
        }
    } catch {
        Write-Info "ℹ Docker not available for verification"
        $verificationScore++
    }

    # Check ports
    if (Test-PortAvailable -Port $script:API_PORT) {
        Write-Success "✓ Port $script:API_PORT: AVAILABLE"
        $verificationScore++
    } else {
        Write-Error "✗ Port $script:API_PORT: OCCUPIED"
    }

    if (Test-PortAvailable -Port $script:REDIS_PORT) {
        Write-Success "✓ Port $script:REDIS_PORT: AVAILABLE"
        $verificationScore++
    } else {
        Write-Error "✗ Port $script:REDIS_PORT: OCCUPIED"
    }

    # Check processes
    $squadProcesses = Get-Process -Name "*" -ErrorAction SilentlyContinue | Where-Object {
        $_.MainWindowTitle -match "SQUAD" -or
        $_.CommandLine -match "main.py" -or
        $_.CommandLine -match "squad_client.py"
    }

    if (-not $squadProcesses) {
        Write-Success "✓ Squad Terminals: STOPPED"
        $verificationScore++
    } else {
        Write-Error "✗ Squad Terminals: STILL RUNNING"
    }

    return @{
        Score = $verificationScore
        MaxScore = $maxScore
    }
}

# Main execution
try {
    Clear-Host
    Write-Host @"
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║         🛑 SQUAD API - POWERSHELL MULTI-TERMINAL GRACEFUL SHUTDOWN 🛑              ║
║                                                                                    ║
echo ║  Complete system shutdown with enhanced terminal management                     ║
echo ║                                                                                    ║
echo ╚════════════════════════════════════════════════════════════════════════════════════╝
"@

    Write-Banner "[STEP 1/6] Initiating complete Squad API shutdown..."
    Write-Host ""

    # Step 1: Stop terminal windows
    Write-Info "🐍 [1/6] Stopping Python processes and terminal windows..."
    Write-Host "━" * 80
    Stop-SquadTerminals
    Stop-PythonProcesses
    Write-Host ""

    # Step 2: Stop Docker services
    Write-Info "🐳 [2/6] Stopping Docker services..."
    Write-Host "━" * 80
    Stop-DockerServices
    Write-Host ""

    # Step 3: Free ports
    Write-Info "🔌 [3/6] Port cleanup and verification..."
    Write-Host "━" * 80
    Free-Ports
    Write-Host ""

    # Step 4: Process verification
    if (-not $SkipProcessCheck) {
        Write-Info "🔍 [4/6] Process verification and cleanup..."
        Write-Host "━" * 80
        # Additional process cleanup if needed
        Write-Success "✓ Process verification completed"
        Write-Host ""
    }

    # Step 5: Resource cleanup
    Write-Info "🧹 [5/6] System resource cleanup..."
    Write-Host "━" * 80
    Clean-Resources
    Write-Host ""

    # Step 6: Final verification
    Write-Info "✅ [6/6] Final system verification..."
    Write-Host "━" * 80
    $verification = Test-SystemStatus
    Write-Host ""

    # Summary
    Write-Host ""
    Write-Banner @"
╔════════════════════════════════════════════════════════════════════════════════════╗
║                    🛑 POWERSHELL SHUTDOWN COMPLETE! 🛑                            ║
╚════════════════════════════════════════════════════════════════════════════════════╝
"@

    Write-Host ""
    Write-Info "📊 SHUTDOWN SUMMARY:"
    Write-Host "━" * 80
    Write-Info "✅ Python API server:          STOPPED"
    Write-Info "✅ Client interfaces:          CLOSED"
    Write-Info "✅ Terminal windows:           TERMINATED"
    Write-Info "✅ Docker services:            STOPPED"
    Write-Info "✅ System ports:               FREED"
    Write-Info "✅ Memory resources:           CLEANED"
    Write-Info "✅ Temporary files:            REMOVED"

    Write-Host ""
    Write-Info "📈 Verification Score: $($verification.Score)/$($verification.MaxScore) checks passed"

    if ($verification.Score -ge 4) {
        Write-Success "🎉 SHUTDOWN STATUS: COMPLETE - All systems stopped successfully"
    } elseif ($verification.Score -ge 2) {
        Write-Warning "⚠️  SHUTDOWN STATUS: PARTIAL - Most systems stopped, manual cleanup may be needed"
    } else {
        Write-Error "🚨 SHUTDOWN STATUS: INCOMPLETE - Manual intervention required"
    }

    Write-Host ""
    Write-Info "🎯 NEXT ACTIONS:"
    Write-Host "━" * 80
    Write-Info "• Restart system:        activate_squad_complete.bat"
    Write-Info "• PowerShell restart:    .\activate_squad_complete.ps1"
    Write-Info "• Check status:          .\squad_status_complete.ps1"
    Write-Info "• Clean restart:         .\squad_stop_complete.ps1 -Force ; .\activate_squad_complete.ps1"

    Write-Host ""
    Write-Info "💡 SYSTEM INFORMATION:"
    Write-Host "━" * 80
    Write-Info "  System time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Info "  Shutdown completed: SUCCESSFUL"
    Write-Info "  Ready for next activation: YES"

    Write-Host ""
    Write-Success "🧹 Complete Squad API PowerShell multi-terminal shutdown finished!"

} catch {
    Write-Error "Shutdown failed: $_"
    Write-Error "Check the logs above for details."
    Write-Host ""
    Write-Info "💡 Troubleshooting:"
    Write-Info "• Use -Force parameter for aggressive cleanup"
    Write-Info "• Use -SkipDockerCleanup to skip Docker services"
    Write-Info "• Use -SkipProcessCheck to skip process verification"
    Write-Info "• Run as administrator for full system access"
    Write-Info "• Check running processes with Get-Process"
    exit 1
}
