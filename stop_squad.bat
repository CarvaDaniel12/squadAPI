@echo off
REM Squad API - Stop Script
REM Stops all running Squad API processes

echo ========================================
echo   Stopping Squad API
echo ========================================
echo.

REM Kill processes on port 8000
echo [INFO] Parando processos na porta 8000...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :8000 ^| findstr LISTENING') do (
    echo Parando processo %%a...
    taskkill /F /PID %%a >nul 2>&1 && echo [OK] Processo %%a parado || echo [AVISO] Nao foi possivel parar processo %%a
)

echo.
echo [OK] Limpeza concluida!
echo.
timeout /t 2 >nul
