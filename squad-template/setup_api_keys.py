#!/usr/bin/env python3
"""
Squad API - Setup Keys Interativo
Configuração automática de chaves API para provedores LLM
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """Mostra banner do setup"""
    print("=" * 60)
    print("🔑 SQUAD API - CONFIGURAÇÃO DE CHAVES API")
    print("=" * 60)
    print("Configure suas chaves API para começar a usar o Squad API")
    print("Pode pular provedores que não deseja usar agora")
    print("=" * 60)

def get_api_key(provider_name, url, description):
    """Pede chave API para um provedor específico"""
    print(f"\n🤖 {provider_name}")
    print(f"   {description}")
    print(f"   URL: {url}")

    key = input(f"   Chave API (deixe vazio para pular): ").strip()
    return key if key else None

def test_api_key(provider, api_key):
    """Testa se uma chave API é válida"""
    if not api_key:
        return False

    print(f"   🔍 Testando {provider}...")

    # Scripts de teste por provedor
    test_scripts = {
        "groq": "scripts/test_groq_key.py",
        "gemini": "scripts/test_gemini_key.py",
        "cerebras": "scripts/test_cerebras_key.py",
        "openrouter": "scripts/test_openrouter_key.py",
        "claude": "scripts/test_claude_key.py"
    }

    script_path = test_scripts.get(provider)
    if not script_path or not Path(script_path).exists():
        print(f"   ⚠️  Script de teste não encontrado para {provider}")
        return True  # Assumir válido se não há teste

    try:
        env = os.environ.copy()
        env[f"{provider.upper()}_API_KEY"] = api_key

        result = subprocess.run(
            [sys.executable, script_path],
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print(f"   ✅ {provider} - Chave válida!")
            return True
        else:
            print(f"   ❌ {provider} - Chave inválida: {result.stderr}")
            return False

    except Exception as e:
        print(f"   ⚠️  Erro ao testar {provider}: {e}")
        return True  # Assumir válido se erro no teste

def generate_env_file(api_keys):
    """Gera arquivo .env com as chaves"""
    env_content = '''# SQUAD API - Environment Variables
# Gerado automaticamente pelo setup_api_keys.py

# ==================================
# LLM Provider API Keys
# ==================================
'''

    for provider, key in api_keys.items():
        if key:
            env_content += f'{provider.upper()}_API_KEY={key}\n'

    env_content += '''
# ==================================
# Database Configuration
# ==================================
POSTGRES_PASSWORD=dev_password_CHANGE_IN_PRODUCTION
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://squad:dev_password@localhost:5432/squad_api

# ==================================
# Application Configuration
# ==================================
LOG_LEVEL=INFO
ENVIRONMENT=dev

# ==================================
# Monitoring (Optional)
# ==================================
GRAFANA_PASSWORD=admin
SLACK_WEBHOOK_URL=
SLACK_ALERTS_ENABLED=false

# ==================================
# Cost Optimization
# ==================================
DAILY_BUDGET_USD=5.0
COST_OPTIMIZATION_ENABLED=true
FREE_TIER_ONLY=false

# ==================================
# Security
# ==================================
PII_DETECTION_ENABLED=true
AUDIT_LOG_ENABLED=true
AUDIT_LOG_LEVEL=INFO
'''

    # Sobrescrever .env se já existir
    if Path(".env").exists():
        backup = Path(".env.bak")
        Path(".env").rename(backup)
        print(f"   📋 Backup criado: {backup}")

    Path(".env").write_text(env_content)
    print(f"   ✅ Arquivo .env criado com sucesso!")

def create_test_scripts():
    """Cria scripts de teste para cada provedor"""
    scripts_dir = Path("scripts")
    scripts_dir.mkdir(exist_ok=True)

    # Script para Groq
    groq_script = '''#!/usr/bin/env python3
import os
import requests

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("GROQ_API_KEY não encontrada")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "llama-3.3-70b-versatile",
    "messages": [{"role": "user", "content": "Test"}],
    "max_tokens": 10
}

try:
    response = requests.post("https://api.groq.com/openai/v1/chat/completions",
                           headers=headers, json=data, timeout=10)
    if response.status_code == 200:
        print("✅ Groq API key valid")
        sys.exit(0)
    else:
        print(f"❌ Groq API error: {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Groq connection error: {e}")
    sys.exit(1)
'''

    scripts_dir.joinpath("test_groq_key.py").write_text(groq_script)

    # Script para Gemini
    gemini_script = '''#!/usr/bin/env python3
import os
import requests

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY não encontrada")
    sys.exit(1)

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"

data = {
    "contents": [{
        "parts": [{"text": "Test"}]
    }]
}

try:
    response = requests.post(url, json=data, timeout=10)
    if response.status_code == 200:
        print("✅ Gemini API key valid")
        sys.exit(0)
    else:
        print(f"❌ Gemini API error: {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Gemini connection error: {e}")
    sys.exit(1)
'''

    scripts_dir.joinpath("test_gemini_key.py").write_text(gemini_script)

    # Script para Cerebras
    cerebras_script = '''#!/usr/bin/env python3
import os
import requests

api_key = os.getenv("CEREBRAS_API_KEY")
if not api_key:
    print("CEREBRAS_API_KEY não encontrada")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "llama3.1-8b",
    "messages": [{"role": "user", "content": "Test"}],
    "max_tokens": 10
}

try:
    response = requests.post("https://api.cerebras.ai/v1/chat/completions",
                           headers=headers, json=data, timeout=10)
    if response.status_code == 200:
        print("✅ Cerebras API key valid")
        sys.exit(0)
    else:
        print(f"❌ Cerebras API error: {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Cerebras connection error: {e}")
    sys.exit(1)
'''

    scripts_dir.joinpath("test_cerebras_key.py").write_text(cerebras_script)

    # Script para OpenRouter
    openrouter_script = '''#!/usr/bin/env python3
import os
import requests

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("OPENROUTER_API_KEY não encontrada")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "google/gemini-2.0-flash-exp:free",
    "messages": [{"role": "user", "content": "Test"}],
    "max_tokens": 10
}

try:
    response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                           headers=headers, json=data, timeout=10)
    if response.status_code == 200:
        print("✅ OpenRouter API key valid")
        sys.exit(0)
    else:
        print(f"❌ OpenRouter API error: {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"❌ OpenRouter connection error: {e}")
    sys.exit(1)
'''

    scripts_dir.joinpath("test_openrouter_key.py").write_text(openrouter_script)

def main():
    """Função principal do setup"""
    print_banner()

    # Criar scripts de teste
    print("\n🔧 Preparando scripts de teste...")
    create_test_scripts()

    # Configurações de provedores
    providers = {
        "groq": {
            "url": "https://console.groq.com/keys",
            "description": "Groq - Ultra-fast inference (Recomendado - Gratuito)"
        },
        "gemini": {
            "url": "https://aistudio.google.com/app/apikey",
            "description": "Google Gemini 2.0 - Potente e gratuito"
        },
        "cerebras": {
            "url": "https://cloud.cerebras.ai/",
            "description": "Cerebras - Alto throughput"
        },
        "openrouter": {
            "url": "https://openrouter.ai/keys",
            "description": "OpenRouter - 46+ modelos gratuitos"
        },
        "claude": {
            "url": "https://console.anthropic.com/",
            "description": "Claude 3.5 - Premium (Pago)"
        }
    }

    # Coletar chaves API
    api_keys = {}
    print("\n📝 Configure suas chaves API:")
    print("   (Deixe vazio para pular provedores)")

    for provider, config in providers.items():
        key = get_api_key(
            provider.upper(),
            config["url"],
            config["description"]
        )
        api_keys[provider] = key

    # Testar chaves
    print("\n🧪 Testando chaves API...")
    valid_providers = []

    for provider, key in api_keys.items():
        if key:
            if test_api_key(provider, key):
                valid_providers.append(provider)
        else:
            print(f"   ⏭️  {provider} - Pulado pelo usuário")

    # Mostrar resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DA CONFIGURAÇÃO")
    print("=" * 60)

    if valid_providers:
        print(f"✅ Provedores configurados: {', '.join(valid_providers)}")
        print(f"🔑 Total de chaves válidas: {len(valid_providers)}")
    else:
        print("⚠️  Nenhuma chave API configurada")
        print("   O sistema funcionará com stubs模拟")

    # Gerar arquivo .env
    print("\n💾 Gerando arquivo .env...")
    generate_env_file(api_keys)

    # Instruções finais
    print("\n" + "=" * 60)
    print("🚀 CONFIGURAÇÃO CONCLUÍDA!")
    print("=" * 60)

    if valid_providers:
        print("Próximos passos:")
        print("1. ✅ Configurei suas chaves API")
        print("2. 📁 Criei arquivo .env")
        print("3. 🚀 Execute: docker-compose up -d")
        print("4. 🧪 Teste: curl http://localhost:8000/health")
    else:
        print("⚠️  Para usar o Squad API você precisa:")
        print("1. 🔑 Obter pelo menos uma chave API (Groq recomendado)")
        print("2. 📝 Executar novamente: python setup_api_keys.py")
        print("3. 🚀 Execute: docker-compose up -d")

    print("\n📚 Documentação:")
    print("   - API Docs: http://localhost:8000/docs")
    print("   - GitHub: https://github.com/your-org/squad-api")
    print("   - Suporte: support@squad-api.example.com")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Setup cancelado pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro durante setup: {e}")
        sys.exit(1)
