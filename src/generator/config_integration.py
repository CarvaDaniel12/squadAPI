"""
Squad Configuration Integration for Project Generator
Story: Integrate project generation with existing Squad configuration system

This module integrates the Project Generator with Squad's existing configuration
system to ensure consistency and enable project-specific configurations.
"""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from src.config.loader import ConfigLoader
from src.config.settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class SquadGeneratorConfig:
    """Configuration for Squad Project Generator"""
    # Output settings
    default_output_dir: str = "generated_projects"
    project_name_format: str = "{project_type}_{timestamp}"

    # Agent settings
    default_agents: List[str] = None
    agent_timeout: int = 300  # 5 minutes
    max_retries: int = 3

    # Generation settings
    include_tests: bool = True
    include_docs: bool = True
    include_deployment: bool = True
    code_quality_check: bool = True

    # Validation settings
    strict_validation: bool = False
    validate_dependencies: bool = True

    # Template settings
    template_dir: str = "templates"
    custom_templates: Dict[str, str] = None

    def __post_init__(self):
        if self.default_agents is None:
            self.default_agents = ["mary", "john", "alex"]
        if self.custom_templates is None:
            self.custom_templates = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class SquadConfigIntegrator:
    """
    Integrates Project Generator with Squad's configuration system

    This class ensures that the project generator respects Squad's existing
    configuration patterns and can use configured settings.
    """

    def __init__(self, config_loader: ConfigLoader, settings: Settings):
        """
        Initialize configuration integrator

        Args:
            config_loader: Squad's configuration loader
            settings: Squad's settings instance
        """
        self.config_loader = config_loader
        self.settings = settings

        # Load generator-specific configuration
        self.generator_config = self._load_generator_config()

        # Validate configuration
        self._validate_config()

    def _load_generator_config(self) -> SquadGeneratorConfig:
        """Load generator configuration from Squad's config system"""
        # Try to load from Squad's configuration files
        generator_config = SquadGeneratorConfig()

        # Check for generator-specific config in Squad's config
        squad_config = self.config_loader.get_full_config()

        # Look for generator section in configuration
        if 'generator' in squad_config:
            config_dict = squad_config['generator']

            # Update defaults with loaded configuration
            for key, value in config_dict.items():
                if hasattr(generator_config, key):
                    setattr(generator_config, key, value)

        # Environment variable overrides
        env_mappings = {
            'SQUAD_GENERATOR_OUTPUT_DIR': 'default_output_dir',
            'SQUAD_GENERATOR_TIMEOUT': 'agent_timeout',
            'SQUAD_GENERATOR_RETRIES': 'max_retries',
            'SQUAD_GENERATOR_INCLUDE_TESTS': 'include_tests',
            'SQUAD_GENERATOR_INCLUDE_DOCS': 'include_docs',
            'SQUAD_GENERATOR_INCLUDE_DEPLOYMENT': 'include_deployment',
            'SQUAD_GENERATOR_STRICT_VALIDATION': 'strict_validation'
        }

        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert string values to appropriate types
                if isinstance(getattr(generator_config, config_key), bool):
                    setattr(generator_config, config_key, env_value.lower() in ('true', '1', 'yes'))
                elif isinstance(getattr(generator_config, config_key), int):
                    setattr(generator_config, config_key, int(env_value))
                else:
                    setattr(generator_config, config_key, env_value)

        logger.info(f"Loaded generator configuration: {generator_config.default_output_dir}")
        return generator_config

    def _validate_config(self):
        """Validate generator configuration"""
        errors = []

        # Validate output directory
        output_dir = Path(self.generator_config.default_output_dir)
        if not output_dir.parent.exists():
            errors.append(f"Output directory parent does not exist: {output_dir.parent}")

        # Validate timeout settings
        if self.generator_config.agent_timeout < 30:
            errors.append("Agent timeout should be at least 30 seconds")

        if self.generator_config.agent_timeout > 1800:
            errors.append("Agent timeout should not exceed 30 minutes")

        # Validate retry settings
        if self.generator_config.max_retries < 1:
            errors.append("Max retries should be at least 1")

        if self.generator_config.max_retries > 10:
            errors.append("Max retries should not exceed 10")

        # Validate default agents
        configured_agents = self.settings.get('agents', {})
        for agent in self.generator_config.default_agents:
            if agent not in configured_agents:
                errors.append(f"Default agent '{agent}' is not configured in Squad")

        if errors:
            logger.warning(f"Generator configuration validation issues: {errors}")

    def get_generator_settings(self) -> Dict[str, Any]:
        """Get generator settings for use by other components"""
        return {
            'output_dir': self.generator_config.default_output_dir,
            'agents': self.generator_config.default_agents,
            'timeout': self.generator_config.agent_timeout,
            'retries': self.generator_config.max_retries,
            'features': {
                'tests': self.generator_config.include_tests,
                'docs': self.generator_config.include_docs,
                'deployment': self.generator_config.include_deployment,
                'quality_check': self.generator_config.code_quality_check
            },
            'validation': {
                'strict': self.generator_config.strict_validation,
                'dependencies': self.generator_config.validate_dependencies
            }
        }

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific agent

        Args:
            agent_name: Name of the agent

        Returns:
            Agent configuration dictionary
        """
        # Get base agent configuration from Squad
        base_config = self.settings.get(f'agents.{agent_name}', {})

        # Add generator-specific settings
        generator_agent_config = {
            'timeout': self.generator_config.agent_timeout,
            'retries': self.generator_config.max_retries,
            'generator_mode': True  # Mark as being used for generation
        }

        # Merge configurations (generator config takes precedence)
        return {**base_config, **generator_agent_config}

    def validate_project_spec_for_squad(self, spec: Dict[str, Any]) -> List[str]:
        """
        Validate project specification against Squad configuration

        Args:
            spec: Project specification to validate

        Returns:
            List of validation errors/warnings
        """
        issues = []

        # Check if required agents are configured
        required_agents = ['mary', 'john', 'alex']  # Default generation team
        configured_agents = self.settings.get('agents', {})

        for agent in required_agents:
            if agent not in configured_agents:
                issues.append(f"Required agent '{agent}' is not configured in Squad")

        # Check provider configuration
        providers = self.settings.get('providers', {})
        if not providers:
            issues.append("No providers configured in Squad - generation will use fallbacks")

        # Check rate limiting configuration
        rate_limit_config = self.settings.get('rate_limit', {})
        if not rate_limit_config:
            issues.append("No rate limiting configured - generation may be throttled")

        # Check monitoring configuration
        monitoring_config = self.settings.get('monitoring', {})
        if not monitoring_config:
            issues.append("No monitoring configured - generation metrics will not be tracked")

        return issues

    def create_generator_config_file(self, output_path: str):
        """
        Create a generator configuration file

        Args:
            output_path: Path where to save the configuration file
        """
        config_content = {
            'generator': self.generator_config.to_dict(),
            'squad_integration': {
                'version': '1.0',
                'description': 'Squad Project Generator Configuration',
                'created_from': 'squad_config_system'
            }
        }

        # Save as YAML for better readability
        with open(output_path, 'w') as f:
            yaml.dump(config_content, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Generator configuration saved to: {output_path}")

    def update_squad_config_for_generator(self, config_updates: Dict[str, Any]):
        """
        Update Squad configuration to optimize for project generation

        Args:
            config_updates: Dictionary of configuration updates
        """
        # This would typically update Squad's configuration files
        # For now, we'll log the intended updates

        logger.info("Updating Squad configuration for generator optimization:")
        for key, value in config_updates.items():
            logger.info(f"  {key}: {value}")

        # In a real implementation, you would:
        # 1. Backup current configuration
        # 2. Update configuration files
        # 3. Validate new configuration
        # 4. Reload Squad configuration if needed

    def get_generation_templates(self) -> Dict[str, str]:
        """
        Get generation templates based on Squad configuration

        Returns:
            Dictionary mapping template names to file paths
        """
        templates = {}

        # Check for custom templates directory
        templates_dir = Path(self.generator_config.template_dir)
        if templates_dir.exists():
            for template_file in templates_dir.glob('*.yaml'):
                template_name = template_file.stem
                templates[template_name] = str(template_file)

        # Add built-in templates
        built_in_templates = {
            'basic': 'basic_project_template.yaml',
            'web_app': 'web_app_template.yaml',
            'api_service': 'api_service_template.yaml',
            'full_stack': 'full_stack_template.yaml'
        }

        # Merge with custom templates
        templates.update(self.generator_config.custom_templates)
        templates.update(built_in_templates)

        return templates


class ProjectTemplateManager:
    """
    Manages project templates with Squad integration

    This class handles loading, validating, and managing project templates
    that are compatible with Squad's configuration system.
    """

    def __init__(self, integrator: SquadConfigIntegrator):
        """
        Initialize template manager

        Args:
            integrator: Squad configuration integrator
        """
        self.integrator = integrator
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load all available templates"""
        templates = {}

        # Get templates from integrator
        template_files = self.integrator.get_generation_templates()

        for template_name, template_path in template_files.items():
            try:
                with open(template_path, 'r') as f:
                    template_data = yaml.safe_load(f)

                # Validate template structure
                if self._validate_template(template_data):
                    templates[template_name] = template_data
                else:
                    logger.warning(f"Template {template_name} validation failed")

            except Exception as e:
                logger.error(f"Failed to load template {template_name}: {e}")

        return templates

    def _validate_template(self, template: Dict[str, Any]) -> bool:
        """Validate template structure"""
        required_fields = ['name', 'description', 'project_type', 'requirements', 'features']

        for field in required_fields:
            if field not in template:
                logger.error(f"Template missing required field: {field}")
                return False

        return True

    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific template

        Args:
            template_name: Name of the template

        Returns:
            Template data or None if not found
        """
        return self.templates.get(template_name)

    def list_templates(self) -> List[str]:
        """List all available template names"""
        return list(self.templates.keys())

    def create_custom_template(self, name: str, spec: Dict[str, Any]) -> bool:
        """
        Create a new custom template

        Args:
            name: Name for the new template
            spec: Project specification for the template

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate the specification
            template_data = spec.copy()
            template_data['template_name'] = name
            template_data['created_by'] = 'squad_generator'
            template_data['created_at'] = str(Path().cwd())

            # Save template
            template_dir = Path(self.integrator.generator_config.template_dir)
            template_dir.mkdir(exist_ok=True)

            template_path = template_dir / f"{name}.yaml"
            with open(template_path, 'w') as f:
                yaml.dump(template_data, f, default_flow_style=False)

            # Reload templates
            self.templates = self._load_templates()

            logger.info(f"Custom template created: {template_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create custom template: {e}")
            return False


# Configuration file templates
GENERATOR_CONFIG_TEMPLATE = """# Squad Project Generator Configuration
# This file configures how the generator works with your Squad setup

generator:
  # Output settings
  default_output_dir: "generated_projects"
  project_name_format: "{project_type}_{timestamp}"

  # Agent settings
  default_agents:
    - mary      # Architecture and planning
    - john      # Development and implementation
    - alex      # Testing and documentation

  agent_timeout: 300        # 5 minutes per agent task
  max_retries: 3           # Retry failed tasks

  # Generation features
  include_tests: true       # Generate test files
  include_docs: true        # Generate documentation
  include_deployment: true  # Generate deployment files
  code_quality_check: true  # Validate generated code

  # Validation settings
  strict_validation: false  # Strict specification validation
  validate_dependencies: true # Check tech stack compatibility

  # Template settings
  template_dir: "templates"
  custom_templates: {}       # Custom template mappings

# Squad integration settings
squad_integration:
  version: "1.0"
  description: "Squad Project Generator Configuration"
"""

SQUAD_UPDATE_RECOMMENDATIONS = """# Recommended Squad Configuration Updates for Project Generator

# 1. Agent Configuration
# Ensure your agents are properly configured for generation tasks:

agents:
  mary:
    specialization: "architecture_planning"
    capabilities: ["system_design", "architecture", "planning"]
    timeout: 300

  john:
    specialization: "development_implementation"
    capabilities: ["coding", "implementation", "integration"]
    timeout: 300

  alex:
    specialization: "quality_documentation"
    capabilities: ["testing", "documentation", "reviews"]
    timeout: 300

# 2. Provider Configuration
# Configure providers with appropriate timeouts for generation:

providers:
  groq:
    timeout: 120
    max_retries: 3
    model_preferences: ["llama-3.1-70b-versatile", "llama-3.1-8b-instant"]

  cerebras:
    timeout: 120
    max_retries: 3

  gemini:
    timeout: 120
    max_retries: 3

# 3. Rate Limiting
# Configure appropriate rate limits for generation workloads:

rate_limit:
  global:
    requests_per_minute: 60
    requests_per_hour: 1000

  per_provider:
    groq:
      requests_per_minute: 30
      tokens_per_hour: 1000000

    cerebras:
      requests_per_minute: 30
      tokens_per_hour: 1000000

# 4. Monitoring
# Enable monitoring for generation metrics:

monitoring:
  enabled: true
  metrics:
    - generation_time
    - files_created
    - agent_usage
    - cost_tracking

  alerts:
    generation_failures: true
    long_generation_times: true
"""
