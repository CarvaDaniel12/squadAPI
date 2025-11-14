# Squad API - AI-Powered Project Generator

## Overview

The Squad API Project Generator is a revolutionary system that transforms Squad's AI agents into a powerful software development engine. Instead of just using AI for conversations, this system orchestrates multiple specialized AI agents to generate complete, production-ready software projects from simple specifications.

## 🎯 Key Features

- **AI-Powered Development**: Uses Squad's specialized agents (Mary, John, Alex) to generate entire projects
- **Multiple Project Types**: Web apps, API services, full-stack applications, CLI tools, libraries, and more
- **Technology Agnostic**: Supports React, Vue, Python, Node.js, Go, Java, databases, and deployment platforms
- **Intelligent Scaffolding**: Creates proper directory structures, configuration files, and project organization
- **Production Ready**: Generates tests, documentation, deployment configs, and CI/CD pipelines
- **CLI Interface**: Simple command-line interface for easy project generation
- **Configuration Integration**: Seamlessly integrates with existing Squad configuration

## 🏗️ Architecture

### Core Components

1. **Project Generator** (`src/generator/project_generator.py`)
   - Coordinates the entire generation process
   - Plans generation workflows
   - Executes tasks through Squad's agent orchestration
   - Manages project packaging and delivery

2. **Specification Parser** (`src/generator/spec_parser.py`)
   - Parses project specifications from JSON, YAML, or Python dicts
   - Validates specifications for completeness and consistency
   - Normalizes and enhances specifications
   - Provides intelligent defaults and recommendations

3. **Scaffolding System** (`src/generator/scaffolding.py`)
   - Creates appropriate project directory structures
   - Generates scaffold files for different technologies
   - Integrates AI-generated content into project structure
   - Handles file organization and naming conventions

4. **Configuration Integration** (`src/generator/config_integration.py`)
   - Integrates with Squad's existing configuration system
   - Manages generator-specific settings
   - Handles template management
   - Provides configuration validation

5. **CLI Interface** (`src/generator/cli.py`)
   - User-friendly command-line interface
   - Multiple generation modes (from files, templates, interactive)
   - Progress tracking and status reporting
   - Rich console output with formatting

### Agent Workflow

The system uses Squad's specialized agents in a coordinated workflow:

- **Mary (Architecture Agent)**: Creates project planning, architecture diagrams, and technical specifications
- **John (Development Agent)**: Implements core functionality, APIs, user interfaces, and integrations
- **Alex (Quality Agent)**: Generates tests, documentation, reviews code quality, and ensures standards

## 🚀 Quick Start

### Prerequisites

- Squad API configured and running
- Python 3.11+
- Required dependencies installed

### Basic Usage

#### Generate from a specification file:

```bash
# Create a specification file
cat > my_project.yaml << EOF
name: My Web App
description: A modern web application with React and Node.js
project_type: web_app
requirements:
  - Build a responsive user interface
  - Create REST API endpoints
  - Implement user authentication
  - Add data persistence
tech_stack:
  - react
  - nodejs
  - postgresql
features:
  - User dashboard
  - Authentication system
  - Data visualization
  - Responsive design
deployment_target: docker
EOF

# Generate the project
squad-generate my_project.yaml --output-dir ./generated
```

#### Generate from a template:

```bash
# List available templates
squad-generate --list-templates

# Create a project from a template
squad-generate create my-awesome-app --template web_app
```

#### Initialize a specification template:

```bash
# Create a specification template to edit
squad-generate init-spec --template basic --output-file my_spec.yaml
```

## 📋 Project Specification Format

### Basic Structure

```yaml
name: Project Name
description: Brief description of the project
project_type: web_app  # or: api_service, full_stack, cli_tool, library, mobile_app
requirements:
  - List of functional requirements
  - What the project must accomplish
tech_stack:
  - react
  - python
  - postgresql
features:
  - List of key features
  - What users should be able to do
architecture: Optional architecture description
constraints:
  - Technical constraints
  - Performance requirements
target_audience: Who will use this project
deployment_target: local  # or: docker, cloud, kubernetes, serverless
```

### Project Types

- **web_app**: Single-page application with frontend focus
- **api_service**: RESTful API service with backend focus
- **full_stack**: Complete web application with frontend and backend
- **cli_tool**: Command-line interface application
- **library**: Reusable library or package
- **mobile_app**: Mobile application (framework planning)
- **data_pipeline**: Data processing and analysis pipeline
- **microservice**: Microservice architecture component

### Technology Stack Examples

#### Frontend
- `react`, `vue`, `angular`, `svelte`
- `tailwind`, `bootstrap`, `material-ui`
- `vite`, `webpack`, `parcel`

#### Backend
- `nodejs`, `python`, `java`, `go`, `rust`
- `express`, `fastapi`, `spring`, `gin`

#### Databases
- `postgresql`, `mysql`, `mongodb`, `redis`
- `sqlite`, `dynamodb`, `cassandra`

#### Deployment
- `docker`, `kubernetes`, `heroku`, `aws`
- `vercel`, `netlify`, `render`

## 🛠️ Advanced Usage

### Custom Templates

Create custom project templates:

```python
from src.generator.spec_parser import load_specification_template

# Load and customize a template
template = load_specification_template('web_app')
template['name'] = 'My Custom Project'
template['tech_stack'].append('typescript')

# Save as custom template
# (Use the template manager API)
```

### Programmatic Generation

```python
import asyncio
from src.generator.project_generator import ProjectGenerator, ProjectSpec, ProjectType
from src.agents.orchestrator import AgentOrchestrator

async def generate_project_programmatically():
    # Set up orchestrator (your Squad instance)
    orchestrator = AgentOrchestrator(...)

    # Create generator
    generator = ProjectGenerator(orchestrator, output_dir="./projects")

    # Define project specification
    spec = ProjectSpec(
        name="My API Service",
        description="A REST API for user management",
        project_type=ProjectType.API_SERVICE,
        requirements=[
            "Create user authentication endpoints",
            "Implement CRUD operations for users",
            "Add data validation and error handling"
        ],
        tech_stack=["python", "fastapi", "postgresql", "redis"],
        features=[
            "User registration and login",
            "JWT authentication",
            "User profile management",
            "Password reset functionality"
        ]
    )

    # Generate project
    result = await generator.generate_project(spec)

    print(f"Generated {len(result.files_created)} files")
    print(f"Project location: {result.artifacts_path}")
    print(f"Generation time: {result.generation_time:.2f}s")

# Run the generation
asyncio.run(generate_project_programmatically())
```

### Configuration

#### Generator Configuration

Create a generator configuration file:

```yaml
# generator-config.yaml
generator:
  default_output_dir: "./generated_projects"
  default_agents:
    - mary
    - john
    - alex
  agent_timeout: 300
  max_retries: 3
  include_tests: true
  include_docs: true
  include_deployment: true
  template_dir: "./custom_templates"
```

#### Squad Configuration Updates

For optimal generation, update your Squad configuration:

```yaml
# In your Squad config
agents:
  mary:
    specialization: "architecture_planning"
    timeout: 300
  john:
    specialization: "development_implementation"
    timeout: 300
  alex:
    specialization: "quality_documentation"
    timeout: 300

providers:
  groq:
    timeout: 120
    max_retries: 3
  cerebras:
    timeout: 120
    max_retries: 3
```

## 📁 Generated Project Structure

### Web Application Example

```
my-web-app/
├── README.md                          # Project overview
├── DEPLOYMENT_GUIDE.md               # Deployment instructions
├── PROJECT_SUMMARY.md                # Generation summary
├── package.json                      # Dependencies and scripts
├── .env.example                      # Environment variables template
├── .gitignore                        # Git ignore rules
├── frontend/                         # Frontend application
│   ├── src/
│   │   ├── components/               # React components
│   │   ├── pages/                    # Page components
│   │   ├── hooks/                    # Custom hooks
│   │   ├── services/                 # API services
│   │   ├── utils/                    # Utility functions
│   │   ├── App.tsx                   # Main app component
│   │   └── main.tsx                  # App entry point
│   ├── public/                       # Static assets
│   ├── vite.config.ts               # Vite configuration
│   └── tailwind.config.js           # Tailwind configuration
├── backend/                          # Backend API
│   ├── src/
│   │   ├── routes/                   # API routes
│   │   ├── models/                   # Data models
│   │   ├── middleware/               # Express middleware
│   │   ├── controllers/              # Route controllers
│   │   └── app.js                    # Express app
│   └── package.json                  # Backend dependencies
├── tests/                           # Test files
│   ├── unit/                        # Unit tests
│   ├── integration/                 # Integration tests
│   └── e2e/                         # End-to-end tests
├── docs/                            # Documentation
│   ├── api/                         # API documentation
│   └── guides/                      # User guides
├── .github/                         # GitHub configuration
│   └── workflows/                   # CI/CD workflows
└── docker-compose.yml               # Docker configuration
```

### API Service Example

```
my-api-service/
├── README.md
├── DEPLOYMENT_GUIDE.md
├── PROJECT_SUMMARY.md
├── requirements.txt                 # Python dependencies
├── main.py                         # FastAPI application
├── alembic.ini                     # Database migrations
├── src/
│   ├── models/                     # Pydantic models
│   ├── routes/                     # API routes
│   ├── controllers/                # Business logic
│   ├── database.py                 # Database connection
│   └── app.py                      # FastAPI app setup
├── tests/
│   ├── unit/                       # Unit tests with pytest
│   └── integration/                # API integration tests
├── docs/                          # API documentation
├── migrations/                    # Database migrations
├── scripts/
│   └── init_db.py                # Database initialization
└── Dockerfile                     # Container configuration
```

## 🎛️ CLI Commands Reference

### Main Commands

```bash
# Generate project from specification file
squad-generate <spec_file> [options]

# Create project from template
squad-generate create <project_name> [options]

# List available templates
squad-generate --list-templates

# Initialize specification template
squad-generate init-spec [options]

# Show project status
squad-generate status <project_directory>
```

### Options

- `--output-dir, -o`: Output directory for generated project
- `--template, -t`: Template to use for project creation
- `--verbose, -v`: Enable verbose output
- `--format`: Package format (zip, tar.gz, docker)

### Examples

```bash
# Generate with custom output directory
squad-generate spec.yaml --output-dir /tmp/my-projects

# Create from template with specific tech stack
squad-generate create my-api --template api_service --output-dir ./services

# Generate with verbose output
squad-generate spec.yaml --verbose

# Initialize specification and edit manually
squad-generate init-spec --template full_stack --output-file full_stack_spec.yaml
```

## 🔧 Development and Contribution

### Project Structure

```
src/generator/
├── __init__.py                     # Module initialization
├── project_generator.py            # Main generator orchestrator
├── spec_parser.py                  # Specification parsing and validation
├── scaffolding.py                  # Project structure and file generation
├── config_integration.py           # Squad configuration integration
├── cli.py                         # Command-line interface
└── templates/                     # Built-in project templates
    ├── basic_project.yaml
    ├── web_app_template.yaml
    ├── api_service_template.yaml
    └── full_stack_template.yaml
```

### Adding New Project Types

1. Define the project type in `ProjectType` enum
2. Add structure planning in `ProjectScaffolder._get_type_specific_structure()`
3. Add technology-specific scaffolds in `_get_tech_specific_structure()`
4. Update CLI templates and help text

### Adding New Technologies

1. Update `ProjectSpecValidator.known_tech_stacks` with technology categories
2. Add scaffolding patterns in `ProjectScaffolder._load_tech_scaffolds()`
3. Add file templates in `_load_file_templates()`
4. Update validation logic for technology compatibility

### Custom Templates

1. Create template files in the `templates/` directory
2. Follow the specification format
3. Add to `ProjectSpecParser.project_type_aliases` if needed
4. Test with different project types

## 📊 Monitoring and Metrics

The generator integrates with Squad's monitoring system to track:

- **Generation Metrics**: Time taken, files created, success rate
- **Agent Usage**: Which agents were used for each task
- **Cost Tracking**: Token usage and provider costs
- **Quality Metrics**: Validation errors, warnings, and suggestions
- **Performance**: Generation speed and throughput

Access metrics through Squad's existing monitoring endpoints and dashboards.

## 🐛 Troubleshooting

### Common Issues

#### Specification Validation Errors

```
ERROR: Required field 'name' is missing
```

**Solution**: Ensure all required fields are present in your specification.

#### Agent Configuration Issues

```
WARNING: Required agent 'mary' is not configured in Squad
```

**Solution**: Verify that all required agents (mary, john, alex) are properly configured in your Squad setup.

#### Provider Timeouts

```
ERROR: Provider timeout during generation
```

**Solution**: Increase timeout values in generator configuration or provider settings.

#### Template Not Found

```
ERROR: Template 'custom_template' not found
```

**Solution**: Ensure template files exist in the templates directory or update the template path.

### Debug Mode

Enable verbose logging for detailed information:

```bash
squad-generate spec.yaml --verbose
```

Or set environment variables:

```bash
export SQUAD_GENERATOR_DEBUG=true
export LOG_LEVEL=DEBUG
```

### Getting Help

1. Check generated `PROJECT_SUMMARY.md` for detailed information
2. Review `DEPLOYMENT_GUIDE.md` for setup instructions
3. Use `squad-generate status <project_dir>` to check project details
4. Enable verbose mode for detailed logs

## 🚀 Future Roadmap

### Planned Features

- **Visual Project Builder**: Web-based interface for project specification
- **Template Marketplace**: Community-contributed templates
- **Advanced Deployment**: Kubernetes, serverless, and cloud-native deployments
- **Multi-language Support**: Generation in multiple programming languages
- **Integration Testing**: Automated testing of generated projects
- **Code Quality Analysis**: Integration with static analysis tools
- **Performance Optimization**: Intelligent code optimization suggestions

### Experimental Features

- **Voice-to-Code**: Generate projects from voice descriptions
- **AI Code Review**: Automated code review and improvement suggestions
- **Dynamic Templates**: Templates that adapt based on project context
- **Collaborative Generation**: Multiple users collaborating on project generation

## 📄 License

This project is part of the Squad API ecosystem. See the main project license for details.

## 🤝 Contributing

Contributions are welcome! Please see the main Squad API contribution guidelines.

### Development Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up Squad API configuration
4. Run tests: `pytest tests/`
5. Start development server

### Testing

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/unit/test_generator/
pytest tests/integration/test_workflow/

# Run with coverage
pytest --cov=src/generator tests/
```

---

**Generated by Squad API Project Generator** - Transforming AI conversations into production-ready software projects.
