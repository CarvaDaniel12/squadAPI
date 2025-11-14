"""
Project Scaffolding and File Structure Generator
Story: Creates appropriate project structures and file scaffolds

This module handles the creation of directory structures, file scaffolds,
and project organization based on specifications and technology stacks.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from .project_generator import ProjectType, ProjectSpec

logger = logging.getLogger(__name__)


class ProjectScaffolder:
    """
    Creates project directory structures and file scaffolds

    Generates appropriate directory layouts, base files, and scaffolding
    based on project type, technology stack, and specifications.
    """

    def __init__(self):
        """Initialize the scaffolder"""
        self.base_templates = self._load_base_templates()
        self.tech_scaffolds = self._load_tech_scaffolds()
        self.file_templates = self._load_file_templates()

    def create_project_structure(
        self,
        project_dir: Path,
        spec: ProjectSpec,
        generated_content: Dict[str, str] = None
    ) -> List[str]:
        """
        Create complete project structure and files

        Args:
            project_dir: Project directory path
            spec: Project specification
            generated_content: Optional pre-generated content to integrate

        Returns:
            List of created file paths
        """
        files_created = []

        try:
            # Create base directory structure
            structure = self._plan_project_structure(spec)
            files_created.extend(self._create_directories(project_dir, structure))

            # Generate scaffold files
            scaffold_files = self._generate_scaffold_files(project_dir, spec)
            files_created.extend(scaffold_files)

            # Integrate generated content
            if generated_content:
                content_files = self._integrate_generated_content(project_dir, spec, generated_content)
                files_created.extend(content_files)

            # Create project metadata and configuration files
            config_files = self._create_config_files(project_dir, spec)
            files_created.extend(config_files)

            logger.info(f"Created project structure with {len(files_created)} files in {project_dir}")

        except Exception as e:
            logger.error(f"Failed to create project structure: {e}")
            raise

        return files_created

    def _plan_project_structure(self, spec: ProjectSpec) -> Dict[str, Any]:
        """Plan the directory structure based on project type and tech stack"""
        structure = {
            'root': [],
            'directories': {},
            'files': {}
        }

        # Base structure for all projects
        base_structure = {
            'docs': {
                'directories': {'api': {}, 'guides': {}},
                'files': {'README.md': 'readme', 'CONTRIBUTING.md': 'contributing', 'LICENSE': 'license'}
            },
            'tests': {
                'directories': {'unit': {}, 'integration': {}, 'e2e': {}},
                'files': {'conftest.py': 'conftest_py', 'test_main.py': 'test_main'}
            },
            '.github': {
                'directories': {'workflows': {}},
                'files': {'ISSUE_TEMPLATE.md': 'issue_template', 'PULL_REQUEST_TEMPLATE.md': 'pr_template'}
            }
        }

        # Project-type specific structure
        type_specific = self._get_type_specific_structure(spec.project_type)
        base_structure.update(type_specific)

        # Technology-specific additions
        tech_specific = self._get_tech_specific_structure(spec.tech_stack)
        for key, value in tech_specific.items():
            if key in base_structure:
                self._merge_structures(base_structure[key], value)
            else:
                base_structure[key] = value

        return base_structure

    def _get_type_specific_structure(self, project_type: ProjectType) -> Dict[str, Any]:
        """Get structure specific to project type"""
        structures = {
            ProjectType.WEB_APP: {
                'frontend': {
                    'directories': {'src': {'components': {}, 'pages': {}, 'utils': {}}, 'public': {}},
                    'files': {
                        'package.json': 'package_json',
                        'vite.config.js': 'vite_config',
                        'tailwind.config.js': 'tailwind_config',
                        'src/index.html': 'html_index',
                        'src/main.jsx': 'main_jsx',
                        'src/App.jsx': 'app_jsx',
                        'src/App.css': 'app_css'
                    }
                },
                'backend': {
                    'directories': {'src': {'routes': {}, 'models': {}, 'middleware': {}}, 'config': {}},
                    'files': {
                        'server.js': 'server_js',
                        'src/app.js': 'app_js',
                        'src/routes/api.js': 'api_routes_js'
                    }
                }
            },

            ProjectType.API_SERVICE: {
                'api': {
                    'directories': {'src': {'routes': {}, 'models': {}, 'controllers': {}, 'middleware': {}}, 'tests': {}},
                    'files': {
                        'main.py': 'main_py',
                        'requirements.txt': 'requirements_txt',
                        'src/app.py': 'app_py',
                        'src/models.py': 'models_py',
                        'src/routes.py': 'routes_py',
                        'src/database.py': 'database_py'
                    }
                }
            },

            ProjectType.FULL_STACK: {
                'frontend': {
                    'directories': {'src': {'components': {}, 'pages': {}, 'hooks': {}, 'services': {}}, 'public': {}},
                    'files': {
                        'package.json': 'package_json',
                        'src/main.tsx': 'main_tsx',
                        'src/App.tsx': 'app_tsx',
                        'vite.config.ts': 'vite_config_ts'
                    }
                },
                'backend': {
                    'directories': {'src': {'routes': {}, 'models': {}, 'controllers': {}, 'services': {}}, 'migrations': {}},
                    'files': {
                        'package.json': 'package_json_backend',
                        'src/server.js': 'server_js',
                        'src/app.js': 'app_js',
                        'src/models/User.js': 'user_model_js'
                    }
                },
                'shared': {
                    'directories': {'types': {}, 'utils': {}},
                    'files': {'shared/types.ts': 'shared_types'}
                }
            },

            ProjectType.CLI_TOOL: {
                'src': {
                    'directories': {'commands': {}, 'utils': {}},
                    'files': {
                        'main.py': 'main_cli_py',
                        'cli.py': 'cli_py',
                        'requirements.txt': 'requirements_txt'
                    }
                }
            },

            ProjectType.LIBRARY: {
                'src': {
                    'directories': {},
                    'files': {
                        '__init__.py': 'lib_init_py',
                        'main.py': 'lib_main_py'
                    }
                },
                'examples': {
                    'directories': {},
                    'files': {'example.py': 'example_py'}
                }
            }
        }

        return structures.get(project_type, {})

    def _get_tech_specific_structure(self, tech_stack: List[str]) -> Dict[str, Any]:
        """Get structure additions based on technology stack"""
        additions = {}

        tech_lower = [tech.lower() for tech in tech_stack]

        # React additions
        if any('react' in tech for tech in tech_lower):
            additions['frontend']['files'].update({
                'src/components/Button.jsx': 'button_component',
                'src/components/Card.jsx': 'card_component',
                'src/hooks/useAPI.js': 'use_api_hook'
            })

        # Python/FastAPI additions
        if any(tech in tech_lower for tech in ['python', 'fastapi']):
            additions.setdefault('api', {})
            additions['api']['files'].update({
                'src/main.py': 'fastapi_main_py',
                'src/models.py': 'fastapi_models_py',
                'src/database.py': 'fastapi_database_py'
            })

        # Database additions
        if any(db in tech_lower for tech in tech_stack for db in ['postgresql', 'mysql', 'mongodb']):
            additions.setdefault('database', {})
            additions['database']['files'] = {
                'schema.sql': 'database_schema',
                'seeds.sql': 'database_seeds'
            }

        # Docker additions
        if any('docker' in tech for tech in tech_lower):
            additions['files'] = additions.get('files', {})
            additions['files'].update({
                'Dockerfile': 'dockerfile',
                'docker-compose.yml': 'docker_compose',
                '.dockerignore': 'dockerignore'
            })

        return additions

    def _merge_structures(self, base: Dict, addition: Dict):
        """Merge two structure dictionaries"""
        for key, value in addition.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_structures(base[key], value)
            else:
                base[key] = value

    def _create_directories(self, base_dir: Path, structure: Dict[str, Any]) -> List[str]:
        """Create directory structure"""
        created_files = []

        def create_from_structure(current_path: Path, current_structure: Dict):
            # Create files in current directory
            files = current_structure.get('files', {})
            for filename, template_name in files.items():
                file_path = current_path / filename
                try:
                    content = self._get_template_content(template_name, filename)
                    file_path.write_text(content, encoding='utf-8')
                    created_files.append(str(file_path))
                except Exception as e:
                    logger.warning(f"Failed to create file {file_path}: {e}")

            # Create subdirectories
            directories = current_structure.get('directories', {})
            for dirname, sub_structure in directories.items():
                sub_path = current_path / dirname
                sub_path.mkdir(exist_ok=True)
                create_from_structure(sub_path, sub_structure)

        create_from_structure(base_dir, structure)
        return created_files

    def _generate_scaffold_files(self, project_dir: Path, spec: ProjectSpec) -> List[str]:
        """Generate scaffold files based on project specs"""
        files_created = []

        # Generate environment files
        env_files = self._create_env_files(project_dir, spec)
        files_created.extend(env_files)

        # Generate build scripts
        build_scripts = self._create_build_scripts(project_dir, spec)
        files_created.extend(build_scripts)

        # Generate CI/CD files
        cicd_files = self._create_cicd_files(project_dir, spec)
        files_created.extend(cicd_files)

        return files_created

    def _integrate_generated_content(
        self,
        project_dir: Path,
        spec: ProjectSpec,
        generated_content: Dict[str, str]
    ) -> List[str]:
        """Integrate AI-generated content into project structure"""
        files_created = []

        for task_id, content in generated_content.items():
            # Determine appropriate file location based on task type
            target_path = self._get_target_path_for_content(task_id, project_dir, spec)

            if target_path:
                try:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    target_path.write_text(content, encoding='utf-8')
                    files_created.append(str(target_path))
                except Exception as e:
                    logger.warning(f"Failed to save generated content to {target_path}: {e}")

        return files_created

    def _get_target_path_for_content(self, task_id: str, project_dir: Path, spec: ProjectSpec) -> Optional[Path]:
        """Determine where to save generated content based on task type"""
        task_path_mapping = {
            'frontend_development': project_dir / 'frontend' / 'src' / 'App.jsx',
            'frontend_fullstack': project_dir / 'frontend' / 'src' / 'App.tsx',
            'backend_api': project_dir / 'backend' / 'src' / 'app.py',
            'backend_fullstack': project_dir / 'backend' / 'src' / 'server.js',
            'api_service': project_dir / 'api' / 'src' / 'main.py',
            'configuration': project_dir / 'package.json',
            'testing_setup': project_dir / 'tests' / 'test_main.py',
            'documentation': project_dir / 'docs' / 'README.md'
        }

        return task_path_mapping.get(task_id)

    def _create_config_files(self, project_dir: Path, spec: ProjectSpec) -> List[str]:
        """Create configuration files for the project"""
        files_created = []

        # Project metadata
        metadata = {
            'project_name': spec.name,
            'project_type': spec.project_type.value,
            'tech_stack': spec.tech_stack,
            'features': spec.features,
            'scaffolded_at': str(Path().cwd()),
            'squad_generated': True
        }

        metadata_file = project_dir / '.squad-metadata.json'
        metadata_file.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        files_created.append(str(metadata_file))

        return files_created

    def _load_base_templates(self) -> Dict[str, Dict]:
        """Load base project templates"""
        return {
            'react_app': {
                'structure': 'standard_react',
                'files': ['package.json', 'vite.config.js', 'index.html']
            },
            'python_api': {
                'structure': 'fastapi_standard',
                'files': ['main.py', 'requirements.txt', 'alembic.ini']
            },
            'node_api': {
                'structure': 'express_standard',
                'files': ['server.js', 'package.json', '.env.example']
            }
        }

    def _load_tech_scaffolds(self) -> Dict[str, Any]:
        """Load technology-specific scaffolding patterns"""
        return {
            'react': {
                'dependencies': ['react', 'react-dom', 'vite'],
                'devDependencies': ['@vitejs/plugin-react', 'tailwindcss', 'autoprefixer'],
                'scripts': {
                    'dev': 'vite',
                    'build': 'vite build',
                    'preview': 'vite preview'
                }
            },
            'fastapi': {
                'dependencies': ['fastapi', 'uvicorn', 'sqlalchemy', 'alembic'],
                'scripts': {
                    'dev': 'uvicorn main:app --reload',
                    'start': 'uvicorn main:app --host 0.0.0.0 --port 8000'
                }
            },
            'express': {
                'dependencies': ['express', 'cors', 'helmet'],
                'scripts': {
                    'dev': 'nodemon server.js',
                    'start': 'node server.js'
                }
            }
        }

    def _load_file_templates(self) -> Dict[str, str]:
        """Load file templates for common files"""
        return {
            'readme': """# {project_name}

{description}

## Features

{features_list}

## Tech Stack

{tech_stack_list}

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+ (if using Python backend)

### Installation

1. Clone the repository
2. Install dependencies: `npm install`
3. Copy environment file: `cp .env.example .env`
4. Start development server: `npm run dev`

## Deployment

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
""",

            'package_json': """{{
  "name": "{project_name}",
  "version": "1.0.0",
  "description": "{description}",
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest"
  }},
  "dependencies": {{
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  }},
  "devDependencies": {{
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.3.6",
    "vite": "^5.0.8",
    "vitest": "^1.0.4"
  }}
}}""",

            'main_jsx': """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)""",

            'app_jsx': """import { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="App">
      <header className="App-header">
        <h1>{project_name}</h1>
        <p>{description}</p>
        <div>
          <button onClick={() => setCount((count) => count + 1)}>
            count is {count}
          </button>
        </div>
      </header>
    </div>
  )
}

export default App""",

            'main_py': """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="{project_name}", description="{description}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {{"message": "{project_name}"}}

@app.get("/health")
async def health_check():
    return {{"status": "healthy"}}""",

            'requirements_txt': """fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.13.1
python-multipart==0.0.6
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
redis==5.0.1
"""
        }

    def _get_template_content(self, template_name: str, filename: str) -> str:
        """Get content for a template"""
        # First try to get from file_templates
        if template_name in self.file_templates:
            content = self.file_templates[template_name]
            # Simple template variable replacement
            content = content.format(
                project_name="{project_name}",
                description="{description}",
                features_list="{features_list}",
                tech_stack_list="{tech_stack_list}"
            )
            return content

        # Fallback to default content
        return self._get_default_file_content(filename)

    def _get_default_file_content(self, filename: str) -> str:
        """Get default content for unknown file types"""
        extensions = {
            '.py': '# Generated by Squad API\n\n',
            '.js': '// Generated by Squad API\n\n',
            '.jsx': '// Generated by Squad API\nimport React from \'react\';\n\n',
            '.ts': '// Generated by Squad API\n\n',
            '.tsx': '// Generated by Squad API\nimport React from \'react\';\n\n',
            '.json': '{\n  "// Generated by Squad API": true\n}\n',
            '.md': '# Generated by Squad API\n\n',
            '.yml': '# Generated by Squad API\nversion: \'3.8\'\n',
            '.yaml': '# Generated by Squad API\nversion: \'3.8\'\n',
            '.html': '<!DOCTYPE html>\n<html>\n<head>\n  <title>Generated</title>\n</head>\n<body>\n  <!-- Generated by Squad API -->\n</body>\n</html>\n',
            '.css': '/* Generated by Squad API */\n\n',
            '.sql': '-- Generated by Squad API\n\n'
        }

        ext = Path(filename).suffix
        return extensions.get(ext, f'# Generated by Squad API: {filename}\n')


class ProjectPackager:
    """
    Package and deliver generated projects

    Handles packaging, compression, and delivery of generated projects
    in various formats for distribution and deployment.
    """

    def __init__(self):
        """Initialize the packager"""
        self.package_formats = ['zip', 'tar.gz', 'docker']

    def package_project(
        self,
        project_dir: Path,
        package_format: str = 'zip',
        include_metadata: bool = True
    ) -> Path:
        """
        Package project for distribution

        Args:
            project_dir: Project directory to package
            package_format: Format to package in ('zip', 'tar.gz', 'docker')
            include_metadata: Whether to include metadata files

        Returns:
            Path to packaged file
        """
        if package_format not in self.package_formats:
            raise ValueError(f"Unsupported package format: {package_format}")

        package_name = project_dir.name
        package_dir = project_dir.parent

        if package_format == 'zip':
            return self._package_zip(project_dir, package_dir, package_name)
        elif package_format == 'tar.gz':
            return self._package_tar_gz(project_dir, package_dir, package_name)
        elif package_format == 'docker':
            return self._package_docker(project_dir, package_dir, package_name)

    def _package_zip(self, project_dir: Path, package_dir: Path, package_name: str) -> Path:
        """Package project as ZIP file"""
        import zipfile

        zip_path = package_dir / f"{package_name}.zip"

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in project_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(project_dir.parent)
                    zipf.write(file_path, arcname)

        logger.info(f"Created ZIP package: {zip_path}")
        return zip_path

    def _package_tar_gz(self, project_dir: Path, package_dir: Path, package_name: str) -> Path:
        """Package project as tar.gz file"""
        import tarfile

        tar_path = package_dir / f"{package_name}.tar.gz"

        with tarfile.open(tar_path, 'w:gz') as tar:
            tar.add(project_dir, arcname=package_name)

        logger.info(f"Created tar.gz package: {tar_path}")
        return tar_path

    def _package_docker(self, project_dir: Path, package_dir: Path, package_name: str) -> Path:
        """Create Docker image for project"""
        dockerfile_content = self._generate_dockerfile(project_dir)
        dockerfile_path = project_dir / 'Dockerfile'
        dockerfile_path.write_text(dockerfile_content)

        # Copy docker-compose if it doesn't exist
        compose_path = project_dir / 'docker-compose.yml'
        if not compose_path.exists():
            compose_content = self._generate_docker_compose(project_dir)
            compose_path.write_text(compose_content)

        logger.info(f"Created Docker files in: {project_dir}")
        return project_dir

    def _generate_dockerfile(self, project_dir: Path) -> str:
        """Generate Dockerfile for the project"""
        # Detect project type and generate appropriate Dockerfile
        if (project_dir / 'package.json').exists():
            # Node.js project
            return """FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
"""
        elif (project_dir / 'requirements.txt').exists() or (project_dir / 'main.py').exists()):
            # Python project
            return """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        else:
            # Generic Dockerfile
            return """FROM ubuntu:22.04

WORKDIR /app

COPY . .

CMD ["echo", "Generated by Squad API"]
"""

    def _generate_docker_compose(self, project_dir: Path) -> str:
        """Generate docker-compose.yml for the project"""
        return f"""version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    volumes:
      - .:/app
      - /app/node_modules

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: {project_dir.name}
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
"""

    def create_deployment_bundle(
        self,
        project_dir: Path,
        deployment_target: str = 'docker'
    ) -> Dict[str, Any]:
        """
        Create deployment bundle with all necessary files

        Args:
            project_dir: Project directory
            deployment_target: Target deployment platform

        Returns:
            Dictionary with bundle information
        """
        bundle_info = {
            'project_name': project_dir.name,
            'deployment_target': deployment_target,
            'files_included': [],
            'deployment_instructions': '',
            'bundle_path': None
        }

        # Package the project
        package_path = self.package_project(project_dir, deployment_target)
        bundle_info['bundle_path'] = str(package_path)

        # List included files
        for file_path in project_dir.rglob('*'):
            if file_path.is_file():
                bundle_info['files_included'].append(str(file_path.relative_to(project_dir)))

        # Generate deployment instructions
        bundle_info['deployment_instructions'] = self._generate_deployment_instructions(
            project_dir, deployment_target
        )

        return bundle_info

    def _generate_deployment_instructions(self, project_dir: Path, deployment_target: str) -> str:
        """Generate deployment instructions for the target platform"""
        instructions = {
            'docker': f"""
# Docker Deployment Instructions for {project_dir.name}

## Prerequisites
- Docker and Docker Compose installed

## Deployment Steps
1. Navigate to the project directory
2. Run: `docker-compose up --build`
3. Access the application at http://localhost:3000

## Production Deployment
1. Set environment variables in docker-compose.prod.yml
2. Use: `docker-compose -f docker-compose.prod.yml up -d`
3. Set up reverse proxy (nginx) for SSL termination
""",

            'cloud': f"""
# Cloud Deployment Instructions for {project_dir.name}

## Supported Platforms
- Heroku
- Vercel (frontend)
- Railway
- Render

## Heroku Deployment
1. Install Heroku CLI
2. Run: `heroku create {project_dir.name}`
3. Set config vars: `heroku config:set KEY=value`
4. Deploy: `git push heroku main`

## Vercel Deployment (Frontend)
1. Install Vercel CLI: `npm i -g vercel`
2. Run: `vercel`
3. Follow the prompts

## General Notes
- Ensure all environment variables are configured
- Set up monitoring and logging
- Configure custom domain if needed
""",

            'local': f"""
# Local Development Instructions for {project_dir.name}

## Prerequisites
- Node.js 18+ (for frontend)
- Python 3.11+ (for backend)
- PostgreSQL (if using database)

## Setup Steps
1. Clone/download the project
2. Install dependencies:
   - Frontend: `cd frontend && npm install`
   - Backend: `cd backend && pip install -r requirements.txt`
3. Set up environment variables (.env file)
4. Start development servers:
   - Frontend: `npm run dev`
   - Backend: `uvicorn main:app --reload`

## Database Setup
1. Install PostgreSQL
2. Create database: `createdb {project_dir.name}`
3. Run migrations: `alembic upgrade head`

## Testing
- Frontend tests: `npm test`
- Backend tests: `pytest`
- End-to-end tests: `npm run test:e2e`
"""
        }

        return instructions.get(deployment_target, instructions['local'])
