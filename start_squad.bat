@echo off
title Squad API - Startup
cd /d "%~dp0"

echo ========================================
echo   SQUAD API - Starting
echo ========================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado! Instale Python 3.8+.
    pause
    exit /b 1
)
echo [OK] Python encontrado

REM Verificar .env
if not exist ".env" (
    echo [ERRO] Arquivo .env nao encontrado!
    echo Crie um arquivo .env com suas chaves de API
    pause
    exit /b 1
)
echo [OK] .env encontrado
echo.

REM Ativar venv
if not exist "venv\Scripts\activate.bat" (
    echo [AVISO] Criando ambiente virtual...
    python -m venv venv
    echo [OK] Ambiente virtual criado
)
echo [OK] Ativando ambiente virtual...
call venv\Scripts\activate.bat
echo.

REM Instalar/atualizar dependencias
echo [OK] Verificando e instalando dependencias...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.

REM Configurar PYTHONPATH
set PYTHONPATH=%~dp0
echo [OK] PYTHONPATH configurado para %PYTHONPATH%
echo.

REM Verificar se servidor ja esta rodando
netstat -an | findstr :8000 >nul
if not errorlevel 1 (
    echo [AVISO] Servidor ja esta rodando na porta 8000
    echo [AVISO] Encerrando processos existentes...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /PID %%a /F
    timeout /t 2 /nobreak >nul
)

echo [OK] Iniciando servidor Squad API...
echo [INFO] Servidor vai rodar em http://localhost:8000
echo [INFO] Documentacao disponivel em http://localhost:8000/docs
echo.

REM Iniciar servidor em background
start "SQUAD API - Server" cmd /k "cd /d %~dp0 && call venv\Scripts\activate.bat && set PYTHONPATH=%~dp0 && echo Aguardando servidor iniciar... && timeout /t 5 /nobreak >nul && python -c \"import uvicorn; print('Iniciando servidor Squad API...'); uvicorn.run('src.main:app', host='0.0.0.0', port=8000, log_level='info')\""

echo [OK] Aguardando servidor iniciar (10 segundos)...
timeout /t 10 /nobreak >nul

REM Testar se servidor esta funcionando
echo [OK] Testando servidor...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Servidor nao respondeu. Verifique os logs.
) else (
    echo [OK] Servidor funcionando corretamente!
    echo.
    echo [SUCCESS] Squad API esta rodando!
    echo [INFO] API: http://localhost:8000
    echo [INFO] Docs: http://localhost:8000/docs
    echo [INFO] Health: http://localhost:8000/health
    echo.
    echo Exemplos de uso:
    echo curl -X POST "http://localhost:8000/v1/agents/analyst" -H "Content-Type: application/json" -d "{\"prompt\": \"Olá! Como posso ajudar?\"}"
    echo.
)

echo Pressione qualquer tecla para continuar...
pause >nul
