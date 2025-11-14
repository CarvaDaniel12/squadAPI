"""
Unit tests for Conversation Manager
Story 1.5: Conversation State Manager - Tests
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from src.agents.conversation import ConversationManager
from src.models.conversation import ConversationHistory, Message


class TestConversationManager:
    """Test suite for ConversationManager"""
    
    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client"""
        redis_mock = AsyncMock()
        return redis_mock
    
    @pytest.fixture
    def manager(self, mock_redis):
        """Create conversation manager with mock Redis"""
        return ConversationManager(redis_client=mock_redis)
    
    @pytest.mark.asyncio
    async def test_add_message_creates_history(self, manager, mock_redis):
        """Test adding first message creates conversation"""
        # Arrange
        mock_redis.get.return_value = None  # No existing history
        
        # Act
        await manager.add_message("dani", "analyst", "user", "Hello Mary!")
        
        # Assert
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        
        # Verify key format
        assert call_args[0][0] == "conversation:dani:analyst"
        
        # Verify TTL is 3600 (1 hour)
        assert call_args[0][1] == 3600
        
        # Verify message stored
        stored_data = json.loads(call_args[0][2])
        assert len(stored_data) == 1
        assert stored_data[0]["role"] == "user"
        assert stored_data[0]["content"] == "Hello Mary!"
    
    @pytest.mark.asyncio
    async def test_add_multiple_messages(self, manager, mock_redis):
        """Test adding multiple messages appends to history"""
        # Arrange
        existing = json.dumps([
            {"role": "user", "content": "First message"}
        ])
        mock_redis.get.return_value = existing
        
        # Act
        await manager.add_message("dani", "analyst", "assistant", "Mary's response")
        
        # Assert
        call_args = mock_redis.setex.call_args
        stored_data = json.loads(call_args[0][2])
        
        assert len(stored_data) == 2
        assert stored_data[0]["content"] == "First message"
        assert stored_data[1]["content"] == "Mary's response"
    
    @pytest.mark.asyncio
    async def test_trim_to_max_messages(self, manager, mock_redis):
        """Test trimming to last 50 messages"""
        # Arrange - Create 60 messages
        existing_messages = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(60)
        ]
        mock_redis.get.return_value = json.dumps(existing_messages)
        
        # Act
        await manager.add_message("dani", "analyst", "user", "New message")
        
        # Assert
        call_args = mock_redis.setex.call_args
        stored_data = json.loads(call_args[0][2])
        
        # Should be trimmed to 50 (max) + 1 new = 50 total (keeps last 50)
        assert len(stored_data) == 50
        assert stored_data[-1]["content"] == "New message"
        assert stored_data[0]["content"] == "Message 11"  # First 10 dropped
    
    @pytest.mark.asyncio
    async def test_get_history_empty(self, manager, mock_redis):
        """Test getting history when none exists"""
        # Arrange
        mock_redis.get.return_value = None
        
        # Act
        history = await manager.get_history("dani", "analyst")
        
        # Assert
        assert isinstance(history, ConversationHistory)
        assert history.user_id == "dani"
        assert history.agent_id == "analyst"
        assert len(history.messages) == 0
    
    @pytest.mark.asyncio
    async def test_get_messages_openai_format(self, manager, mock_redis):
        """Test getting messages in OpenAI format"""
        # Arrange
        existing = json.dumps([
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ])
        mock_redis.get.return_value = existing
        
        # Act
        messages = await manager.get_messages("dani", "analyst")
        
        # Assert
        assert isinstance(messages, list)
        assert len(messages) == 2
        assert messages[0] == {"role": "user", "content": "Hello"}
        assert messages[1] == {"role": "assistant", "content": "Hi there!"}
    
    @pytest.mark.asyncio
    async def test_clear_history(self, manager, mock_redis):
        """Test clearing conversation history"""
        # Act
        await manager.clear_history("dani", "analyst")
        
        # Assert
        mock_redis.delete.assert_called_once_with("conversation:dani:analyst")
    
    def test_make_key(self, manager):
        """Test Redis key format"""
        # Act
        key = manager._make_key("dani", "analyst")
        
        # Assert
        assert key == "conversation:dani:analyst"

