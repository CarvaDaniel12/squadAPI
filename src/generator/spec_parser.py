"""
Project Specification Parser and Validator
Story: Parse and validate project specifications for Squad-powered development

This module provides functionality to parse project specifications from various
formats (JSON, YAML, Python dict) and validate them according to Squad's requirements.
"""

import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from .project_generator import ProjectType

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when project specification validation fails"""
    pass


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    ERROR = "error"      # Must be fixed
    WARNING = "warning"  # Should be fixed
    INFO = "info"        # Nice to have


@dataclass
class ValidationIssue:
    """Individual validation issue"""
    severity: ValidationSeverity
    field: str
    message: str
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of project specification validation"""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, field: str, message: str, suggestion: Optional[str] = None):
        """Add validation error"""
        self.issues.append(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            field=field,
            message=message,
            suggestion=suggestion
        ))

    def add_warning(self, field: str, message: str, suggestion: Optional[str] = None):
        """Add validation warning"""
        self.issues.append(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            field=field,
            message=message,
            suggestion=suggestion
        ))

    def add_info(self, field: str, message: str):
        """Add validation info"""
        self.issues.append(ValidationIssue(
            severity=ValidationSeverity.INFO,
            field=field,
            message=message
        ))

    def get_errors(self) -> List[ValidationIssue]:
        """Get all validation errors"""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR]

    def get_warnings(self) -> List[ValidationIssue]:
        """Get all validation warnings"""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING]


class ProjectSpecParser:
    """
    Parse project specifications from various formats

    Supports JSON, YAML, and Python dict formats.
    Provides intelligent parsing with sensible defaults and fallbacks.
    """

    def __init__(self):
        """Initialize the parser"""
        self.supported_formats = ['json', 'yaml', 'yml', 'dict']
        self.required_fields = [
            'name', 'description', 'project_type', 'requirements', 'tech_stack', 'features'
        ]

        # Known tech stack patterns for validation
        self.known_tech_stacks = {
            'frontend': ['react', 'vue', 'angular', 'svelte', 'jquery', 'bootstrap', 'tailwind'],
            'backend': ['nodejs', 'python', 'java', 'go', 'rust', 'csharp', 'php'],
            'database': ['postgresql', 'mysql', 'mongodb', 'redis', 'sqlite', 'dynamodb'],
            'api': ['rest', 'graphql', 'grpc', 'websockets'],
            'deployment': ['docker', 'kubernetes', 'heroku', 'aws', 'gcp', 'azure'],
            'tools': ['webpack', 'vite', 'babel', 'eslint', 'jest', 'cypress']
        }

        # Project type mappings
        self.project_type_aliases = {
            'web': 'web_app',
            'website': 'web_app',
            'webapp': 'web_app',
            'web_application': 'web_app',
            'api': 'api_service',
            'rest_api': 'api_service',
            'microservice': 'microservice',
            'micro_service': 'microservice',
            'fullstack': 'full_stack',
            'full-stack': 'full_stack',
            'full_stack': 'full_stack',
            'data_pipeline': 'data_pipeline',
            'pipeline': 'data_pipeline',
            'cli': 'cli_tool',
            'command_line': 'cli_tool',
            'library': 'library',
            'package': 'library',
            'npm': 'library',
            'mobile': 'mobile_app',
            'app': 'mobile_app',
            'ios': 'mobile_app',
            'android': 'mobile_app'
        }

    def parse_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Parse project specification from file

        Args:
            file_path: Path to specification file

        Returns:
            Parsed specification dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
            ValidationError: If file format is not supported
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Specification file not found: {file_path}")

        file_extension = file_path.suffix.lower().lstrip('.')

        if file_extension not in self.supported_formats and file_extension != '':
            raise ValidationError(f"Unsupported file format: {file_extension}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_extension in ['yaml', 'yml']:
                    return yaml.safe_load(f)
                elif file_extension == 'json':
                    return json.load(f)
                else:
                    # Assume YAML for .yml or no extension
                    return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML format: {e}")
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON format: {e}")

    def parse_string(self, spec_string: str, format_hint: str = 'auto') -> Dict[str, Any]:
        """
        Parse project specification from string

        Args:
            spec_string: Specification as string
            format_hint: Format hint ('json', 'yaml', 'auto')

        Returns:
            Parsed specification dictionary
        """
        if format_hint == 'auto':
            # Auto-detect format
            if spec_string.strip().startswith('{'):
                format_hint = 'json'
            else:
                format_hint = 'yaml'

        try:
            if format_hint == 'json':
                return json.loads(spec_string)
            elif format_hint in ['yaml', 'yml']:
                return yaml.safe_load(spec_string)
            else:
                # Try JSON first, then YAML
                try:
                    return json.loads(spec_string)
                except json.JSONDecodeError:
                    return yaml.safe_load(spec_string)
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ValidationError(f"Invalid {format_hint} format: {e}")

    def parse_dict(self, spec_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse project specification from dictionary (already structured)

        Args:
            spec_dict: Specification as dictionary

        Returns:
            Validated and normalized specification dictionary
        """
        return spec_dict


class ProjectSpecValidator:
    """
    Validate project specifications for Squad-powered development

    Ensures specifications are complete, consistent, and feasible for AI generation.
    """

    def __init__(self):
        """Initialize the validator"""
        self.parser = ProjectSpecParser()
        self.min_requirements_count = 1
        self.min_features_count = 1
        self.max_features_count = 20
        self.max_description_length = 500
        self.max_name_length = 50

    def validate(self, spec: Dict[str, Any]) -> ValidationResult:
        """
        Validate a complete project specification

        Args:
            spec: Project specification dictionary

        Returns:
            ValidationResult with validation status and issues
        """
        result = ValidationResult(is_valid=True)

        # Basic structure validation
        self._validate_basic_structure(spec, result)

        # Field-by-field validation
        self._validate_name(spec, result)
        self._validate_description(spec, result)
        self._validate_project_type(spec, result)
        self._validate_requirements(spec, result)
        self._validate_tech_stack(spec, result)
        self._validate_features(spec, result)
        self._validate_architecture(spec, result)
        self._validate_constraints(spec, result)
        self._validate_target_audience(spec, result)
        self._validate_deployment_target(spec, result)

        # Cross-field validation
        self._validate_dependencies(spec, result)
        self._validate_compatibility(spec, result)

        # Update validity status
        result.is_valid = len(result.get_errors()) == 0

        return result

    def _validate_basic_structure(self, spec: Dict[str, Any], result: ValidationResult):
        """Validate basic specification structure"""
        # Check for required fields
        for field in self.parser.required_fields:
            if field not in spec:
                result.add_error(
                    field,
                    f"Required field '{field}' is missing",
                    f"Add a '{field}' field to your specification"
                )
            elif not spec[field]:
                result.add_error(
                    field,
                    f"Required field '{field}' is empty",
                    f"Provide a value for '{field}'"
                )

    def _validate_name(self, spec: Dict[str, Any], result: ValidationResult):
        """Validate project name"""
        name = spec.get('name', '')

        if not name:
            return

        # Length validation
        if len(name) > self.max_name_length:
            result.add_error(
                'name',
                f"Project name is too long ({len(name)} characters)",
                f"Keep the name under {self.max_name_length} characters"
            )

        # Character validation
        if not name.replace('-', '').replace('_', '').replace(' ', '').isalnum():
            result.add_warning(
                'name',
                "Project name contains special characters",
                "Consider using only letters, numbers, hyphens, underscores, and spaces"
            )

        # Naming conventions
        if ' ' in name and not any(word[0].isupper() for word in name.split()):
            result.add_info(
                'name',
                "Consider using CamelCase or PascalCase for better readability"
            )

    def _validate_description(self, spec: Dict[str, Any], result: ValidationResult):
        """Validate project description"""
        description = spec.get('description', '')

        if not description:
            return

        # Length validation
        if len(description) > self.max_description_length:
            result.add_warning(
                'description',
                f"Description is quite long ({len(description)} characters)",
                "Consider shortening the description for better readability"
            )

        # Content validation
        if len(description.split()) < 5:
            result.add_warning(
                'description',
                "Description might be too brief",
                "Add more detail about the project's purpose and functionality"
            )

    def _validate_project_type(self, spec: Dict[str, Any], result: ValidationResult):
        """Validate project type"""
        project_type = spec.get('project_type', '')

        if not project_type:
            return

        # Normalize project type
        normalized_type = project_type.lower().replace(' ', '_')

        # Check for aliases
        if normalized_type in self.parser.project_type_aliases:
            original_type = project_type
            project_type = self.parser.project_type_aliases[normalized_type]
            result.add_info(
                'project_type',
                f"Using '{original_type}' which maps to '{project_type}'"
            )

        # Validate against known types
        try:
            ProjectType(project_type)
        except ValueError:
            available_types = ', '.join([t.value for t in ProjectType])
            result.add_error(
                'project_type',
                f"Unknown project type: '{project_type}'",
                f"Use one of: {available_types}"
            )

    def _validate_requirements(self, spec: Dict[str, Any], result: ValidationResult):
        """Validate project requirements"""
        requirements = spec.get('requirements', [])

        if not isinstance(requirements, list):
            result.add_error(
                'requirements',
                "Requirements must be a list",
                "Provide requirements as a list of strings"
            )
            return

        # Count validation
        if len(requirements) < self.min_requirements_count:
            result.add_warning(
                'requirements',
                f"At least {self.min_requirements_count} requirement should be specified",
                "Add more detailed requirements for better project generation"
            )

        # Content validation
        for i, req in enumerate(requirements):
            if not isinstance(req, str) or not req.strip():
                result.add_error(
                    f'requirements[{i}]',
                    f"Requirement at index {i} is invalid",
                    "Provide valid requirement text"
                )

    def _validate_tech_stack(self, spec: Dict[str, Any], result: ValidationResult):
        """Validate technology stack"""
        tech_stack = spec.get('tech_stack', [])

        if not isinstance(tech_stack, list):
            result.add_error(
                'tech_stack',
                "Tech stack must be a list",
                "Provide tech stack as a list of technology names"
            )
            return

        # Content validation
        if not tech_stack:
            result.add_warning(
                'tech_stack',
                "No technology stack specified",
                "Add technologies to help generate more appropriate code"
            )

        unknown_technologies = []
        for i, tech in enumerate(tech_stack):
            if not isinstance(tech, str) or not tech.strip():
                result.add_error(
                    f'tech_stack[{i}]',
                    f"Technology at index {i} is invalid",
                    "Provide valid technology name"
                )
                continue

            tech_lower = tech.lower()

            # Check against known technologies
            if not any(tech_lower in category for category in self.parser.known_tech_stacks.values()):
                unknown_technologies.append(tech)

        if unknown_technologies:
            result.add_warning(
                'tech_stack',
                f"Unknown technologies: {', '.join(unknown_technologies)}",
                "Ensure technologies are correctly spelled and supported by Squad"
            )

    def _validate_features(self, spec: Dict[str, Any], result: ValidationResult):
        """Validate project features"""
        features = spec.get('features', [])

        if not isinstance(features, list):
            result.add_error(
                'features',
                "Features must be a list",
                "Provide features as a list of strings"
            )
            return

        # Count validation
        if len(features) < self.min_features_count:
            result.add_warning(
                'features',
                f"At least {self.min_features_count} feature should be specified",
                "Add features to better define the project's scope"
            )
        elif len(features) > self.max_features_count:
            result.add_warning(
                'features',
                f"Too many features ({len(features)})",
                f"Consider limiting to {self.max_features_count} features for focused development"
            )

        # Content validation
        for i, feature in enumerate(features):
            if not isinstance(feature, str) or not feature.strip():
                result.add_error(
                    f'features[{i}]',
                    f"Feature at index {i} is invalid",
                    "Provide valid feature description"
                )

    def _validate_architecture(self, spec: Dict[str, Any], result: ValidationResult):
        """Validate architecture specification"""
        architecture = spec.get('architecture')

        if not architecture:
            result.add_info(
                'architecture',
                "No architecture specified - Squad will use best practices"
            )
            return

        if not isinstance(architecture, str):
            result.add_error(
                'architecture',
                "Architecture must be a string",
                "Provide architecture description as text"
            )

    def _validate_constraints(self, spec: Dict[str, Any], result: ValidationResult):
        """Validate project constraints"""
        constraints = spec.get('constraints')

        if not constraints:
            return

        if not isinstance(constraints, list):
            result.add_error(
                'constraints',
                "Constraints must be a list",
                "Provide constraints as a list of strings"
            )
            return

        for i, constraint in enumerate(constraints):
            if not isinstance(constraint, str) or not constraint.strip():
                result.add_error(
                    f'constraints[{i}]',
                    f"Constraint at index {i} is invalid",
                    "Provide valid constraint description"
                )

    def _validate_target_audience(self, spec: Dict[str, Any], result: ValidationResult):
        """Validate target audience specification"""
        target_audience = spec.get('target_audience')

        if not target_audience:
            return

        if not isinstance(target_audience, str):
            result.add_error(
                'target_audience',
                "Target audience must be a string",
                "Provide target audience description as text"
            )
        elif len(target_audience.strip()) < 5:
            result.add_warning(
                'target_audience',
                "Target audience description might be too brief",
                "Provide more detail about who will use this project"
            )

    def _validate_deployment_target(self, spec: Dict[str, Any], result: ValidationResult):
        """Validate deployment target specification"""
        deployment_target = spec.get('deployment_target')

        if not deployment_target:
            result.add_info(
                'deployment_target',
                "No deployment target specified - using default local deployment"
            )
            return

        valid_targets = ['local', 'docker', 'cloud', 'kubernetes', 'serverless']

        if deployment_target.lower() not in valid_targets:
            result.add_warning(
                'deployment_target',
                f"Unknown deployment target: '{deployment_target}'",
                f"Consider using: {', '.join(valid_targets)}"
            )

    def _validate_dependencies(self, spec: Dict[str, Any], result: ValidationResult):
        """Validate cross-field dependencies"""
        # Ensure tech stack is compatible with project type
        project_type = spec.get('project_type', '').lower()
        tech_stack = spec.get('tech_stack', [])

        if project_type == 'web_app' and not any(
            tech.lower() in self.parser.known_tech_stacks['frontend']
            for tech in tech_stack
        ):
            result.add_warning(
                'tech_stack',
                "No frontend technologies specified for web application",
                "Consider adding React, Vue, or Angular for frontend development"
            )

        if project_type == 'api_service' and not any(
            tech.lower() in self.parser.known_tech_stacks['backend']
            for tech in tech_stack
        ):
            result.add_warning(
                'tech_stack',
                "No backend technologies specified for API service",
                "Consider adding Node.js, Python, or Java for backend development"
            )

    def _validate_compatibility(self, spec: Dict[str, Any], result: ValidationResult):
        """Validate compatibility and consistency"""
        tech_stack = spec.get('tech_stack', [])
        features = spec.get('features', [])
        project_type = spec.get('project_type', '')

        # Check for conflicting technologies
        conflicting_pairs = [
            (['react', 'vue'], 'Multiple frontend frameworks specified'),
            (['mysql', 'postgresql'], 'Multiple databases specified'),
            (['nodejs', 'python'], 'Multiple backend languages specified'),
        ]

        for conflicting_techs, message in conflicting_pairs:
            found_techs = [tech for tech in tech_stack
                          if any(conflict.lower() in tech.lower() for conflict in conflicting_techs)]
            if len(found_techs) > 1:
                result.add_warning(
                    'tech_stack',
                    f"{message}: {', '.join(found_techs)}",
                    "Consider choosing one technology from each category"
                )

        # Feature-tech stack alignment
        web_features = ['dashboard', 'login', 'user interface', 'frontend', 'spa']
        api_features = ['rest api', 'endpoint', 'authentication', 'database']

        if any(feature.lower() in web_features for feature in features):
            if not any(tech.lower() in self.parser.known_tech_stacks['frontend'] for tech in tech_stack):
                result.add_warning(
                    'features',
                    "Web features specified but no frontend technologies",
                    "Add frontend technologies like React or Vue for web interface"
                )

        if any(feature.lower() in api_features for feature in features):
            if not any(tech.lower() in self.parser.known_tech_stacks['backend'] for tech in tech_stack):
                result.add_warning(
                    'features',
                    "API features specified but no backend technologies",
                    "Add backend technologies like Node.js or Python for API development"
                )


class ProjectSpecNormalizer:
    """
    Normalize and enhance project specifications

    Applies defaults, normalizes formatting, and enhances specifications
    for optimal Squad generation.
    """

    def __init__(self):
        """Initialize the normalizer"""
        self.validator = ProjectSpecValidator()

    def normalize(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize and enhance project specification

        Args:
            spec: Raw project specification

        Returns:
            Normalized specification dictionary
        """
        normalized = spec.copy()

        # Apply defaults
        self._apply_defaults(normalized)

        # Normalize formatting
        self._normalize_formatting(normalized)

        # Enhance with recommendations
        self._enhance_specification(normalized)

        # Auto-populate missing fields
        self._auto_populate_fields(normalized)

        return normalized

    def _apply_defaults(self, spec: Dict[str, Any]):
        """Apply sensible defaults to specification"""
        # Set default project type if not specified
        if 'project_type' not in spec or not spec['project_type']:
            # Try to infer from tech stack or features
            tech_stack = spec.get('tech_stack', [])
            features = spec.get('features', [])

            if any(tech.lower() in ['react', 'vue', 'angular'] for tech in tech_stack):
                spec['project_type'] = 'web_app'
            elif any(feature.lower() in ['api', 'rest', 'endpoint'] for feature in features):
                spec['project_type'] = 'api_service'
            else:
                spec['project_type'] = 'web_app'  # Default fallback

        # Set default deployment target
        if 'deployment_target' not in spec or not spec['deployment_target']:
            spec['deployment_target'] = 'local'

        # Initialize empty lists if not provided
        if 'requirements' not in spec:
            spec['requirements'] = []
        if 'tech_stack' not in spec:
            spec['tech_stack'] = []
        if 'features' not in spec:
            spec['features'] = []
        if 'constraints' not in spec:
            spec['constraints'] = []

    def _normalize_formatting(self, spec: Dict[str, Any]):
        """Normalize text formatting in specification"""
        # Normalize name
        if 'name' in spec:
            spec['name'] = spec['name'].strip().title()

        # Normalize description
        if 'description' in spec:
            spec['description'] = ' '.join(spec['description'].strip().split())

        # Normalize project type
        if 'project_type' in spec:
            spec['project_type'] = spec['project_type'].lower().replace(' ', '_')

        # Clean up lists
        for field in ['requirements', 'tech_stack', 'features', 'constraints']:
            if field in spec and isinstance(spec[field], list):
                # Remove empty strings and normalize
                spec[field] = [item.strip() for item in spec[field] if item and item.strip()]

    def _enhance_specification(self, spec: Dict[str, Any]):
        """Enhance specification with recommendations"""
        tech_stack = spec.get('tech_stack', [])
        project_type = spec.get('project_type', '')

        # Suggest missing technologies based on project type
        if project_type == 'web_app':
            missing_frontend = not any(
                tech.lower() in self.validator.parser.known_tech_stacks['frontend']
                for tech in tech_stack
            )
            if missing_frontend:
                if 'react' not in [t.lower() for t in tech_stack]:
                    tech_stack.append('react')

        elif project_type == 'api_service':
            missing_backend = not any(
                tech.lower() in self.validator.parser.known_tech_stacks['backend']
                for tech in tech_stack
            )
            if missing_backend:
                if 'python' not in [t.lower() for t in tech_stack]:
                    tech_stack.append('python')

        # Update tech stack
        spec['tech_stack'] = tech_stack

    def _auto_populate_fields(self, spec: Dict[str, Any]):
        """Auto-populate missing fields based on available information"""
        # Auto-generate basic requirements if none provided
        if not spec.get('requirements'):
            project_type = spec.get('project_type', '')
            name = spec.get('name', '')

            basic_requirements = [
                f"Build a {project_type.replace('_', ' ')} application",
                f"Implement core functionality for {name}",
                "Ensure responsive design and user experience",
                "Include error handling and validation"
            ]
            spec['requirements'] = basic_requirements

        # Auto-generate basic features if none provided
        if not spec.get('features'):
            project_type = spec.get('project_type', '')

            if project_type == 'web_app':
                spec['features'] = ['User interface', 'Navigation', 'Responsive design']
            elif project_type == 'api_service':
                spec['features'] = ['REST API endpoints', 'Data validation', 'Error handling']
            else:
                spec['features'] = ['Core functionality', 'User interface', 'Data management']


# Convenience functions for easy use
def parse_and_validate_specification(
    spec_input: Union[str, Path, Dict[str, Any]],
    format_hint: str = 'auto'
) -> tuple[Dict[str, Any], ValidationResult]:
    """
    Parse and validate a project specification

    Args:
        spec_input: Specification as string, file path, or dictionary
        format_hint: Format hint for string input

    Returns:
        Tuple of (normalized_specification, validation_result)
    """
    parser = ProjectSpecParser()
    validator = ProjectSpecValidator()
    normalizer = ProjectSpecNormalizer()

    # Parse specification
    if isinstance(spec_input, dict):
        spec = spec_input
    elif isinstance(spec_input, (str, Path)):
        if isinstance(spec_input, Path) or Path(spec_input).exists():
            spec = parser.parse_file(spec_input)
        else:
            spec = parser.parse_string(spec_input, format_hint)
    else:
        raise ValidationError("Invalid specification input type")

    # Validate specification
    validation_result = validator.validate(spec)

    # Normalize specification
    normalized_spec = normalizer.normalize(spec)

    # Merge validation results for normalized spec
    normalized_validation = validator.validate(normalized_spec)
    validation_result.issues.extend(normalized_validation.issues)
    validation_result.is_valid = len(validation_result.get_errors()) == 0

    return normalized_spec, validation_result


def load_specification_template(template_name: str = 'basic') -> Dict[str, Any]:
    """
    Load a project specification template

    Args:
        template_name: Name of template ('basic', 'web_app', 'api_service')

    Returns:
        Specification template dictionary
    """
    templates = {
        'basic': {
            'name': 'My Project',
            'description': 'A brief description of what this project does',
            'project_type': 'web_app',
            'requirements': [
                'Create a functional application',
                'Implement user interface',
                'Add data persistence'
            ],
            'tech_stack': ['react', 'nodejs', 'postgresql'],
            'features': ['User management', 'Dashboard', 'Data visualization'],
            'architecture': None,
            'constraints': [],
            'target_audience': 'General users',
            'deployment_target': 'local'
        },
        'web_app': {
            'name': 'Web Application',
            'description': 'A modern web application with responsive design',
            'project_type': 'web_app',
            'requirements': [
                'Build responsive user interface',
                'Implement client-side routing',
                'Add state management',
                'Integrate with backend APIs'
            ],
            'tech_stack': ['react', 'tailwind', 'vite'],
            'features': ['Single Page Application', 'Responsive design', 'Modern UI'],
            'architecture': 'SPA with component-based architecture',
            'constraints': ['Must work on mobile devices'],
            'target_audience': 'Web users',
            'deployment_target': 'docker'
        },
        'api_service': {
            'name': 'REST API Service',
            'description': 'A RESTful API service with authentication and data management',
            'project_type': 'api_service',
            'requirements': [
                'Create RESTful API endpoints',
                'Implement authentication',
                'Add data validation',
                'Include error handling'
            ],
            'tech_stack': ['fastapi', 'postgresql', 'redis'],
            'features': ['REST API', 'JWT authentication', 'Data validation'],
            'architecture': 'Microservice with layered architecture',
            'constraints': ['Must handle 1000+ concurrent requests'],
            'target_audience': 'API consumers',
            'deployment_target': 'kubernetes'
        }
    }

    return templates.get(template_name, templates['basic'])


def create_specification_interactive() -> Dict[str, Any]:
    """
    Interactive specification creation (simplified version)

    This would normally be an interactive CLI, but for demonstration
    we'll return a basic structure that users can fill in.
    """
    return {
        'name': 'TODO: Enter your project name',
        'description': 'TODO: Describe what your project does',
        'project_type': 'TODO: Choose from web_app, api_service, full_stack, etc.',
        'requirements': [
            'TODO: List what this project must accomplish'
        ],
        'tech_stack': [
            'TODO: List technologies (e.g., react, python, postgresql)'
        ],
        'features': [
            'TODO: List key features you want'
        ],
        'architecture': 'TODO: Optional - describe preferred architecture',
        'constraints': [],
        'target_audience': 'TODO: Optional - who will use this',
        'deployment_target': 'TODO: Optional - local, docker, cloud, etc.'
    }
