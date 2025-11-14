"""
Unit tests for configuration reload handler.

Story 7.5: Config Change Monitoring
Tests ConfigReloadHandler class for hot-reloading components.
"""

import threading

import pytest

from src.config.reload import ConfigReloadHandler


class TestConfigReloadHandler:
    """Test suite for ConfigReloadHandler."""

    def test_registers_rate_limiters(self):
        """Test that handler can register rate limiters."""
        handler = ConfigReloadHandler()

        mock_limiters = {
            "groq": "limiter1",
            "cerebras": "limiter2",
        }

        handler.register_rate_limiters(mock_limiters)

        assert handler._rate_limiters == mock_limiters

    def test_registers_orchestrator(self):
        """Test that handler can register orchestrator."""
        handler = ConfigReloadHandler()

        mock_orchestrator = "test_orchestrator"
        handler.register_orchestrator(mock_orchestrator)

        assert handler._orchestrator == mock_orchestrator

    def test_registers_provider_factory(self):
        """Test that handler can register provider factory."""
        handler = ConfigReloadHandler()

        mock_factory = "test_factory"
        handler.register_provider_factory(mock_factory)

        assert handler._provider_factory == mock_factory

    def test_reload_updates_rate_limiters(self):
        """Test that reload handler updates rate limiters with new values."""

        # Mock rate limiter
        class MockRateLimiter:
            def __init__(self):
                self.rpm = 30
                self.burst = 30
                self.tokens_per_minute = 100000
                self.updated = False

            def update_limits(self, rpm, burst, tokens_per_minute):
                self.rpm = rpm
                self.burst = burst
                self.tokens_per_minute = tokens_per_minute
                self.updated = True

        limiter = MockRateLimiter()
        handler = ConfigReloadHandler()
        handler.register_rate_limiters({"groq": limiter})

        # Mock new config
        class RateLimitConfig:
            rpm = 60
            burst = 60
            tokens_per_minute = 200000

        class NewRateLimitsConfig:
            groq = RateLimitConfig()

        handler.reload({"rate_limits": NewRateLimitsConfig()})

        # Verify update
        assert limiter.updated is True
        assert limiter.rpm == 60
        assert limiter.burst == 60
        assert limiter.tokens_per_minute == 200000

    def test_reload_handles_limiters_without_update_method(self, caplog):
        """Test that reload handles rate limiters without update_limits method."""

        # Mock rate limiter without update_limits
        class MockRateLimiterNoUpdate:
            rpm = 30

        limiter = MockRateLimiterNoUpdate()
        handler = ConfigReloadHandler()
        handler.register_rate_limiters({"groq": limiter})

        class RateLimitConfig:
            rpm = 60
            burst = 60
            tokens_per_minute = 200000

        class NewRateLimitsConfig:
            groq = RateLimitConfig()

        handler.reload({"rate_limits": NewRateLimitsConfig()})

        # Should log warning
        assert "does not support update_limits" in caplog.text

    def test_reload_updates_orchestrator(self):
        """Test that reload handler updates orchestrator with new chains."""

        # Mock orchestrator
        class MockOrchestrator:
            def __init__(self):
                self.chains_updated = False
                self.new_chains = None

            def update_chains(self, chains):
                self.chains_updated = True
                self.new_chains = chains

        orchestrator = MockOrchestrator()
        handler = ConfigReloadHandler()
        handler.register_orchestrator(orchestrator)

        # Mock new config
        mock_chains = {"mary": {"primary": "groq", "fallbacks": ["cerebras"]}}
        handler.reload({"agent_chains": mock_chains})

        # Verify update
        assert orchestrator.chains_updated is True
        assert orchestrator.new_chains == mock_chains

    def test_reload_handles_orchestrator_without_update_method(self, caplog):
        """Test that reload handles orchestrator without update_chains method."""

        # Mock orchestrator without update_chains
        class MockOrchestratorNoUpdate:
            pass

        orchestrator = MockOrchestratorNoUpdate()
        handler = ConfigReloadHandler()
        handler.register_orchestrator(orchestrator)

        handler.reload({"agent_chains": {}})

        # Should log warning
        assert "does not support update_chains" in caplog.text

    def test_reload_updates_provider_factory(self):
        """Test that reload handler updates provider factory with new settings."""

        # Mock provider factory
        class MockProviderFactory:
            def __init__(self):
                self.providers_updated = False
                self.new_providers = None

            def update_providers(self, providers):
                self.providers_updated = True
                self.new_providers = providers

        factory = MockProviderFactory()
        handler = ConfigReloadHandler()
        handler.register_provider_factory(factory)

        # Mock new config
        mock_providers = {"groq": {"enabled": True, "model": "new-model"}}
        handler.reload({"providers": mock_providers})

        # Verify update
        assert factory.providers_updated is True
        assert factory.new_providers == mock_providers

    def test_reload_handles_factory_without_update_method(self, caplog):
        """Test that reload handles factory without update_providers method."""

        # Mock factory without update_providers
        class MockFactoryNoUpdate:
            pass

        factory = MockFactoryNoUpdate()
        handler = ConfigReloadHandler()
        handler.register_provider_factory(factory)

        handler.reload({"providers": {}})

        # Should log warning
        assert "does not support update_providers" in caplog.text

    def test_reload_is_thread_safe(self):
        """Test that reload handler is thread-safe with concurrent calls."""
        handler = ConfigReloadHandler()
        errors = []

        def reload_config():
            try:
                handler.reload({})
            except Exception as e:
                errors.append(e)

        # Run 20 concurrent reloads
        threads = [threading.Thread(target=reload_config) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have no errors
        assert len(errors) == 0

    def test_reload_updates_multiple_components(self):
        """Test that reload can update multiple components simultaneously."""

        # Mock all components
        class MockRateLimiter:
            def __init__(self):
                self.updated = False

            def update_limits(self, rpm, burst, tokens_per_minute):
                self.updated = True

        class MockOrchestrator:
            def __init__(self):
                self.updated = False

            def update_chains(self, chains):
                self.updated = True

        class MockProviderFactory:
            def __init__(self):
                self.updated = False

            def update_providers(self, providers):
                self.updated = True

        limiter = MockRateLimiter()
        orchestrator = MockOrchestrator()
        factory = MockProviderFactory()

        handler = ConfigReloadHandler()
        handler.register_rate_limiters({"groq": limiter})
        handler.register_orchestrator(orchestrator)
        handler.register_provider_factory(factory)

        # Mock configs
        class RateLimitConfig:
            rpm = 60
            burst = 60
            tokens_per_minute = 200000

        class NewRateLimitsConfig:
            groq = RateLimitConfig()

        handler.reload(
            {
                "rate_limits": NewRateLimitsConfig(),
                "agent_chains": {},
                "providers": {},
            }
        )

        # All should be updated
        assert limiter.updated is True
        assert orchestrator.updated is True
        assert factory.updated is True

    def test_reload_handles_empty_config(self):
        """Test that reload handles empty configuration gracefully."""
        handler = ConfigReloadHandler()

        # Should not raise error
        handler.reload({})

    def test_reload_logs_updated_components(self, caplog):
        """Test that reload logs which components were updated."""
        import logging
        caplog.set_level(logging.INFO)

        class MockRateLimiter:
            def update_limits(self, rpm, burst, tokens_per_minute):
                pass

        limiter = MockRateLimiter()
        handler = ConfigReloadHandler()
        handler.register_rate_limiters({"groq": limiter})

        class RateLimitConfig:
            rpm = 60
            burst = 60
            tokens_per_minute = 200000

        class NewRateLimitsConfig:
            groq = RateLimitConfig()

        handler.reload({"rate_limits": NewRateLimitsConfig()})

        # Should log what was updated
        assert "rate_limiters" in caplog.text or "Configuration applied" in caplog.text
