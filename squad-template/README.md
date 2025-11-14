# Squad API Template 🚀

> Sistema de templates automatizado para implementação rápida do Squad API em qualquer projeto

## 🎯 Visão Geral

Este template permite que você implemente o Squad API (orquestração multi-agente LLM) em qualquer projeto em **menos de 5 minutos**, com:

- ✅ **Instalação automática** com um comando
- ✅ **Configuração inteligente** de chaves API
- ✅ **Templates modulares** para diferentes casos de uso
- ✅ **Monitoramento integrado** (Prometheus + Grafana)
- ✅ **Rate limiting avançado** e fallback automático
- ✅ **Documentação automática** gerada

## 🚀 Uso Rápido

### 1. Instalar em qualquer projeto
```bash
# Clone o template
git clone https://github.com/your-org/squad-template.git

# Execute o instalador automático
cd squad-template
python install.py --project_name="meu-projeto" --template="full-stack"
```

### 2. Configurar chaves API
```bash
# Script interativo para configurar chaves
python setup_api_keys.py
```

### 3. Iniciar
```bash
# Start completo (API + Redis + Monitoramento)
docker-compose up -d

# Ou modo desenvolvimento
python quickstart.py
```

## 📁 Templates Disponíveis

| Template | Descrição | Tempo Setup | Ideal Para |
|----------|-----------|-------------|------------|
| `basic` | API básica + 1 LLM provider | 2 min | Prototipagem |
| `full-stack` | Stack completo + monitoramento | 5 min | Produção |
| `microservices` | Arquitetura distribuída | 10 min | Enterprise |
| `serverless` | AWS Lambda + API Gateway | 7 min | Cloud-native |

## 🛠️ Estrutura Modular

```
squad-template/
├── core/                    # Componentes principais
│   ├── api/                # Endpoints FastAPI
│   ├── agents/             # Orquestração de agentes
│   ├── providers/          # Provedores LLM
│   └── rate-limit/         # Controle de taxa
├── templates/              # Templates de projeto
│   ├── basic/
│   ├── full-stack/
│   ├── microservices/
│   └── serverless/
├── scripts/                # Automação
│   ├── install.py          # Instalação automática
│   ├── setup_api_keys.py   # Configuração interativa
│   └── deploy.py           # Deploy automatizado
└── config/                 # Configurações
    ├── docker/
    ├── kubernetes/
    └── aws/
```

## ⚡ Configuração Automática

### Instalador Interativo
```bash
python install.py --interactive
```

Responde às perguntas e deixa tudo pronto:
- Tipo de template
- Provedores LLM desejados
- Configuração de monitoramento
- URLs e portas personalizadas

### Configuração Programática
```bash
# Para CI/CD
python install.py \
  --project_name="api-orders" \
  --template="full-stack" \
  --providers="groq,gemini,cerebras" \
  --monitoring="prometheus,grafana" \
  --auto-start=true
```

## 🔧 Personalização

### Adicionar novo provedor LLM
```python
# Em config/providers.yaml
my_provider:
  enabled: true
  model: "my-model-v1"
  api_key_env: "MY_PROVIDER_API_KEY"
  timeout: 30
  rpm_limit: 60
```

### Customizar agentes
```yaml
# Em .bmad/agents/
meu_especialista.yaml:
  role: "Especialista em Domain X"
  system_prompt: "Você é um especialista em..."
  capabilities:
    - "Análise de X"
    - "Processamento de Y"
```

### Configurar monitoramento
```yaml
# Em config/monitoring.yaml
alerts:
  - type: "slack"
    webhook: "${SLACK_WEBHOOK_URL}"
  - type: "email"
    recipients: ["admin@empresa.com"]
```

## 📊 Monitoramento Padrão

Cada projeto inclui:

- **Prometheus** (`http://localhost:9090`)
  - Métricas de performance
  - Taxa de requisições por provider
  - Custos e uso de tokens

- **Grafana** (`http://localhost:3000`)
  - Dashboards pré-configurados
  - Alertas automáticos
  - Relatórios de custo

## 🔒 Segurança

- **Rate limiting** por provedor
- **Sanitização PII** automática
- **Audit logs** completos
- **Health checks** em tempo real
- **SSL/TLS** para produção

## 📚 Casos de Uso

### 1. API de E-commerce
```bash
python install.py \
  --template="full-stack" \
  --agents="analyst,developer,reviewer" \
  --providers="groq,openrouter" \
  --features="pii-sanitization,audit-logs"
```

### 2. Sistema de BI
```bash
python install.py \
  --template="microservices" \
  --agents="data-scientist,analyst,visualizer" \
  --providers="gemini,claude" \
  --monitoring="enhanced"
```

### 3. App Mobile Backend
```bash
python install.py \
  --template="serverless" \
  --agents="developer,qa,reviewer" \
  --providers="groq,cerebras" \
  --deployment="aws-lambda"
```

## 🐛 Troubleshooting

### Problemas Comuns

**Redis não conecta**
```bash
# Verificar status
docker-compose ps redis

# Restart Redis
docker-compose restart redis

# Verificar logs
docker-compose logs redis
```

**Chaves API inválidas**
```bash
# Testar chaves
python scripts/test_api_keys.py

# Reconfigurar
python setup_api_keys.py --reset
```

**Portas ocupadas**
```bash
# Verificar uso
netstat -tulpn | grep :8000

# Alterar portas no .env
echo "API_PORT=8001" >> .env
```

## 🤝 Contribuir

1. Fork o repositório
2. Crie uma branch para sua feature
3. Execute os testes: `python -m pytest`
4. Submeta o PR

## 📄 Licença

MIT License - livre para uso comercial e pessoal

---

**🚀 Pronto para usar?** Execute `python install.py --interactive` e tenha seu Squad API rodando em minutos!
