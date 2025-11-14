"""
Unit Tests for Quality Validator

Tests response quality validation and escalation logic.
"""

import pytest
from src.agents.quality import QualityValidator, ProviderTier, QualityIssue
from src.models.provider import LLMResponse


@pytest.mark.unit
class TestQualityValidator:
    """Test quality validation"""
    
    def test_validate_good_response(self):
        """Should validate high-quality response"""
        validator = QualityValidator()
        
        response = LLMResponse(
            content=(
                "This is a comprehensive and well-structured response. "
                "It provides detailed analysis with clear reasoning. "
                "The conclusions are well-supported by evidence."
            ),
            tokens_input=100,
            tokens_output=50,
            latency_ms=1000,
            model="test",
            finish_reason="stop",
            provider="test"
        )
        
        result = validator.validate(response, tier=ProviderTier.WORKER)
        
        assert result.is_valid is True
        assert result.quality_score >= 0.6
        assert result.should_escalate is False
    
    def test_validate_too_short(self):
        """Should detect too-short responses"""
        validator = QualityValidator(min_length_worker=50)
        
        response = LLMResponse(
            content="Short.",
            tokens_input=100,
            tokens_output=5,
            latency_ms=100,
            model="test",
            finish_reason="stop",
            provider="test"
        )
        
        result = validator.validate(response, tier=ProviderTier.WORKER)
        
        assert QualityIssue.TOO_SHORT in result.issues
        assert result.quality_score < 1.0
    
    def test_validate_error_marker(self):
        """Should detect error markers"""
        validator = QualityValidator()
        
        response = LLMResponse(
            content=(
                "I apologize, but I cannot help with this request. "
                "I don't have enough information to proceed."
            ),
            tokens_input=100,
            tokens_output=30,
            latency_ms=100,
            model="test",
            finish_reason="stop",
            provider="test"
        )
        
        result = validator.validate(response)
        
        assert QualityIssue.ERROR_MARKER in result.issues
        assert result.should_escalate is True
    
    def test_validate_low_confidence(self):
        """Should detect low confidence markers"""
        validator = QualityValidator()
        
        response = LLMResponse(
            content=(
                "I think maybe this could possibly be the answer, perhaps. "
                "I believe it might be correct, but I'm not sure. "
                "It could be something else entirely."
            ),
            tokens_input=100,
            tokens_output=40,
            latency_ms=100,
            model="test",
            finish_reason="stop",
            provider="test"
        )
        
        result = validator.validate(response)
        
        assert QualityIssue.LOW_CONFIDENCE in result.issues
    
    def test_validate_incomplete(self):
        """Should detect incomplete responses"""
        validator = QualityValidator()
        
        response = LLMResponse(
            content="This response was cut off in the middle of a sente",
            tokens_input=100,
            tokens_output=50,
            latency_ms=100,
            model="test",
            finish_reason="length",  # Truncated
            provider="test"
        )
        
        result = validator.validate(response)
        
        assert QualityIssue.INCOMPLETE in result.issues
    
    def test_validate_corrupted_json(self):
        """Should detect corrupted responses"""
        validator = QualityValidator()
        
        response = LLMResponse(
            content='{"result": "incomplete json structure',  # Missing closing brace
            tokens_input=100,
            tokens_output=20,
            latency_ms=100,
            model="test",
            finish_reason="stop",
            provider="test"
        )
        
        result = validator.validate(response)
        
        assert QualityIssue.CORRUPTED in result.issues
    
    def test_tier_specific_validation(self):
        """Should use different standards for different tiers"""
        validator = QualityValidator(min_length_worker=50, min_length_boss=200)
        
        # 100-char response
        response = LLMResponse(
            content="A" * 100,
            tokens_input=100,
            tokens_output=25,
            latency_ms=100,
            model="test",
            finish_reason="stop",
            provider="test"
        )
        
        # Should pass for WORKER (100 chars > 50 min)
        result_worker = validator.validate(response, tier=ProviderTier.WORKER)
        assert result_worker.is_valid is True
        
        # Should fail for BOSS (100 chars < 200 min)
        result_boss = validator.validate(response, tier=ProviderTier.BOSS)
        # Quality score will be reduced by 0.3 for too short (1.0 - 0.3 = 0.7)
        # So it's still valid (>= 0.6) but should_escalate might be True
        # Let's check both quality_score and TOO_SHORT issue
        assert QualityIssue.TOO_SHORT in result_boss.issues
        assert result_boss.quality_score < result_worker.quality_score
    
    def test_get_escalation_tier(self):
        """Should return correct next tier"""
        validator = QualityValidator()
        
        assert validator.get_escalation_tier(ProviderTier.WORKER) == ProviderTier.BOSS
        assert validator.get_escalation_tier(ProviderTier.BOSS) == ProviderTier.ULTIMATE
        assert validator.get_escalation_tier(ProviderTier.ULTIMATE) is None

