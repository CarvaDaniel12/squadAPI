# Helper script to create .env file from environment variables
# Usage: .\scripts\create_env_file.ps1

$projectRoot = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $projectRoot ".env"

Write-Host "Creating .env file from environment variables..." -ForegroundColor Cyan
Write-Host ""

$apiKeyVars = @{
    'GROQ_API_KEY' = 'Groq API Key'
    'CEREBRAS_API_KEY' = 'Cerebras API Key'
    'GEMINI_API_KEY' = 'Gemini API Key'
    'OPENROUTER_API_KEY' = 'OpenRouter API Key'
    'ANTHROPIC_API_KEY' = 'Anthropic API Key'
    'OPENAI_API_KEY' = 'OpenAI API Key'
    'TOGETHER_API_KEY' = 'Together AI API Key'
    'REDIS_URL' = 'Redis URL'
}

$envContent = @"
# Squad API - Environment Variables
# Generated automatically by create_env_file.ps1
# DO NOT commit this file to version control!

"@

$foundCount = 0
foreach ($key in $apiKeyVars.Keys) {
    # Check Process, User, and Machine level environment variables
    $value = [Environment]::GetEnvironmentVariable($key, [EnvironmentVariableTarget]::Process)
    if (-not $value) {
        $value = [Environment]::GetEnvironmentVariable($key, [EnvironmentVariableTarget]::User)
    }
    if (-not $value) {
        $value = [Environment]::GetEnvironmentVariable($key, [EnvironmentVariableTarget]::Machine)
    }
    
    if ($value) {
        $envContent += "$key=$value`n"
        Write-Host "✓ Found $($apiKeyVars[$key])" -ForegroundColor Green
        $foundCount++
    } else {
        $envContent += "# $key=your_key_here`n"
        Write-Host "✗ Missing $($apiKeyVars[$key])" -ForegroundColor Yellow
    }
}

# Add other common environment variables
$otherVars = @{
    'REDIS_URL' = 'redis://localhost:6379/0'
    'LOG_LEVEL' = 'INFO'
}

foreach ($key in $otherVars.Keys) {
    if ($envContent -notmatch "$key=") {
        $value = [Environment]::GetEnvironmentVariable($key, [EnvironmentVariableTarget]::Process)
        if (-not $value) {
            $value = [Environment]::GetEnvironmentVariable($key, [EnvironmentVariableTarget]::User)
        }
        if (-not $value) {
            $value = [Environment]::GetEnvironmentVariable($key, [EnvironmentVariableTarget]::Machine)
        }
        
        if ($value) {
            $envContent += "$key=$value`n"
        } else {
            $envContent += "$key=$($otherVars[$key])`n"
        }
    }
}

# Write to file
try {
    $envContent | Out-File -FilePath $envFile -Encoding UTF8 -NoNewline
    Write-Host ""
    Write-Host "✓ .env file created at: $envFile" -ForegroundColor Green
    Write-Host ""
    
    if ($foundCount -eq 0) {
        Write-Host "⚠ WARNING: No API keys found in environment variables!" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Please edit $envFile and add your API keys manually:" -ForegroundColor Cyan
        Write-Host "  GROQ_API_KEY=your_key_here"
        Write-Host "  GEMINI_API_KEY=your_key_here"
        Write-Host "  etc."
    } elseif ($foundCount -lt 3) {
        Write-Host "⚠ WARNING: Only $foundCount API key(s) found. Consider adding more for better reliability." -ForegroundColor Yellow
    } else {
        Write-Host "✓ $foundCount API key(s) found - you're good to go!" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Review the .env file to ensure all keys are correct"
    Write-Host "  2. Run .\activate_squad_complete.ps1 to start the Squad API"
    
} catch {
    Write-Host ""
    Write-Host "✗ Error creating .env file: $_" -ForegroundColor Red
    exit 1
}

