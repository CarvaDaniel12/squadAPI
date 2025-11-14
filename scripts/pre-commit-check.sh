#!/bin/bash
# Pre-commit safety check
# Run this before EVERY commit to ensure quality

set -e  # Exit on any error

echo "🔍 PRE-COMMIT SAFETY CHECK"
echo "=========================="
echo ""

# 1. Linting
echo "📝 Step 1/5: Running linters..."
ruff check src/ tests/ || {
    echo "❌ Linting failed! Fix errors before committing."
    exit 1
}
echo "✅ Linting passed"
echo ""

# 2. Code formatting
echo "🎨 Step 2/5: Checking code formatting..."
black --check src/ tests/ || {
    echo "❌ Formatting issues found! Run: black src/ tests/"
    exit 1
}
echo "✅ Formatting OK"
echo ""

# 3. Type checking (optional but recommended)
echo "🔬 Step 3/5: Type checking..."
mypy src/ --ignore-missing-imports || {
    echo "⚠️  Type check warnings (non-blocking)"
}
echo ""

# 4. Unit tests
echo "🧪 Step 4/5: Running unit tests..."
pytest tests/unit/ -v --tb=short --maxfail=3 || {
    echo "❌ Unit tests failed! Fix before committing."
    exit 1
}
echo "✅ Unit tests passed"
echo ""

# 5. Coverage check
echo "📊 Step 5/5: Checking test coverage..."
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=70 -q || {
    echo "❌ Coverage below 70%! Add more tests."
    exit 1
}
echo "✅ Coverage OK"
echo ""

echo "✨ ALL CHECKS PASSED! Safe to commit."
echo ""
echo "Next steps:"
echo "  git add ."
echo "  git commit -m 'Your message'"
echo "  git push"

