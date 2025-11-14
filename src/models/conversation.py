"""
Conversation Models
Story 1.5: Conversation State Manager
"""

from typing import List, Literal
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Single conversation message"""
    role: Literal["user", "assistant", "system"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")


class ConversationHistory(BaseModel):
    """Complete conversation history"""
    user_id: str
    agent_id: str
    messages: List[Message] = Field(default_factory=list)
    
    def add_message(self, role: str, content: str):
        """Add message to history"""
        self.messages.append(Message(role=role, content=content))
    
    def trim_to(self, max_messages: int = 50):
        """Trim to last N messages"""
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]
    
    def to_openai_format(self) -> List[dict]:
        """Convert to OpenAI chat format"""
        return [{"role": m.role, "content": m.content} for m in self.messages]

