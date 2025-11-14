"""Prompt planning schemas for local optimizer and Agile enforcement."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, validator


Methodology = Literal["BMAD-Agile"]
TaskRole = Literal["analyst", "developer", "reviewer", "qa", "ops"]
AggregationStrategy = Literal["local_summarizer", "vote", "chain-of-thought"]
Ceremony = Literal["Planning", "Daily", "Review", "Retro"]


class AgileMetadata(BaseModel):
    """Container for BMAD/Agile governance details that every plan must include."""

    methodology: Methodology = Field(default="BMAD-Agile")
    sprint_goal: str = Field(..., description="Sprint objective this work contributes to")
    backlog_item_id: str = Field(..., description="Unique backlog reference")
    priority: Literal["P0", "P1", "P2", "P3"]
    acceptance_criteria: List[str] = Field(..., min_items=1)
    ceremonies: List[Ceremony] = Field(..., description="Required ceremonies for this work")
    bmad_phase: Literal["Blueprint", "Mobilize", "Accelerate", "Deliver"]
    compliance_checklist: List[str] = Field(
        ..., description="Checklist entries satisfied for BMAD compliance"
    )
    requires_approval: bool = Field(
        default=True,
        description="True when BMAD governance must sign off before execution",
    )

    model_config = ConfigDict(frozen=True)


class SpecialistTask(BaseModel):
    """Single specialist instruction destined for a remote LLM provider."""

    id: str
    role: TaskRole
    provider: str = Field(..., description="Provider key defined in config/providers.yaml")
    expertise_context: str = Field(..., description="Persona/system prompt context for the provider")
    task_prompt: str = Field(..., description="Final prompt that will be sent downstream")
    blocking: bool = False
    inputs: List[str] = Field(default_factory=list, description="IDs of prerequisite tasks")
    expected_outputs: List[str] = Field(..., min_items=1)
    definition_of_done: List[str] = Field(..., min_items=1)

    model_config = ConfigDict(frozen=True)

    @validator("id")
    def ensure_id(cls, value: str) -> str:  # noqa: D401
        """Ensure IDs are non-empty and trimmed."""
        if not value or not value.strip():
            raise ValueError("Task id must be non-empty")
        return value.strip()


class PromptPlan(BaseModel):
    """Normalized representation of user intent plus Agile metadata."""

    user_request: str
    normalized_problem: str
    agile: AgileMetadata
    tasks: List[SpecialistTask]
    aggregation_strategy: AggregationStrategy = "local_summarizer"
    post_processing_prompt: str = Field(
        ..., description="Prompt for local aggregator to synthesize remote responses"
    )

    model_config = ConfigDict(frozen=True)

    @validator("tasks")
    def ensure_tasks_not_empty(cls, value: List[SpecialistTask]) -> List[SpecialistTask]:
        if not value:
            raise ValueError("Prompt plan must include at least one specialist task")
        return value
