# Safe Development Workflow

**🎯 Objetivo:** Garantir que o código SEMPRE funciona conforme evoluímos na sprint ágil.

## 📋 Workflow Completo (Por Story)

### **FASE 1: Planejamento (5 min)**
```
1. Ler acceptance criteria da story
2. Identificar o que precisa de testes
3. Criar checklist mental: "O que pode quebrar?"
```

### **FASE 2: Red (Escrever Testes) (15-30 min)**
```bash
# Criar testes que FALHAM (Red)
touch tests/unit/test_new_feature.py

# Escrever testes baseados em acceptance criteria
pytest tests/unit/test_new_feature.py -v
# Resultado esperado: ❌ FALHOU (código não existe ainda)
```

**✅ Checkpoint:** Testes criados e falhando

### **FASE 3: Green (Implementar) (30-60 min)**
```bash
# Implementar feature mínima para passar testes
vim src/new_feature.py

# Rodar testes continuamente
pytest tests/unit/test_new_feature.py -v --tb=short
# Resultado esperado: ✅ PASSOU
```

**✅ Checkpoint:** Testes passando

### **FASE 4: Refactor (Melhorar) (15 min)**
```bash
# Melhorar código SEM quebrar testes
black src/new_feature.py
ruff check src/new_feature.py

# Verificar que testes AINDA passam
pytest tests/unit/test_new_feature.py -v
# Resultado: ✅ PASSOU (após refactor)
```

**✅ Checkpoint:** Código limpo, testes passando

### **FASE 5: Integration Check (10 min)**
```bash
# Rodar TODOS os testes (garantir não quebrou nada)
pytest tests/ -v --maxfail=5

# Verificar coverage não regrediu
pytest tests/ --cov=src --cov-report=term-missing
```

**✅ Checkpoint:** Suite completa passando

### **FASE 6: Pre-Commit Safety (5 min)**
```bash
# Windows
.\scripts\pre-commit-check.ps1

# Linux/Mac
./scripts/pre-commit-check.sh
```

**✅ Checkpoint:** Todos quality gates passaram

### **FASE 7: Commit (2 min)**
```bash
git add .
git commit -m "feat: Add new feature [Story X.Y]

- Implemented feature Z
- Added 10 unit tests
- Coverage: 75%
- All tests passing
"
```

**✅ Checkpoint:** Código commitado

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🚨 Quality Gates (NUNCA Ignorar)

### **Gate 1: Test Pass Rate**
```bash
pytest tests/ -v
```
**Rule:** 100% dos testes devem passar. Zero tolerância para falhas.

### **Gate 2: Code Coverage**
```bash
pytest tests/ --cov=src --cov-fail-under=70
```
**Rule:** Coverage mínimo de 70%. Ideal: 80%+.

### **Gate 3: Linting**
```bash
ruff check src/ tests/
```
**Rule:** Zero erros de linting. Warnings OK.

### **Gate 4: Formatting**
```bash
black --check src/ tests/
```
**Rule:** Código formatado consistentemente.

### **Gate 5: No Regressions**
```bash
pytest tests/integration/ -v
```
**Rule:** Testes de integração sempre passam.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📊 Métricas de Saúde (Track Daily)

### **Diário (Every Commit)**
- ✅ Test pass rate: 100%
- ✅ Coverage: >= 70%
- ✅ Lint errors: 0
- ✅ Build time: < 2 min

### **Semanal (End of Sprint)**
- ✅ Stories completed: X/Y
- ✅ Bugs introduced: < 2
- ✅ Tests added: +50
- ✅ Coverage delta: +5%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🔄 Git Workflow (Branch Strategy)

### **Estrutura de Branches**
```
main (production-ready)
  ↑
develop (integration)
  ↑
feature/epic-X-story-Y (your work)
```

### **Workflow Seguro**
```bash
# 1. Criar feature branch
git checkout develop
git pull origin develop
git checkout -b feature/epic-3-story-2

# 2. Trabalhar com commits pequenos
git add src/new_feature.py tests/unit/test_new_feature.py
git commit -m "feat: Add new feature [Story 3.2]"

# 3. Rodar safety check ANTES de push
.\scripts\pre-commit-check.ps1

# 4. Push para remote
git push origin feature/epic-3-story-2

# 5. Criar Pull Request
# - Revisar diff
# - Aguardar CI passar
# - Merge para develop

# 6. Deploy (quando sprint completa)
git checkout main
git merge develop
git push origin main
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🛠️ Ferramentas de Segurança

### **1. Watch Mode (Desenvolvimento Ativo)**
```bash
# Auto-run tests on file changes
pytest-watch tests/ src/
```

### **2. Coverage Delta Check**
```bash
# Compare coverage before/after
pytest tests/ --cov=src --cov-report=json
# Store baseline, compare on next run
```

### **3. Mutation Testing (Advanced)**
```bash
# Test your tests!
mutmut run --paths-to-mutate=src/
```

### **4. Performance Regression**
```bash
# Benchmark tests
pytest tests/ --benchmark-only
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🚀 Quick Commands (Copy-Paste Ready)

### **Full Safety Check (Before Commit)**
```powershell
# Windows
.\scripts\pre-commit-check.ps1 && git status
```

```bash
# Linux/Mac
./scripts/pre-commit-check.sh && git status
```

### **Fast Feedback Loop (During Development)**
```bash
# Run only tests for current feature
pytest tests/unit/test_my_feature.py -v -x

# Watch mode
pytest-watch tests/unit/test_my_feature.py
```

### **Full Regression Check (Before Merge)**
```bash
# Run everything
pytest tests/ -v --cov=src --cov-report=term-missing --maxfail=5
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📖 Best Practices

### **DO ✅**
1. **Test BEFORE code** (TDD)
2. **Commit frequently** (every 1-2h)
3. **Run pre-commit check** (always)
4. **Keep tests fast** (< 1s per test)
5. **Review coverage delta** (ogni commit)
6. **Fix broken tests immediately** (no deixar para depois)
7. **Write descriptive test names** (test_should_return_error_when_invalid_input)

### **DON'T ❌**
1. ❌ Skip tests ("will add later")
2. ❌ Commit broken code ("will fix tomorrow")
3. ❌ Ignore coverage drops
4. ❌ Disable linting rules
5. ❌ Push without running checks
6. ❌ Comment out failing tests
7. ❌ Merge with CI failing

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎯 Success Metrics

### **Individual Developer**
- Commits per day: 3-8
- Test pass rate: 100%
- Coverage contribution: Positive
- Bugs introduced: < 1 per sprint

### **Team**
- Sprint velocity: Increasing
- Bug escape rate: < 5%
- Test suite runtime: < 5 min
- Code review cycle: < 4 hours

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🆘 Troubleshooting

### **"Tests are taking too long"**
```bash
# Run only fast tests
pytest tests/unit/ -m "not slow"

# Parallelize
pytest tests/ -n auto
```

### **"Coverage keeps dropping"**
```bash
# Find untested code
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

### **"CI is failing but local works"**
```bash
# Replicate CI environment
docker run -it python:3.11 bash
pip install -r requirements.txt
pytest tests/
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📚 References

- [Test-Driven Development](https://martinfowler.com/bliki/TestDrivenDevelopment.html)
- [Git Workflow](https://www.atlassian.com/git/tutorials/comparing-workflows)
- [Continuous Integration](https://www.martinfowler.com/articles/continuousIntegration.html)
- [Code Coverage Best Practices](https://about.codecov.io/blog/code-coverage-best-practices/)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**🎯 Remember:** Safe development = Fast development!

Tests give you **confidence** to move fast without breaking things.

