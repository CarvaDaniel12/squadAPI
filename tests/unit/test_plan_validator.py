"""Unit tests for prompt plan validation guardrails."""

import pytest

from src.agents.plan_validator import ProcessComplianceError, validate_prompt_plan
from src.models.prompt_plan import AgileMetadata, PromptPlan, SpecialistTask


def _agile_metadata() -> AgileMetadata:
    return AgileMetadata(
        sprint_goal="Improve analyst insights",
        backlog_item_id="B-123",
        priority="P1",
        acceptance_criteria=["Analyst can reference BMAD artifacts"],
        ceremonies=["Planning", "Daily"],
        bmad_phase="Blueprint",
        compliance_checklist=["Checklist item"],
        requires_approval=True,
    )


def _task(task_id: str, provider: str = "groq", inputs=None) -> SpecialistTask:
    return SpecialistTask(
        id=task_id,
        role="analyst",
        provider=provider,
        expertise_context="You are the analyst",
        task_prompt=f"Do work for {task_id}",
        blocking=False,
        inputs=list(inputs or []),
        expected_outputs=["summary"],
        definition_of_done=["Complete"],
    )


def _plan(*tasks: SpecialistTask) -> PromptPlan:
    return PromptPlan(
        user_request="Summarize backlog",
        normalized_problem="Normalized backlog",
        agile=_agile_metadata(),
        tasks=list(tasks),
        post_processing_prompt="Combine everything",
    )


class TestPromptPlanValidator:
    def test_accepts_valid_plan(self):
        plan = _plan(
            _task("analysis"),
            _task("review", inputs=["analysis"]),
        )

        # Should not raise
        validate_prompt_plan(plan, available_providers={"groq"})

    def test_rejects_unknown_provider(self):
        plan = _plan(_task("analysis", provider="unknown"))

        with pytest.raises(ProcessComplianceError) as exc:
            validate_prompt_plan(plan, available_providers={"groq"})

        assert "not configured" in str(exc.value)

    def test_detects_cyclic_dependencies(self):
        plan = _plan(
            _task("analysis", inputs=["review"]),
            _task("review", inputs=["analysis"]),
        )

        with pytest.raises(ProcessComplianceError) as exc:
            validate_prompt_plan(plan, available_providers={"groq"})

        assert "Cyclic" in str(exc.value)
