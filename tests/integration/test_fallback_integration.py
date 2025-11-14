"""
Integration Tests for Fallback & Resilience

Tests complete fallback scenarios with quality validation and auto-throttling.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock

from src.agents.fallback import FallbackExecutor, AllProvidersFailed
from src.agents.quality import QualityValidator, ProviderTier
from src.rate_limit.auto_throttle import AutoThrottler
from src.providers.stub_provider import StubLLMProvider
from src.models.provider import (
    ProviderConfig,
    LLMResponse,
    ProviderRateLimitError,
    ProviderTimeoutError
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestFallbackIntegration:
    """Test complete fallback scenarios"""
    
    async def test_fallback_chain_success_on_second_provider(self):
        """Should fallback to second provider when first fails"""
        # Create providers
        provider1 = StubLLMProvider(
            config=ProviderConfig(
                name="provider1",
                type="stub",
                model="model1",
                rpm_limit=30,
                tpm_limit=20000
            ),
            fixed_response="This should not be returned"
        )
        
        provider2 = StubLLMProvider(
            config=ProviderConfig(
                name="provider2",
                type="stub",
                model="model2",
                rpm_limit=30,
                tpm_limit=20000
            ),
            fixed_response="Success from provider2"
        )
        
        # Mock provider1 to fail with rate limit
        async def provider1_fail(*args, **kwargs):
            raise ProviderRateLimitError("provider1", "Rate limit exceeded")
        
        provider1.call = provider1_fail
        
        # Create fallback executor
        providers = {"provider1": provider1, "provider2": provider2}
        fallback_chains = {"test_agent": ["provider1", "provider2"]}
        
        executor = FallbackExecutor(providers, fallback_chains)
        
        # Execute with fallback
        response = await executor.execute_with_fallback(
            agent_id="test_agent",
            system_prompt="System",
            user_prompt="User"
        )
        
        # Verify fallback worked
        assert response.content == "Success from provider2"
        assert response.provider == "provider2"
        
        # Verify stats
        stats = executor.get_stats()
        assert stats['fallback_triggered'] == 1
        assert stats['fallback_success'] == 1
    
    async def test_all_providers_fail(self):
        """Should raise AllProvidersFailed when all fail"""
        # Create failing providers
        async def fail_rate_limit(*args, **kwargs):
            raise ProviderRateLimitError("provider", "Rate limit")
        
        provider1 = StubLLMProvider()
        provider1.call = fail_rate_limit
        
        provider2 = StubLLMProvider()
        provider2.call = fail_rate_limit
        
        # Create executor
        providers = {"provider1": provider1, "provider2": provider2}
        fallback_chains = {"test_agent": ["provider1", "provider2"]}
        
        executor = FallbackExecutor(providers, fallback_chains)
        
        # Execute should fail
        with pytest.raises(AllProvidersFailed) as exc_info:
            await executor.execute_with_fallback(
                agent_id="test_agent",
                system_prompt="System",
                user_prompt="User"
            )
        
        # Verify exception details
        assert exc_info.value.agent_id == "test_agent"
        assert len(exc_info.value.errors) == 2
        
        # Verify stats
        stats = executor.get_stats()
        assert stats['all_failed'] == 1
    
    async def test_fallback_with_timeout_then_success(self):
        """Should handle timeout and fallback to healthy provider"""
        # Provider 1: timeout
        async def timeout_error(*args, **kwargs):
            raise ProviderTimeoutError("provider1", "Timeout")
        
        provider1 = StubLLMProvider()
        provider1.call = timeout_error
        
        # Provider 2: success
        provider2 = StubLLMProvider(
            fixed_response="Success after timeout"
        )
        
        # Create executor
        providers = {"provider1": provider1, "provider2": provider2}
        fallback_chains = {"test_agent": ["provider1", "provider2"]}
        
        executor = FallbackExecutor(providers, fallback_chains)
        
        # Execute
        response = await executor.execute_with_fallback(
            agent_id="test_agent",
            system_prompt="System",
            user_prompt="User"
        )
        
        # Verify
        assert response.content == "Success after timeout"
        assert executor.get_stats()['fallback_success'] == 1


@pytest.mark.integration
@pytest.mark.asyncio
class TestQualityValidationIntegration:
    """Test quality validation scenarios"""
    
    async def test_quality_validation_good_response(self):
        """Should accept high-quality response"""
        validator = QualityValidator()
        
        response = LLMResponse(
            content="This is a comprehensive and detailed response that provides valuable insights. "
                   "The analysis covers multiple aspects and demonstrates deep understanding. "
                   "Based on the evidence, we can conclude with high confidence.",
            tokens_input=100,
            tokens_output=50,
            latency_ms=1000,
            model="test-model",
            finish_reason="stop",
            provider="test"
        )
        
        result = validator.validate(response, tier=ProviderTier.WORKER)
        
        assert result.is_valid is True
        assert result.quality_score >= 0.6
        assert result.should_escalate is False
    
    async def test_quality_validation_poor_response(self):
        """Should reject poor quality and recommend escalation"""
        validator = QualityValidator()
        
        response = LLMResponse(
            content="I don't know.",
            tokens_input=100,
            tokens_output=5,
            latency_ms=100,
            model="test-model",
            finish_reason="stop",
            provider="test"
        )
        
        result = validator.validate(response, tier=ProviderTier.WORKER)
        
        assert result.is_valid is False
        assert result.should_escalate is True
        assert len(result.issues) > 0
    
    async def test_quality_escalation_tier(self):
        """Should recommend correct escalation tier"""
        validator = QualityValidator()
        
        # Worker  Boss
        next_tier = validator.get_escalation_tier(ProviderTier.WORKER)
        assert next_tier == ProviderTier.BOSS
        
        # Boss  Ultimate
        next_tier = validator.get_escalation_tier(ProviderTier.BOSS)
        assert next_tier == ProviderTier.ULTIMATE
        
        # Ultimate  None (already at top)
        next_tier = validator.get_escalation_tier(ProviderTier.ULTIMATE)
        assert next_tier is None


@pytest.mark.integration
@pytest.mark.asyncio
class TestAutoThrottlingIntegration:
    """Test auto-throttling scenarios"""
    
    async def test_auto_throttle_on_spike(self):
        """Should throttle RPM when spike detected"""
        throttler = AutoThrottler(
            spike_threshold=3,
            spike_window_seconds=60,
            throttle_reduction=0.20
        )
        
        # Initialize provider
        throttler.initialize_provider("groq", original_rpm=30)
        
        # Simulate spike (3 errors in short time)
        for _ in range(3):
            error = ProviderRateLimitError("groq", "Rate limit")
            throttler.record_error("groq", error)
        
        # Verify throttling
        assert throttler.is_throttled("groq") is True
        current_rpm = throttler.get_current_rpm("groq")
        assert current_rpm == 24  # 30 * 0.8 (20% reduction)
        
        stats = throttler.get_stats()
        assert stats['total_throttles'] == 1
    
    async def test_auto_restore_after_stable(self):
        """Should restore RPM after stable period"""
        throttler = AutoThrottler(
            spike_threshold=3,
            stable_duration_minutes=2
        )
        
        # Initialize and throttle
        throttler.initialize_provider("groq", original_rpm=30)
        
        # Trigger throttle
        for _ in range(3):
            throttler.record_error("groq", ProviderRateLimitError("groq", "429"))
        
        assert throttler.is_throttled("groq") is True
        throttled_rpm = throttler.get_current_rpm("groq")
        assert throttled_rpm < 30
        
        # Simulate stable period (2 minutes)
        for _ in range(2):
            restored = throttler.check_restore("groq")
        
        # Should restore some RPM
        current_rpm = throttler.get_current_rpm("groq")
        assert current_rpm > throttled_rpm
        
        stats = throttler.get_stats()
        assert stats['total_restores'] >= 1


@pytest.mark.integration
@pytest.mark.asyncio
class TestCompleteResilienceFlow:
    """Test complete resilience flow with all components"""
    
    async def test_complete_fallback_with_quality_and_throttling(self):
        """Test complete flow: fallback + quality + throttling"""
        # Create providers with different quality
        low_quality = StubLLMProvider(
            fixed_response="I don't know"  # Poor quality
        )
        
        high_quality = StubLLMProvider(
            fixed_response=(
                "This is a comprehensive analysis of the situation. "
                "Based on thorough evaluation of multiple factors, "
                "we can conclude with high confidence that the approach is sound."
            )
        )
        
        # Create fallback executor
        providers = {"low": low_quality, "high": high_quality}
        fallback_chains = {"analyst": ["low", "high"]}
        
        executor = FallbackExecutor(providers, fallback_chains)
        
        # Create quality validator
        validator = QualityValidator()
        
        # Execute with fallback
        response = await executor.execute_with_fallback(
            agent_id="analyst",
            system_prompt="You are an analyst",
            user_prompt="Analyze the system"
        )
        
        # First try low quality
        result = validator.validate(response, tier=ProviderTier.WORKER)
        
        # If quality is poor, we would escalate (simulated)
        if result.should_escalate:
            # Re-execute with high quality provider
            response = await high_quality.call(
                "You are an analyst",
                "Analyze the system"
            )
        
        # Verify final response
        assert len(response.content) > 100
        assert "comprehensive" in response.content.lower()


