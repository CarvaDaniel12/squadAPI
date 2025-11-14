# Script para restaurar/criar arquivo .env com as chaves encontradas
# Usage: .\scripts\restore_env_file.ps1

$projectRoot = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $projectRoot ".env"

Write-Host "Procurando chaves de API configuradas..." -ForegroundColor Cyan
Write-Host ""

$apiKeyVars = @{
    'GROQ_API_KEY' = 'Groq'
    'CEREBRAS_API_KEY' = 'Cerebras'
    'GEMINI_API_KEY' = 'Gemini'
    'OPENROUTER_API_KEY' = 'OpenRouter'
    'ANTHROPIC_API_KEY' = 'Anthropic'
    'OPENAI_API_KEY' = 'OpenAI'
    'TOGETHER_API_KEY' = 'Together AI'
}

$foundKeys = @{}
$missingKeys = @()

foreach ($key in $apiKeyVars.Keys) {
    # Verificar em Process, User e Machine level
    $value = $null
    $value = [Environment]::GetEnvironmentVariable($key, [EnvironmentVariableTarget]::Process)
    if (-not $value) {
        $value = [Environment]::GetEnvironmentVariable($key, [EnvironmentVariableTarget]::User)
    }
    if (-not $value) {
        $value = [Environment]::GetEnvironmentVariable($key, [EnvironmentVariableTarget]::Machine)
    }
    
    if ($value) {
        $foundKeys[$key] = $value
        $preview = $value.Substring(0, [Math]::Min(20, $value.Length))
        Write-Host "[OK] $($apiKeyVars[$key]): $preview..." -ForegroundColor Green
    } else {
        $missingKeys += $key
        Write-Host "[MISSING] $($apiKeyVars[$key]): NAO ENCONTRADA" -ForegroundColor Yellow
    }
}

Write-Host ""

if ($foundKeys.Count -eq 0) {
    Write-Host "ERRO: Nenhuma chave encontrada!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Voce precisa configurar pelo menos uma chave:" -ForegroundColor Cyan
    Write-Host "   1. Crie um arquivo .env na raiz do projeto"
    Write-Host "   2. Adicione suas chaves:"
    Write-Host "      GROQ_API_KEY=sua_chave_aqui"
    Write-Host "      GEMINI_API_KEY=sua_chave_aqui"
    Write-Host "      etc."
    Write-Host ""
    Write-Host "   Ou defina como variaveis de ambiente do sistema"
    exit 1
}

# Criar conteudo do .env
$envContent = "# Squad API - Environment Variables`n"
$envContent += "# Arquivo .env gerado automaticamente`n"
$envContent += "# NAO commitar este arquivo no Git!`n`n"

foreach ($key in $apiKeyVars.Keys) {
    if ($foundKeys.ContainsKey($key)) {
        $envContent += "$key=$($foundKeys[$key])`n"
    } else {
        $envContent += "# $key=your_key_here`n"
    }
}

# Adicionar outras variaveis comuns
$envContent += "`n# Redis Configuration`n"
$envContent += "REDIS_URL=redis://localhost:6379/0`n`n"
$envContent += "# Logging`n"
$envContent += "LOG_LEVEL=INFO`n"

# Salvar arquivo
try {
    $envContent | Out-File -FilePath $envFile -Encoding UTF8 -NoNewline
    Write-Host "[OK] Arquivo .env criado em: $envFile" -ForegroundColor Green
    Write-Host ""
    Write-Host "Resumo:" -ForegroundColor Cyan
    Write-Host "   Chaves encontradas: $($foundKeys.Count)" -ForegroundColor Green
    Write-Host "   Chaves faltando: $($missingKeys.Count)" -ForegroundColor Yellow
    
    if ($missingKeys.Count -gt 0) {
        Write-Host ""
        Write-Host "Voce pode adicionar as chaves faltantes editando o arquivo .env:" -ForegroundColor Yellow
        foreach ($key in $missingKeys) {
            Write-Host "   $key=your_key_here"
        }
    }
    
    Write-Host ""
    Write-Host "Proximos passos:" -ForegroundColor Cyan
    Write-Host "   1. Revise o arquivo .env para confirmar que esta correto"
    Write-Host "   2. Adicione as chaves faltantes se necessario"
    Write-Host "   3. Execute: .\activate_squad_complete.ps1"
    
} catch {
    Write-Host ""
    Write-Host "ERRO ao criar arquivo .env: $_" -ForegroundColor Red
    exit 1
}
