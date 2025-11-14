"""
Squad Project Generator CLI and Pipeline Coordinator
Story: Main interface for Squad-powered development

This module provides the primary CLI interface and coordinates the entire
project generation pipeline from specification to final deliverables.
"""

import asyncio
import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.syntax import Syntax

from .project_generator import ProjectGenerator, ProjectSpec, ProjectType
from .spec_parser import (
    parse_and_validate_specification,
    load_specification_template,
    ValidationResult,
    ValidationError
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

console = Console()


class SquadProjectGeneratorCLI:
    """
    Command-line interface for Squad-powered project generation

    Provides an intuitive interface for users to generate complete software projects
    using AI agents through the Squad API.
    """

    def __init__(self, orchestrator, output_dir: str = "generated_projects"):
        """
        Initialize CLI

        Args:
            orchestrator: Squad API orchestrator instance
            output_dir: Default directory for generated projects
        """
        self.generator = ProjectGenerator(orchestrator, output_dir)
        self.output_dir = Path(output_dir)

    def generate_from_file(self, spec_file: Path, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate project from specification file

        Args:
            spec_file: Path to project specification file
            output_dir: Override output directory

        Returns:
            Generation result dictionary
        """
        console.print(f"\n[bold blue]🚀 Squad Project Generator[/bold blue]")
        console.print(f"[dim]Generating project from: {spec_file}[/dim]\n")

        try:
            # Parse and validate specification
            console.print("[yellow]📋 Parsing specification...[/yellow]")
            spec, validation_result = parse_and_validate_specification(spec_file)

            # Show validation results
            self._display_validation_results(validation_result)

            if not validation_result.is_valid:
                console.print("\n[red]❌ Specification validation failed![/red]")
                console.print("Please fix the errors above and try again.")
                return {"success": False, "errors": validation_result.get_errors()}

            # Update output directory if specified
            if output_dir:
                self.generator.output_dir = Path(output_dir)
                self.generator.output_dir.mkdir(exist_ok=True)

            # Generate project
            return asyncio.run(self._generate_project_async(spec))

        except Exception as e:
            console.print(f"\n[red]❌ Error: {e}[/red]")
            return {"success": False, "error": str(e)}

    def generate_from_template(self, template_name: str, project_name: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate project from template

        Args:
            template_name: Name of template to use
            project_name: Name for the new project
            output_dir: Override output directory

        Returns:
            Generation result dictionary
        """
        console.print(f"\n[bold blue]🚀 Squad Project Generator[/bold blue]")
        console.print(f"[dim]Creating project '{project_name}' from template '{template_name}'[/dim]\n")

        try:
            # Load template
            console.print("[yellow]📋 Loading template...[/yellow]")
            template_spec = load_specification_template(template_name)
            template_spec['name'] = project_name

            # Update output directory if specified
            if output_dir:
                self.generator.output_dir = Path(output_dir)
                self.generator.output_dir.mkdir(exist_ok=True)

            # Generate project
            return asyncio.run(self._generate_project_async(template_spec))

        except Exception as e:
            console.print(f"\n[red]❌ Error: {e}[/red]")
            return {"success": False, "error": str(e)}

    async def _generate_project_async(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Async wrapper for project generation"""
        # Create ProjectSpec object
        project_spec = ProjectSpec(
            name=spec['name'],
            description=spec['description'],
            project_type=ProjectType(spec['project_type']),
            requirements=spec['requirements'],
            tech_stack=spec['tech_stack'],
            features=spec['features'],
            architecture=spec.get('architecture'),
            constraints=spec.get('constraints', []),
            target_audience=spec.get('target_audience'),
            deployment_target=spec.get('deployment_target', 'local')
        )

        # Generate project with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:

            # Start generation task
            task = progress.add_task("🎯 Planning project architecture...", total=None)

            try:
                # Generate project
                result = await self.generator.generate_project(project_spec)

                # Update progress
                progress.update(task, description="✅ Project generated successfully!")

                # Display results
                self._display_generation_results(result)

                return {
                    "success": True,
                    "project_id": result.project_id,
                    "project_path": result.artifacts_path,
                    "files_created": result.files_created,
                    "generation_time": result.generation_time,
                    "errors": result.errors
                }

            except Exception as e:
                progress.update(task, description="❌ Generation failed!")
                console.print(f"\n[red]❌ Generation failed: {e}[/red]")
                return {"success": False, "error": str(e)}

    def _display_validation_results(self, validation_result: ValidationResult):
        """Display validation results in a nice format"""
        if validation_result.is_valid and not validation_result.issues:
            console.print("[green]✅ Specification is valid![/green]\n")
            return

        # Create table for issues
        table = Table(title="🔍 Specification Validation Results")
        table.add_column("Severity", style="bold")
        table.add_column("Field", style="cyan")
        table.add_column("Message", style="white")
        table.add_column("Suggestion", style="dim")

        for issue in validation_result.issues:
            severity_style = {
                "error": "red",
                "warning": "yellow",
                "info": "blue"
            }.get(issue.severity.value, "white")

            table.add_row(
                f"[{severity_style}]{issue.severity.value.upper()}[/{severity_style}]",
                issue.field,
                issue.message,
                issue.suggestion or ""
            )

        console.print(table)
        console.print()

    def _display_generation_results(self, result):
        """Display generation results in a nice format"""
        # Summary panel
        status_color = "green" if result.status.value == "completed" else "red"
        summary = f"""[bold]Project:[/bold] {result.spec.name}
[bold]Type:[/bold] {result.spec.project_type.value}
[bold]Status:[/bold] [{status_color}]{result.status.value.upper()}[/{status_color}]
[bold]Files Created:[/bold] {len(result.files_created)}
[bold]Generation Time:[/bold] {result.generation_time:.2f}s
[bold]Output Path:[/bold] {result.artifacts_path}"""

        console.print(Panel(summary, title="🎉 Generation Complete", border_style="blue"))

        # Show some created files
        if result.files_created:
            console.print("\n[bold]📁 Files Created:[/bold]")
            for file_path in result.files_created[:10]:  # Show first 10 files
                relative_path = Path(file_path).relative_to(self.output_dir)
                console.print(f"  • {relative_path}")

            if len(result.files_created) > 10:
                console.print(f"  ... and {len(result.files_created) - 10} more files")

        # Show any errors
        if result.errors:
            console.print("\n[bold yellow]⚠️ Issues Encountered:[/bold yellow]")
            for error in result.errors:
                console.print(f"  • {error}")

        # Show next steps
        console.print("\n[bold]🚀 Next Steps:[/bold]")
        console.print(f"  1. Navigate to: {result.artifacts_path}")
        console.print("  2. Review the generated code")
        console.print("  3. Run: npm install  (or pip install -r requirements.txt)")
        console.print("  4. Follow the deployment guide in DEPLOYMENT_GUIDE.md")
        console.print(f"  5. Check PROJECT_SUMMARY.md for detailed information")


def create_cli(orchestrator) -> SquadProjectGeneratorCLI:
    """
    Create and configure the CLI interface

    Args:
        orchestrator: Squad API orchestrator instance

    Returns:
        Configured CLI instance
    """
    cli = SquadProjectGeneratorCLI(orchestrator)
    return cli


# Click CLI interface
@click.group()
@click.pass_context
def cli(ctx):
    """Squad API - AI-Powered Project Generator

    Generate complete software projects using Squad's AI agents.

    Examples:
        squad-generate spec.yaml
        squad-generate --template web_app my-project
        squad-generate --list-templates
    """
    ctx.ensure_object(dict)
    # CLI is handled by the SquadProjectGeneratorCLI class


@cli.command()
@click.argument('spec_file', type=click.Path(exists=True))
@click.option('--output-dir', '-o', help='Output directory for generated project')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def generate(ctx, spec_file, output_dir, verbose):
    """Generate a project from a specification file"""
    orchestrator = ctx.obj.get('orchestrator')
    if not orchestrator:
        console.print("[red]Error: Orchestrator not available[/red]")
        return

    cli_instance = create_cli(orchestrator)

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    result = cli_instance.generate_from_file(Path(spec_file), output_dir)

    if not result.get('success'):
        sys.exit(1)


@cli.command()
@click.argument('project_name')
@click.option('--template', '-t', default='basic', help='Template to use')
@click.option('--output-dir', '-o', help='Output directory for generated project')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def create(ctx, project_name, template, output_dir, verbose):
    """Create a new project from a template"""
    orchestrator = ctx.obj.get('orchestrator')
    if not orchestrator:
        console.print("[red]Error: Orchestrator not available[/red]")
        return

    cli_instance = create_cli(orchestrator)

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    result = cli_instance.generate_from_template(template, project_name, output_dir)

    if not result.get('success'):
        sys.exit(1)


@cli.command()
def list_templates():
    """List available project templates"""
    templates = {
        'basic': 'Basic project with React frontend and Python backend',
        'web_app': 'Modern web application with React and Node.js',
        'api_service': 'RESTful API service with FastAPI and PostgreSQL'
    }

    table = Table(title="📋 Available Templates")
    table.add_column("Template", style="cyan")
    table.add_column("Description", style="white")

    for template_name, description in templates.items():
        table.add_row(template_name, description)

    console.print(table)


@cli.command()
@click.option('--output-file', '-o', help='Output file for specification template')
@click.option('--template', '-t', default='basic', help='Template to generate')
def init_spec(output_file, template):
    """Initialize a project specification from template"""
    if not output_file:
        output_file = f"{template}_spec.yaml"

    template_spec = load_specification_template(template)

    # Convert to YAML for better readability
    import yaml
    spec_yaml = yaml.dump(template_spec, default_flow_style=False, sort_keys=False)

    with open(output_file, 'w') as f:
        f.write(spec_yaml)

    console.print(f"[green]✅ Specification template created: {output_file}[/green]")
    console.print(f"[dim]Edit this file with your project details and run:[/dim]")
    console.print(f"[blue]squad-generate {output_file}[/blue]")


@cli.command()
@click.argument('project_dir', type=click.Path())
def status(project_dir):
    """Show status of a generated project"""
    project_path = Path(project_dir)

    if not project_path.exists():
        console.print(f"[red]Error: Project directory not found: {project_path}[/red]")
        return

    # Look for metadata file
    metadata_file = project_path / 'project_metadata.json'
    if metadata_file.exists():
        with open(metadata_file) as f:
            metadata = json.load(f)

        # Display project info
        table = Table(title="📊 Project Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Name", metadata.get('name', 'N/A'))
        table.add_row("Type", metadata.get('type', 'N/A'))
        table.add_row("Generated", metadata.get('generated_at', 'N/A'))
        table.add_row("Tech Stack", ', '.join(metadata.get('tech_stack', [])))
        table.add_row("Files Created", str(metadata.get('generation_results', {}).get('files_created', 0)))

        console.print(table)

        # Show recent files
        files = list(project_path.rglob('*'))
        if files:
            console.print(f"\n[bold]📁 Project Structure ([/bold]{len(files)} files):")
            for file_path in sorted(files)[:20]:  # Show first 20
                if file_path.is_file():
                    relative_path = file_path.relative_to(project_path)
                    console.print(f"  • {relative_path}")

            if len(files) > 20:
                console.print(f"  ... and {len(files) - 20} more items")
    else:
        console.print("[yellow]⚠️ No metadata found - this may not be a Squad-generated project[/yellow]")


if __name__ == '__main__':
    # Example usage when run directly
    console.print("[bold blue]🚀 Squad Project Generator CLI[/bold blue]")
    console.print("[dim]Use this module as part of the Squad API system[/dim]")

    # You would need to provide an orchestrator instance here
    # For demonstration, we'll show the help
    import subprocess
    subprocess.run([sys.executable, __file__, '--help'])
