# Pre-commit safety check (Windows PowerShell)
# Run this before EVERY commit to ensure quality

$ErrorActionPreference = "Stop"

Write-Host "🔍 PRE-COMMIT SAFETY CHECK" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan
Write-Host ""

# Navigate to project root
Set-Location $PSScriptRoot\..

# Activate venv if exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    . venv\Scripts\Activate.ps1
}

# 1. Linting
Write-Host "📝 Step 1/5: Running linters..." -ForegroundColor Yellow
try {
    ruff check src\ tests\
    Write-Host "✅ Linting passed" -ForegroundColor Green
} catch {
    Write-Host "❌ Linting failed! Fix errors before committing." -ForegroundColor Red
    exit 1
}
Write-Host ""

# 2. Code formatting
Write-Host "🎨 Step 2/5: Checking code formatting..." -ForegroundColor Yellow
try {
    black --check src\ tests\
    Write-Host "✅ Formatting OK" -ForegroundColor Green
} catch {
    Write-Host "❌ Formatting issues found! Run: black src\ tests\" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 3. Type checking
Write-Host "🔬 Step 3/5: Type checking..." -ForegroundColor Yellow
try {
    mypy src\ --ignore-missing-imports
} catch {
    Write-Host "⚠️  Type check warnings (non-blocking)" -ForegroundColor Yellow
}
Write-Host ""

# 4. Unit tests
Write-Host "🧪 Step 4/5: Running unit tests..." -ForegroundColor Yellow
try {
    pytest tests\unit\ -v --tb=short --maxfail=3
    Write-Host "✅ Unit tests passed" -ForegroundColor Green
} catch {
    Write-Host "❌ Unit tests failed! Fix before committing." -ForegroundColor Red
    exit 1
}
Write-Host ""

# 5. Coverage check
Write-Host "📊 Step 5/5: Checking test coverage..." -ForegroundColor Yellow
try {
    pytest tests\ --cov=src --cov-report=term-missing --cov-fail-under=70 -q
    Write-Host "✅ Coverage OK" -ForegroundColor Green
} catch {
    Write-Host "❌ Coverage below 70%! Add more tests." -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "✨ ALL CHECKS PASSED! Safe to commit." -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  git add ."
Write-Host "  git commit -m 'Your message'"
Write-Host "  git push"

