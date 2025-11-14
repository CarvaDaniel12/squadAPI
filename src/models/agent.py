"""
Agent Definition Models
Story 1.2: Agent Definition Models (Pydantic)
"""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class Persona(BaseModel):
    """Agent persona definition"""
    role: str
    identity: str
    communication_style: str
    principles: str


class MenuItem(BaseModel):
    """Menu item definition"""
    cmd: str
    description: Optional[str] = None
    workflow: Optional[str] = None
    exec: Optional[str] = None
    data: Optional[str] = None
    action: Optional[str] = None


class AgentDefinition(BaseModel):
    """Complete agent definition parsed from .bmad agent file"""
    id: str = Field(..., description="Agent ID (e.g., 'analyst')")
    name: str = Field(..., description="Agent name (e.g., 'Mary')")
    title: str = Field(..., description="Agent title (e.g., 'Business Analyst')")
    icon: str = Field(..., description="Agent icon emoji")
    persona: Persona
    menu: List[MenuItem]
    workflows: List[str] = Field(default_factory=list, description="Workflow paths from menu")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "analyst",
                "name": "Mary",
                "title": "Business Analyst",
                "icon": "",
                "persona": {
                    "role": "Business Analyst",
                    "identity": "Strategic thinker...",
                    "communication_style": "Clear and structured",
                    "principles": "Data-driven decisions"
                },
                "menu": [
                    {"cmd": "*help", "description": "Show menu"},
                    {"cmd": "*research", "workflow": ".bmad/bmm/workflows/research/workflow.yaml"}
                ],
                "workflows": [".bmad/bmm/workflows/research/workflow.yaml"]
            }
        }
    )


