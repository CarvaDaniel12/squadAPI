"""
Request Validation Unit Tests
Tests Pydantic validation for AgentExecutionRequest model
"""

import pytest
from pydantic import ValidationError

from src.models.request import AgentExecutionRequest


class TestAgentExecutionRequestValidation:
    """Test Pydantic validation rules for AgentExecutionRequest"""

    def test_valid_request_minimal(self):
        """Test valid request with only required fields"""
        request = AgentExecutionRequest(prompt="Write a function")
        assert request.prompt == "Write a function"
        assert request.conversation_id is None
        assert request.metadata == {}

    def test_valid_request_full(self):
        """Test valid request with all fields"""
        request = AgentExecutionRequest(
            prompt="Write a function",
            conversation_id="test-123",
            metadata={"user": "john"},
            max_tokens=1000,
            temperature=0.7
        )
        assert request.prompt == "Write a function"
        assert request.conversation_id == "test-123"
        assert request.metadata == {"user": "john"}
        assert request.max_tokens == 1000
        assert request.temperature == 0.7

    def test_missing_prompt_raises_error(self):
        """Test that missing prompt raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            AgentExecutionRequest()

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("prompt",) for error in errors)

    def test_empty_prompt_raises_error(self):
        """Test that empty prompt raises validation error (min_length=1)"""
        with pytest.raises(ValidationError) as exc_info:
            AgentExecutionRequest(prompt="")

        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("prompt",) and "at least 1 character" in str(error["msg"])
            for error in errors
        )

    def test_prompt_too_long_raises_error(self):
        """Test that prompt exceeding max_length raises error"""
        with pytest.raises(ValidationError) as exc_info:
            AgentExecutionRequest(prompt="x" * 10001)  # max_length=10000

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("prompt",) for error in errors)

    def test_temperature_below_min_raises_error(self):
        """Test that temperature < 0.0 raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            AgentExecutionRequest(
                prompt="test",
                temperature=-0.1
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("temperature",) for error in errors)

    def test_temperature_above_max_raises_error(self):
        """Test that temperature > 2.0 raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            AgentExecutionRequest(
                prompt="test",
                temperature=2.1
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("temperature",) for error in errors)

    def test_temperature_valid_range(self):
        """Test that temperature in valid range works"""
        # Min boundary
        request_min = AgentExecutionRequest(prompt="test", temperature=0.0)
        assert request_min.temperature == 0.0

        # Max boundary
        request_max = AgentExecutionRequest(prompt="test", temperature=2.0)
        assert request_max.temperature == 2.0

        # Middle value
        request_mid = AgentExecutionRequest(prompt="test", temperature=0.7)
        assert request_mid.temperature == 0.7

    def test_max_tokens_negative_raises_error(self):
        """Test that negative max_tokens raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            AgentExecutionRequest(
                prompt="test",
                max_tokens=-1
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("max_tokens",) for error in errors)

    def test_max_tokens_above_limit_raises_error(self):
        """Test that max_tokens > 100000 raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            AgentExecutionRequest(
                prompt="test",
                max_tokens=100001
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("max_tokens",) for error in errors)

    def test_max_tokens_valid_range(self):
        """Test that max_tokens in valid range works"""
        # Min boundary
        request_min = AgentExecutionRequest(prompt="test", max_tokens=1)
        assert request_min.max_tokens == 1

        # Max boundary
        request_max = AgentExecutionRequest(prompt="test", max_tokens=100000)
        assert request_max.max_tokens == 100000

        # Common value
        request_common = AgentExecutionRequest(prompt="test", max_tokens=2000)
        assert request_common.max_tokens == 2000

    def test_metadata_optional(self):
        """Test that metadata is optional and defaults to empty dict"""
        request = AgentExecutionRequest(prompt="test")
        assert request.metadata == {}

    def test_metadata_custom_dict(self):
        """Test that metadata accepts custom dictionary"""
        custom_metadata = {
            "user_id": "john@example.com",
            "session": "abc123",
            "nested": {"key": "value"}
        }
        request = AgentExecutionRequest(
            prompt="test",
            metadata=custom_metadata
        )
        assert request.metadata == custom_metadata

    def test_conversation_id_optional(self):
        """Test that conversation_id is optional"""
        request = AgentExecutionRequest(prompt="test")
        assert request.conversation_id is None

    def test_conversation_id_string(self):
        """Test that conversation_id accepts string values"""
        request = AgentExecutionRequest(
            prompt="test",
            conversation_id="conv-12345"
        )
        assert request.conversation_id == "conv-12345"


# Test Summary
"""
Request Validation Unit Tests Coverage:

 Valid requests (2 tests)
   - Minimal (only prompt)
   - Full (all fields)

 Prompt validation (3 tests)
   - Missing prompt
   - Empty prompt (min_length)
   - Too long prompt (max_length)

 Temperature validation (3 tests)
   - Below min (< 0.0)
   - Above max (> 2.0)
   - Valid range (0.0 - 2.0)

 Max tokens validation (3 tests)
   - Negative value
   - Above limit (> 100000)
   - Valid range (1 - 100000)

 Optional fields (4 tests)
   - Metadata optional/custom
   - Conversation_id optional/string

Total: 15 unit tests for request validation
These are proper unit tests testing Pydantic validation rules
"""

