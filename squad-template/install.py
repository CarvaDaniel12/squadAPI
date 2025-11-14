#!/usr/bin/env python3
"""
Squad API Template Installer
Instalação automática e configuração para qualquer projeto
"""

import os
import sys
import shutil
import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import jinja2

class SquadTemplateInstaller:
    def __init__(self):
        self.current_dir = Path.cwd()
        self.template_dir = Path(__file__).parent
        self.project_name = None
        self.template_type = "full-stack"
        self.providers = ["groq", "gemini", "cerebras"]
        self.monitoring = ["prometheus", "grafana"]
        self.features = []

    def parse_args(self):
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(
            description="Squad API Template Installer",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Exemplos de uso:
  %(prog)s --project_name="meu-projeto" --template="full-stack"
  %(prog)s --interactive
  %(prog)s --project_name="api-restaurante" --providers="groq,openrouter" --features="pii-sanitization,audit-logs"
            """
        )

        parser.add_argument(
            "--project_name", "-n",
            type=str,
            help="Nome do projeto para criar"
        )

        parser.add_argument(
            "--template", "-t",
            choices=["basic", "full-stack", "microservices", "serverless"],
            default="full-stack",
            help="Tipo de template a instalar"
        )

        parser.add_argument(
            "--providers", "-p",
            type=str,
            help="Provedores LLM (groq,gemini,cerebras,openrouter,claude)"
        )

        parser.add_argument(
            "--monitoring", "-m",
            type=str,
            help="Monitoramento (prometheus,grafana,datadog)"
        )

        parser.add_argument(
            "--features", "-f",
            type=str,
            help="Features adicionais (pii-sanitization,audit-logs,cost-optimization)"
        )

        parser.add_argument(
            "--interactive", "-i",
            action="store_true",
            help="Modo interativo para configuração"
        )

        parser.add_argument(
            "--auto-start", "-s",
            action="store_true",
            help="Iniciar automaticamente após instalação"
        )

        parser.add_argument(
            "--force", "-f",
            action="store_true",
            help="Sobrescrever projeto existente"
        )

        return parser.parse_args()

    def interactive_setup(self):
        """Setup interativo com perguntas"""
        print("🤖 Squad API Template Installer")
        print("=" * 50)

        # Nome do projeto
        self.project_name = input("Nome do projeto: ").strip()
        if not self.project_name:
            self.project_name = "meu-squad-api"

        # Tipo de template
        print("\nTipos de template disponíveis:")
        print("1. basic - API básica + 1 LLM provider (2 min)")
        print("2. full-stack - Stack completo + monitoramento (5 min)")
        print("3. microservices - Arquitetura distribuída (10 min)")
        print("4. serverless - AWS Lambda + API Gateway (7 min)")

        template_choice = input("Escolha (1-4) [full-stack]: ").strip()
        template_map = {"1": "basic", "2": "full-stack", "3": "microservices", "4": "serverless"}
        self.template_type = template_map.get(template_choice, "full-stack")

        # Provedores LLM
        print("\nProvedores LLM disponíveis:")
        available_providers = ["groq", "gemini", "cerebras", "openrouter", "claude"]
        print("Disponíveis:", ", ".join(available_providers))
        print("Recomendados: groq, gemini (gratuitos)")

        providers_input = input("Provedores [groq,gemini,cerebras]: ").strip()
        if providers_input:
            self.providers = [p.strip() for p in providers_input.split(",")]
        else:
            self.providers = ["groq", "gemini", "cerebras"]

        # Monitoramento
        print("\nOpções de monitoramento:")
        print("1. prometheus+grafana (padrão)")
        print("2. datadog")
        print("3. nenhum")

        monitoring_choice = input("Escolha (1-3) [1]: ").strip()
        if monitoring_choice == "2":
            self.monitoring = ["datadog"]
        elif monitoring_choice == "3":
            self.monitoring = []
        else:
            self.monitoring = ["prometheus", "grafana"]

        # Features
        print("\nFeatures adicionais:")
        print("1. pii-sanitization - Remoção de dados pessoais")
        print("2. audit-logs - Logs de auditoria completos")
        print("3. cost-optimization - Otimização de custos")
        print("4. rate-limits - Controle de taxa avançado")

        features_input = input("Features (números separados por vírgula): ").strip()
        if features_input:
            feature_map = {"1": "pii-sanitization", "2": "audit-logs", "3": "cost-optimization", "4": "rate-limits"}
            self.features = [feature_map[num.strip()] for num in features_input.split(",")]

        # Auto-start
        auto_start = input("\nIniciar automaticamente? (s/n) [s]: ").strip().lower()
        self.auto_start = auto_start != "n"

        print(f"\n✅ Configuração concluída!")
        print(f"Projeto: {self.project_name}")
        print(f"Template: {self.template_type}")
        print(f"Provedores: {', '.join(self.providers)}")
        print(f"Monitoramento: {', '.join(self.monitoring) if self.monitoring else 'nenhum'}")
        print(f"Features: {', '.join(self.features) if self.features else 'nenhuma'}")

    def validate_configuration(self):
        """Valida a configuração antes da instalação"""
        if not self.project_name:
            raise ValueError("Nome do projeto é obrigatório")

        if not self.template_type:
            raise ValueError("Tipo de template é obrigatório")

        # Verificar se projeto já existe
        if Path(self.project_name).exists() and not self.force:
            raise ValueError(f"Diretório '{self.project_name}' já existe. Use --force para sobrescrever")

        # Validar provedores
        valid_providers = ["groq", "gemini", "cerebras", "openrouter", "claude", "openai"]
        for provider in self.providers:
            if provider not in valid_providers:
                raise ValueError(f"Provedor inválido: {provider}")

        # Validar template
        valid_templates = ["basic", "full-stack", "microservices", "serverless"]
        if self.template_type not in valid_templates:
            raise ValueError(f"Template inválido: {self.template_type}")

        print("✅ Configuração válida")

    def create_project_structure(self):
        """Cria a estrutura do projeto baseada no template"""
        project_path = Path(self.project_name)
        project_path.mkdir(exist_ok=True)

        print(f"📁 Criando estrutura do projeto: {project_path}")

        # Template Jinja2 para renderização
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir / "templates" / self.template_type)),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Contexto para template
        template_context = {
            "project_name": self.project_name,
            "providers": self.providers,
            "monitoring": self.monitoring,
            "features": self.features,
            "template_type": self.template_type
        }

        # Copiar template base
        self.copy_template_files(env, template_context, project_path)

        # Configurar arquivos específicos do template
        self.setup_template_specifics(project_path, template_context)

        print("✅ Estrutura do projeto criada")

    def copy_template_files(self, env: jinja2.Environment, context: Dict, project_path: Path):
        """Copia e renderiza arquivos do template"""
        template_path = self.template_dir / "templates" / self.template_type

        for file_path in template_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith("."):
                # Calcular caminho relativo no projeto
                rel_path = file_path.relative_to(template_path)

                # Renderizar nome do arquivo se necessário
                if rel_path.suffix in [".j2", ".jinja"]:
                    template_name = str(rel_path.with_suffix(""))
                    rendered_name = env.from_string(template_name).render(context)
                    target_path = project_path / rendered_name
                else:
                    target_path = project_path / rel_path

                # Criar diretório se não existir
                target_path.parent.mkdir(parents=True, exist_ok=True)

                # Renderizar conteúdo se for template
                if file_path.suffix in [".j2", ".jinja"]:
                    template = env.get_template(str(rel_path.with_suffix("")))
                    content = template.render(context)
                    target_path.write_text(content)
                else:
                    # Copiar arquivo diretamente
                    shutil.copy2(file_path, target_path)

    def setup_template_specifics(self, project_path: Path, context: Dict):
        """Configurações específicas do template"""
        if self.template_type == "serverless":
            # Configurar para AWS Lambda
            self.setup_serverless_config(project_path, context)
        elif self.template_type == "microservices":
            # Configurar para microservices
            self.setup_microservices_config(project_path, context)

        # Configurar Python package
        self.setup_python_package(project_path, context)

    def setup_serverless_config(self, project_path: Path, context: Dict):
        """Configuração específica para serverless"""
        serverless_config = {
            "service": context["project_name"],
            "provider": {
                "name": "aws",
                "runtime": "python3.9",
                "region": "us-east-1",
                "memorySize": 512,
                "timeout": 30
            },
            "functions": {
                "api": {
                    "handler": "src/main.handler",
                    "events": [
                        {
                            "http": {
                                "path": "/{proxy+}",
                                "method": "ANY"
                            }
                        }
                    ]
                }
            }
        }

        (project_path / "serverless.yml").write_text(yaml.dump(serverless_config, default_flow_style=False))

    def setup_microservices_config(self, project_path: Path, context: Dict):
        """Configuração específica para microservices"""
        # Configuração de Kubernetes
        k8s_dir = project_path / "kubernetes"
        k8s_dir.mkdir(exist_ok=True)

        # Deployment template
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": context["project_name"]},
            "spec": {
                "replicas": 3,
                "selector": {"matchLabels": {"app": context["project_name"]}},
                "template": {
                    "metadata": {"labels": {"app": context["project_name"]}},
                    "spec": {
                        "containers": [{
                            "name": context["project_name"],
                            "image": "python:3.9-slim",
                            "ports": [{"containerPort": 8000}]
                        }]
                    }
                }
            }
        }

        (k8s_dir / "deployment.yaml").write_text(yaml.dump(deployment, default_flow_style=False))

    def setup_python_package(self, project_path: Path, context: Dict):
        """Configura como package Python"""
        # Setup.py
        setup_py = f'''
from setuptools import setup, find_packages

setup(
    name="{context["project_name"]}",
    version="0.1.0",
    description="Squad API - {context["template_type"]} template",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "redis",
        "pyyaml",
        "python-dotenv",
    ],
    extras_require={{
        "providers-{'-'.join(context["providers"])}": [],
        "monitoring-{'-'.join(context["monitoring"]) if context["monitoring"] else "none"}": [],
    }},
    python_requires=">=3.9",
)
'''
        (project_path / "setup.py").write_text(setup_py)

    def generate_configuration_files(self):
        """Gera arquivos de configuração personalizados"""
        project_path = Path(self.project_name)

        # .env template
        self.generate_env_file(project_path)

        # providers.yaml
        self.generate_providers_config(project_path)

        # rate_limits.yaml
        self.generate_rate_limits_config(project_path)

        # docker-compose.yml
        self.generate_docker_compose(project_path)

    def generate_env_file(self, project_path: Path):
        """Gera arquivo .env.example"""
        env_content = f'''# Squad API - {self.project_name}
# Gerado automaticamente pelo Squad Template Installer

# ==================================
# LLM Provider API Keys
# ==================================
'''

        # Adicionar chaves para provedores selecionados
        for provider in self.providers:
            if provider == "groq":
                env_content += f'''GROQ_API_KEY=your_groq_api_key_here
# Get at: https://console.groq.com/keys
'''
            elif provider == "gemini":
                env_content += f'''GEMINI_API_KEY=your_gemini_api_key_here
# Get at: https://aistudio.google.com/app/apikey
'''
            elif provider == "cerebras":
                env_content += f'''CEREBRAS_API_KEY=your_cerebras_api_key_here
# Get at: https://cloud.cerebras.ai/
'''
            elif provider == "openrouter":
                env_content += f'''OPENROUTER_API_KEY=your_openrouter_api_key_here
# Get at: https://openrouter.ai/keys
'''
            elif provider == "claude":
                env_content += f'''ANTHROPIC_API_KEY=your_anthropic_api_key_here
# Get at: https://console.anthropic.com/
'''
            elif provider == "openai":
                env_content += f'''OPENAI_API_KEY=your_openai_api_key_here
# Get at: https://platform.openai.com/api-keys
'''

        env_content += f'''
# ==================================
# Database Configuration
# ==================================
REDIS_URL=redis://localhost:6379
POSTGRES_PASSWORD=dev_password_CHANGE_IN_PRODUCTION
DATABASE_URL=postgresql://squad:dev_password@localhost:5432/{self.project_name}

# ==================================
# Application Configuration
# ==================================
LOG_LEVEL=INFO
ENVIRONMENT=dev
PROJECT_NAME={self.project_name}
'''

        # Adicionar configurações específicas por template
        if "monitoring" in self.monitoring:
            env_content += '''
# Monitoring
GRAFANA_PASSWORD=admin
'''

        if "pii-sanitization" in self.features:
            env_content += '''
# PII Sanitization
PII_DETECTION_ENABLED=true
PII_REDACTION_MODE=mask
'''

        if "audit-logs" in self.features:
            env_content += '''
# Audit Logs
AUDIT_LOG_ENABLED=true
AUDIT_LOG_LEVEL=INFO
AUDIT_LOG_RETENTION_DAYS=30
'''

        if "cost-optimization" in self.features:
            env_content += '''
# Cost Optimization
DAILY_BUDGET_USD=5.0
COST_OPTIMIZATION_ENABLED=true
FREE_TIER_ONLY=false
'''

        (project_path / ".env.example").write_text(env_content)

    def generate_providers_config(self, project_path: Path):
        """Gera configuração de provedores personalizada"""
        providers_config = {"providers": {}}

        for provider in self.providers:
            if provider == "groq":
                providers_config["providers"]["groq"] = {
                    "enabled": True,
                    "model": "llama-3.3-70b-versatile",
                    "api_key_env": "GROQ_API_KEY",
                    "timeout": 30,
                    "rpm_limit": 30,
                    "tpm_limit": 20000
                }
            elif provider == "gemini":
                providers_config["providers"]["gemini"] = {
                    "enabled": True,
                    "model": "gemini-2.0-flash-exp",
                    "api_key_env": "GEMINI_API_KEY",
                    "timeout": 30,
                    "rpm_limit": 15,
                    "tpm_limit": 1000000
                }
            elif provider == "cerebras":
                providers_config["providers"]["cerebras"] = {
                    "enabled": True,
                    "model": "llama3.1-8b",
                    "api_key_env": "CEREBRAS_API_KEY",
                    "timeout": 30,
                    "rpm_limit": 30,
                    "tpm_limit": 180000
                }
            elif provider == "openrouter":
                providers_config["providers"]["openrouter"] = {
                    "enabled": True,
                    "model": "openrouter/auto",
                    "api_key_env": "OPENROUTER_API_KEY",
                    "timeout": 45,
                    "rpm_limit": 20,
                    "tpm_limit": 200000
                }

        # Adicionar prompt optimizer se habilitado
        providers_config["prompt_optimizer"] = {
            "enabled": "ollama" in self.features,
            "runtime": "ollama",
            "endpoint": "http://localhost:11434",
            "model_path": "qwen3:8b"
        }

        (project_path / "config" / "providers.yaml").parent.mkdir(exist_ok=True)
        (project_path / "config" / "providers.yaml").write_text(yaml.dump(providers_config, default_flow_style=False))

    def generate_rate_limits_config(self, project_path: Path):
        """Gera configuração de rate limits"""
        rate_limits = {}

        for provider in self.providers:
            if provider in ["groq", "cerebras"]:
                rate_limits[provider] = {
                    "rpm": 30,
                    "burst": 30,
                    "tokens_per_minute": 20000 if provider == "groq" else 180000
                }
            elif provider == "gemini":
                rate_limits[provider] = {
                    "rpm": 15,
                    "burst": 15,
                    "tokens_per_minute": 1000000
                }
            elif provider == "openrouter":
                rate_limits[provider] = {
                    "rpm": 20,
                    "burst": 20,
                    "tokens_per_minute": 200000
                }

        (project_path / "config" / "rate_limits.yaml").parent.mkdir(exist_ok=True)
        (project_path / "config" / "rate_limits.yaml").write_text(yaml.dump(rate_limits, default_flow_style=False))

    def generate_docker_compose(self, project_path: Path):
        """Gera docker-compose.yml personalizado"""
        services = {
            "version": "3.8",
            "networks": {
                "backend": {"driver": "bridge"},
                "frontend": {"driver": "bridge"}
            },
            "volumes": {
                "redis_data": {"driver": "local"},
                "postgres_data": {"driver": "local"}
            },
            "services": {}
        }

        # Redis (sempre incluído)
        services["services"]["redis"] = {
            "image": "redis:7-alpine",
            "container_name": f"{self.project_name}-redis",
            "ports": ["6379:6379"],
            "volumes": ["redis_data:/data"],
            "networks": ["backend"]
        }

        # API Principal
        api_service = {
            "build": {"context": ".", "dockerfile": "Dockerfile"},
            "container_name": f"{self.project_name}-api",
            "ports": ["8000:8000"],
            "environment": [f"PROJECT_NAME={self.project_name}"],
            "volumes": ["./src:/app/src:ro", "./config:/app/config:ro"],
            "networks": ["backend", "frontend"],
            "depends_on": ["redis"]
        }

        # Adicionar variáveis de ambiente para provedores
        for provider in self.providers:
            env_var = f"{provider.upper()}_API_KEY"
            api_service["environment"].append(f"{env_var}=${env_var}")

        services["services"]["api"] = api_service

        # Adicionar monitoramento se habilitado
        if "prometheus" in self.monitoring:
            services["services"]["prometheus"] = {
                "image": "prom/prometheus:v2.48.0",
                "container_name": f"{self.project_name}-prometheus",
                "ports": ["9090:9090"],
                "volumes": ["./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro"],
                "networks": ["backend", "frontend"]
            }

        if "grafana" in self.monitoring:
            services["services"]["grafana"] = {
                "image": "grafana/grafana:10.2.2",
                "container_name": f"{self.project_name}-grafana",
                "ports": ["3000:3000"],
                "environment": ["GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}"],
                "networks": ["frontend"],
                "depends_on": ["prometheus"] if "prometheus" in self.monitoring else []
            }

        compose_content = yaml.dump(services, default_flow_style=False)
        (project_path / "docker-compose.yml").write_text(compose_content)

    def create_startup_scripts(self):
        """Cria scripts de inicialização"""
        project_path = Path(self.project_name)

        # Script de start (Windows)
        start_bat = f'''@echo off
echo Iniciando {self.project_name}...
docker-compose up -d
echo.
echo 🎉 {self.project_name} iniciado!
echo API: http://localhost:8000
echo Docs: http://localhost:8000/docs
'''
        (project_path / "start.bat").write_text(start_bat)

        # Script de start (Linux/Mac)
        start_sh = f'''#!/bin/bash
echo "Iniciando {self.project_name}..."
docker-compose up -d
echo ""
echo "🎉 {self.project_name} iniciado!"
echo "API: http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
'''
        (project_path / "start.sh").write_text(start_sh)
        os.chmod(project_path / "start.sh", 0o755)

    def create_documentation(self):
        """Cria documentação personalizada"""
        project_path = Path(self.project_name)

        readme_content = f'''# {self.project_name} 🚀

> Squad API Template - {self.template_type} configurado para {self.project_name}

## 🏃‍♂️ Início Rápido

### 1. Configurar chaves API
```bash
cp .env.example .env
# Edite o .env com suas chaves API
```

### 2. Iniciar
```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

### 3. Testar
```bash
curl http://localhost:8000/health
```

## 📊 Configuração

### Provedores LLM Ativos
{chr(10).join([f"- {p.title()}" for p in self.providers])}

### Monitoramento
{chr(10).join([f"- {m.title()}" for m in self.monitoring]) if self.monitoring else "- Nenhum"}

### Features Ativas
{chr(10).join([f"- {f.replace('-', ' ').title()}" for f in self.features]) if self.features else "- Nenhuma"}

## 🔧 URLs de Acesso

- **API**: http://localhost:8000
- **Documentação**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

{f"- **Prometheus**: http://localhost:9090" if "prometheus" in self.monitoring else ""}
{f"- **Grafana**: http://localhost:3000 (admin/admin)" if "grafana" in self.monitoring else ""}

## 🚀 Próximos Passos

1. Configure suas chaves API no arquivo `.env`
2. Teste os endpoints: `python scripts/test_endpoints.py`
3. Personalize os agentes em `.bmad/agents/`
4. Configure alertas (se aplicável)

## 📞 Suporte

- Documentação: Ver pasta `docs/`
- Logs: `docker-compose logs -f api`
- Reset: `docker-compose down -v && docker-compose up -d`
'''

        (project_path / "README.md").write_text(readme_content)

    def run_installation(self):
        """Executa a instalação completa"""
        print("🚀 Iniciando instalação do Squad API Template...")

        try:
            # Validar configuração
            self.validate_configuration()

            # Criar estrutura
            self.create_project_structure()

            # Gerar configurações
            self.generate_configuration_files()

            # Criar scripts
            self.create_startup_scripts()

            # Criar documentação
            self.create_documentation()

            print(f"✅ Instalação concluída com sucesso!")
            print(f"📁 Projeto criado em: {self.project_name}/")
            print(f"🎯 Template: {self.template_type}")
            print(f"🔧 Provedores: {', '.join(self.providers)}")

            if self.auto_start:
                print("\n🚀 Iniciando o projeto...")
                os.chdir(self.project_name)
                subprocess.run(["docker-compose", "up", "-d"])
                print(f"✅ {self.project_name} iniciado!")
                print("📍 Acesse: http://localhost:8000/docs")

            return True

        except Exception as e:
            print(f"❌ Erro durante instalação: {e}")
            return False

def main():
    installer = SquadTemplateInstaller()

    try:
        # Parse argumentos
        args = installer.parse_args()

        # Configurar propriedades
        if args.project_name:
            installer.project_name = args.project_name
        if args.template:
            installer.template_type = args.template
        if args.providers:
            installer.providers = [p.strip() for p in args.providers.split(",")]
        if args.monitoring:
            installer.monitoring = [m.strip() for m in args.monitoring.split(",")]
        if args.features:
            installer.features = [f.strip() for f in args.features.split(",")]
        installer.auto_start = args.auto_start
        installer.force = args.force

        # Modo interativo
        if args.interactive:
            installer.interactive_setup()

        # Verificar parâmetros obrigatórios
        if not installer.project_name and not args.interactive:
            print("❌ Nome do projeto é obrigatório")
            print("💡 Use --project_name ou --interactive")
            sys.exit(1)

        # Executar instalação
        success = installer.run_installation()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n❌ Instalação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
