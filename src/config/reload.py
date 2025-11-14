"""
Configuration reload handler for hot-reloading components.

Story 7.5: Config Change Monitoring
Handles applying new configuration to running components (rate limiters, chains, providers).
"""

import logging
from threading import Lock
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ConfigReloadHandler:
    """Handles hot reload of configuration to running components."""

    def __init__(self):
        """Initialize the reload handler."""
        self._lock = Lock()
        self._rate_limiters: Dict[str, Any] = {}
        self._orchestrator: Any = None
        self._provider_factory: Any = None

    def register_rate_limiters(self, rate_limiters: Dict[str, Any]):
        """
        Register rate limiters for hot reload.

        Args:
            rate_limiters: Dictionary mapping provider names to RateLimiter instances
        """
        with self._lock:
            self._rate_limiters = rate_limiters
            logger.debug(f"Registered {len(rate_limiters)} rate limiters for reload")

    def register_orchestrator(self, orchestrator: Any):
        """
        Register orchestrator for agent chain updates.

        Args:
            orchestrator: AgentOrchestrator instance
        """
        with self._lock:
            self._orchestrator = orchestrator
            logger.debug("Registered orchestrator for reload")

    def register_provider_factory(self, factory: Any):
        """
        Register provider factory for provider setting updates.

        Args:
            factory: ProviderFactory instance
        """
        with self._lock:
            self._provider_factory = factory
            logger.debug("Registered provider factory for reload")

    def reload(self, new_config: Dict[str, Any]):
        """
        Apply new configuration to all registered components.

        This method is thread-safe and will only apply valid configuration.

        Args:
            new_config: Dictionary with 'settings', 'rate_limits', 'agent_chains', 'providers'
        """
        with self._lock:
            logger.info("Applying new configuration to components...")

            updated_components = []

            # Update rate limiters
            if "rate_limits" in new_config:
                self._update_rate_limiters(new_config["rate_limits"])
                updated_components.append("rate_limiters")

            # Update agent chains
            if "agent_chains" in new_config and self._orchestrator:
                self._update_orchestrator(new_config["agent_chains"])
                updated_components.append("agent_chains")

            # Update providers
            if "providers" in new_config and self._provider_factory:
                self._update_providers(new_config["providers"])
                updated_components.append("providers")

            logger.info(
                f" Configuration applied to: {', '.join(updated_components)}"
            )

    def _update_rate_limiters(self, rate_limits_config):
        """
        Update rate limiter values.

        Args:
            rate_limits_config: RateLimitsConfig object with new limits
        """
        for provider_name, rate_limiter in self._rate_limiters.items():
            if hasattr(rate_limits_config, provider_name):
                limits = getattr(rate_limits_config, provider_name)

                # Get old values for logging
                old_rpm = (
                    getattr(rate_limiter, "rpm", "N/A")
                    if hasattr(rate_limiter, "rpm")
                    else "N/A"
                )
                new_rpm = limits.rpm

                # Update rate limiter
                # Note: This assumes RateLimiter has an update_limits method
                # Actual implementation depends on the RateLimiter API from Epic 2
                if hasattr(rate_limiter, "update_limits"):
                    rate_limiter.update_limits(
                        rpm=limits.rpm,
                        burst=limits.burst,
                        tokens_per_minute=limits.tokens_per_minute,
                    )
                    logger.info(
                        f"  {provider_name}: {old_rpm}  {new_rpm} rpm, "
                        f"burst={limits.burst}, tokens={limits.tokens_per_minute}"
                    )
                else:
                    logger.warning(
                        f"  {provider_name}: RateLimiter does not support update_limits()"
                    )

    def _update_orchestrator(self, agent_chains_config):
        """
        Update agent chains in orchestrator.

        Args:
            agent_chains_config: AgentChainsConfig object with new chains
        """
        # Note: This assumes Orchestrator has an update_chains method
        # Actual implementation depends on the Orchestrator API from Epic 1
        if hasattr(self._orchestrator, "update_chains"):
            self._orchestrator.update_chains(agent_chains_config)
            logger.info("  Agent chains updated in orchestrator")
        else:
            logger.warning("  Orchestrator does not support update_chains()")

    def _update_providers(self, providers_config):
        """
        Update provider settings in factory.

        Args:
            providers_config: ProvidersConfig object with new provider settings
        """
        # Note: This assumes ProviderFactory has an update_providers method
        # Actual implementation depends on the ProviderFactory API from Epic 3
        if hasattr(self._provider_factory, "update_providers"):
            self._provider_factory.update_providers(providers_config)
            logger.info("  Provider settings updated in factory")
        else:
            logger.warning("  ProviderFactory does not support update_providers()")

