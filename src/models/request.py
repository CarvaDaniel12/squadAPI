"""
Request Models
Story 1.7: Agent Execution Orchestrator
Epic 8: Enhanced OpenAPI Documentation
"""

from typing import Any, Dict, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class AgentExecutionRequest(BaseModel):
    """Agent execution payload shared between FastAPI and the orchestrator."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "prompt": "Write a Python function to calculate Fibonacci numbers",

                    "conversation_id": "test-123",
                    "metadata": {
                        "user_id": "john@example.com"
                    }
                },
                {
                    "prompt": "Continue from the previous response and add error handling",
                    "conversation_id": "test-123",
                    "max_tokens": 2000,
                    "temperature": 0.5
                }
            ]
        }
    )

    agent: Optional[str] = Field(
        default=None,
        description="Agent identifier resolved from the router",
        min_length=1,
        examples=["analyst", "code", "creative"]
    )

    user_id: Optional[str] = Field(
        default=None,
        description="End-user identifier for conversation tracking",
        min_length=1,
        examples=["user-123", "customer-42"]
    )

    task: str = Field(
        ...,
        alias="prompt",
        validation_alias=AliasChoices("prompt", "task"),
        description="The task or question for the agent to process",
        min_length=1,
        max_length=10000,
        examples=[
            "Write a Python function to calculate Fibonacci numbers",
            "Analyze the performance bottlenecks in this system",
            "Create a marketing email for our new product launch"
        ]
    )

    conversation_id: Optional[str] = Field(
        default=None,
        description="Optional conversation ID for multi-turn dialogs. Use the same ID to maintain context across requests.",
        examples=["conv-123", "session-abc", None]
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata for tracking and analytics",
        examples=[
            {"user_id": "john@example.com", "session": "abc123"},
            {"source": "web-app", "version": "1.2.0"}
        ]
    )

    max_tokens: Optional[int] = Field(
        default=None,
        description="Maximum tokens in the response (provider-specific)",
        ge=1,
        le=100000,
        examples=[1000, 2000, None]
    )

    temperature: Optional[float] = Field(
        default=None,
        description="Sampling temperature (0.0 = deterministic, 1.0 = creative)",
        ge=0.0,
        le=2.0,
        examples=[0.7, 0.0, 1.0]
    )

    @property
    def prompt(self) -> str:
        """Expose the new prompt name without breaking orchestrator expectations."""
        return self.task


