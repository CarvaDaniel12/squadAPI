"""Validation helpers for prompt plans and Agile/BMAD compliance."""
from __future__ import annotations

from typing import Collection, Dict, Set

from src.models.prompt_plan import PromptPlan


class ProcessComplianceError(RuntimeError):
    """Raised when a prompt plan fails Agile/BMAD validation."""


def validate_prompt_plan(plan: PromptPlan, available_providers: Collection[str]) -> None:
    """Validate basic correctness of a prompt plan before execution."""
    if plan.agile.methodology != "BMAD-Agile":
        raise ProcessComplianceError(
            f"Prompt plan must use BMAD-Agile methodology, received {plan.agile.methodology}"
        )

    if not plan.agile.compliance_checklist:
        raise ProcessComplianceError("Compliance checklist cannot be empty")

    provider_set = set(available_providers)

    task_ids: Set[str] = set()
    for task in plan.tasks:
        if task.id in task_ids:
            raise ProcessComplianceError(f"Duplicate task id detected: {task.id}")
        task_ids.add(task.id)

        if task.provider not in provider_set:
            raise ProcessComplianceError(
                f"Task {task.id} references provider '{task.provider}' which is not configured. "
                f"Available providers: {list(provider_set)}"
            )

        for dep in task.inputs:
            if dep == task.id:
                raise ProcessComplianceError(f"Task {task.id} cannot depend on itself")

    _validate_dag(plan)


def _validate_dag(plan: PromptPlan) -> None:
    graph: Dict[str, Set[str]] = {task.id: set(task.inputs) for task in plan.tasks}

    # ensure dependencies exist
    for task_id, deps in graph.items():
        missing = deps - graph.keys()
        if missing:
            raise ProcessComplianceError(
                f"Task '{task_id}' depends on missing tasks: {', '.join(sorted(missing))}"
            )

    temporary: Set[str] = set()
    permanent: Set[str] = set()

    def visit(node: str) -> None:
        if node in permanent:
            return
        if node in temporary:
            raise ProcessComplianceError("Cyclic dependency detected in prompt plan")
        temporary.add(node)
        for dep in graph[node]:
            visit(dep)
        temporary.remove(node)
        permanent.add(node)

    for node in graph:
        if node not in permanent:
            visit(node)
