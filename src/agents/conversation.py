"""
Conversation State Manager
Story 1.5: Conversation State Manager (Redis)

Manages conversation history per user/agent in Redis
"""

import json
import logging
from typing import List, Optional, Dict

import redis.asyncio as redis

from src.models.conversation import ConversationHistory, Message

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversation state in Redis"""
    
    MAX_MESSAGES = 50  # Rolling window
    TTL_SECONDS = 3600  # 1 hour inactivity
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize Conversation Manager
        
        Args:
            redis_client: Redis client for state persistence (optional for testing)
        """
        self.redis = redis_client
        self._memory_cache: Dict[str, List[dict]] = {}  # In-memory fallback
    
    async def add_message(
        self,
        user_id: str,
        agent_id: str,
        role: str,  # "user" or "assistant"
        content: str
    ):
        """
        Add message to conversation history
        
        Args:
            user_id: User identifier
            agent_id: Agent identifier (e.g., 'analyst')
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        key = self._make_key(user_id, agent_id)
        
        # Get existing history
        history = await self.get_history(user_id, agent_id)
        
        # Add new message
        history.add_message(role, content)
        
        # Trim to max messages
        history.trim_to(self.MAX_MESSAGES)
        
        # Save to Redis with TTL
        await self._save_history(key, history)
    
    async def get_history(
        self,
        user_id: str,
        agent_id: str
    ) -> ConversationHistory:
        """
        Get conversation history from Redis
        
        Returns:
            ConversationHistory (empty if not found)
        """
        key = self._make_key(user_id, agent_id)
        
        try:
            if self.redis:
                data = await self.redis.get(key)
                
                if data:
                    messages_data = json.loads(data)
                    messages = [Message(**m) for m in messages_data]
                    
                    return ConversationHistory(
                        user_id=user_id,
                        agent_id=agent_id,
                        messages=messages
                    )
            else:
                # Fallback to memory
                if key in self._memory_cache:
                    messages_data = self._memory_cache[key]
                    messages = [Message(**m) for m in messages_data]
                    
                    return ConversationHistory(
                        user_id=user_id,
                        agent_id=agent_id,
                        messages=messages
                    )
        except Exception as e:
            logger.warning(f"Failed to load conversation history for {key}: {e}")
        
        # Return empty history
        return ConversationHistory(user_id=user_id, agent_id=agent_id)
    
    async def get_messages(
        self,
        user_id: str,
        agent_id: str
    ) -> List[dict]:
        """
        Get messages in OpenAI chat format
        
        Returns:
            List of message dicts: [{"role": "user", "content": "..."}]
        """
        history = await self.get_history(user_id, agent_id)
        return history.to_openai_format()
    
    async def clear_history(self, user_id: str, agent_id: str):
        """Clear conversation history"""
        key = self._make_key(user_id, agent_id)
        
        if self.redis:
            await self.redis.delete(key)
        else:
            self._memory_cache.pop(key, None)
    
    async def _save_history(self, key: str, history: ConversationHistory):
        """Save history to Redis with TTL"""
        messages_data = [m.model_dump() for m in history.messages]
        
        if self.redis:
            await self.redis.setex(
                key,
                self.TTL_SECONDS,
                json.dumps(messages_data)
            )
        else:
            # Fallback to memory
            self._memory_cache[key] = messages_data
    
    def _make_key(self, user_id: str, agent_id: str) -> str:
        """Build Redis key for conversation"""
        return f"conversation:{user_id}:{agent_id}"

