"""
Auto-Throttling System

Automatically adjusts rate limits based on 429 error patterns.
Prevents cascading failures and maintains optimal throughput.
"""

import time
import logging
import os
import asyncio
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..models.provider import ProviderRateLimitError
from ..alerts.slack import send_throttle_alert


logger = logging.getLogger(__name__)


@dataclass
class ThrottleState:
    """Current throttle state for a provider"""
    original_rpm: int
    current_rpm: int
    throttle_factor: float  # 1.0 = no throttle, 0.8 = 20% reduction
    spike_count: int
    last_spike_time: Optional[float]
    consecutive_stable_minutes: int
    is_throttled: bool
    last_error_time: Optional[float]
    last_stability_reset: Optional[float]


class AutoThrottler:
    """
    Automatically adjusts rate limits based on error patterns

    Features:
    - Spike detection (multiple 429s in short window)
    - Automatic RPM reduction (20% per spike)
    - Gradual restoration (10%/min when stable)
    - Per-provider throttling
    - Metrics and logging

    Algorithm:
    1. DETECT: Count 429 errors in 60s window
    2. THROTTLE: If >= 3 errors, reduce RPM by 20%
    3. RESTORE: If stable for 5 min, increase RPM by 10%
    4. REPEAT: Until back to original RPM

    Usage:
        throttler = AutoThrottler(providers)

        # On 429 error:
        throttler.record_error(provider_name, error)

        # Check if should throttle:
        if throttler.should_throttle(provider_name):
            new_rpm = throttler.get_throttled_rpm(provider_name)
            rate_limiter.update_rpm(provider_name, new_rpm)
    """

    def __init__(
        self,
        spike_threshold: int = 3,
        spike_window_seconds: int = 60,
        throttle_reduction: float = 0.20,  # 20% reduction
        restore_increment: float = 0.10,   # 10% increase
        stable_duration_minutes: int = 5
    ):
        """
        Initialize auto-throttler

        Args:
            spike_threshold: Number of 429s to trigger throttle
            spike_window_seconds: Time window for spike detection
            throttle_reduction: Factor to reduce RPM (0.20 = 20% reduction)
            restore_increment: Factor to increase RPM (0.10 = 10% increase)
            stable_duration_minutes: Minutes stable before restore
        """
        self.spike_threshold = spike_threshold
        self.spike_window = spike_window_seconds
        self.throttle_reduction = throttle_reduction
        self.restore_increment = restore_increment
        self.stable_duration = stable_duration_minutes

        # Provider states
        self.states: Dict[str, ThrottleState] = {}

        # Error tracking (provider  list of timestamps)
        self.error_history: Dict[str, List[float]] = {}

        # Statistics
        self.total_spikes = 0
        self.total_throttles = 0
        self.total_restores = 0

        # Slack configuration
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        self.slack_enabled = os.getenv('SLACK_ALERTS_ENABLED', 'false').lower() == 'true'

        logger.info(
            f"Auto-throttler initialized: "
            f"spike_threshold={spike_threshold}, "
            f"window={spike_window_seconds}s, "
            f"reduction={throttle_reduction*100}%, "
            f"slack_enabled={self.slack_enabled}"
        )

    def initialize_provider(self, provider_name: str, original_rpm: int):
        """
        Initialize throttle state for a provider

        Args:
            provider_name: Provider name
            original_rpm: Original RPM limit
        """
        if provider_name not in self.states:
            self.states[provider_name] = ThrottleState(
                original_rpm=original_rpm,
                current_rpm=original_rpm,
                throttle_factor=1.0,
                spike_count=0,
                last_spike_time=None,
                consecutive_stable_minutes=0,
                is_throttled=False,
                last_error_time=None,
                last_stability_reset=time.time()
            )
            self.error_history[provider_name] = []

            logger.debug(
                f"Initialized throttle state for '{provider_name}': "
                f"rpm={original_rpm}"
            )

    def record_error(self, provider_name: str, error: ProviderRateLimitError):
        """
        Record a 429 rate limit error

        Args:
            provider_name: Provider that returned 429
            error: The rate limit error
        """
        now = time.time()

        # Ensure provider is initialized
        if provider_name not in self.error_history:
            logger.warning(
                f"Provider '{provider_name}' not initialized, "
                f"cannot record error"
            )
            return

        # Add error timestamp
        self.error_history[provider_name].append(now)
        state = self.states.get(provider_name)
        if state:
            state.last_error_time = now
            state.consecutive_stable_minutes = 0

        # Cleanup old errors (outside window)
        cutoff = now - self.spike_window
        self.error_history[provider_name] = [
            ts for ts in self.error_history[provider_name]
            if ts > cutoff
        ]

        # Check for spike
        error_count = len(self.error_history[provider_name])

        logger.warning(
            f"429 error from '{provider_name}': "
            f"{error_count} errors in last {self.spike_window}s"
        )

        if error_count >= self.spike_threshold:
            self._trigger_spike(provider_name, error_count)

    def _trigger_spike(self, provider_name: str, error_count: int):
        """
        Trigger spike throttling

        Args:
            provider_name: Provider experiencing spike
            error_count: Number of errors in window
        """
        state = self.states[provider_name]
        now = time.time()

        # Check if already recently throttled (avoid over-throttling)
        if state.last_spike_time and (now - state.last_spike_time) < 30:
            logger.debug(
                f"Spike throttle skipped for '{provider_name}' "
                f"(recently throttled {int(now - state.last_spike_time)}s ago)"
            )
            return

        # Calculate new throttled RPM
        new_factor = state.throttle_factor * (1 - self.throttle_reduction)
        new_factor = max(0.2, new_factor)  # Never throttle below 20% of original

        old_rpm = state.current_rpm
        new_rpm = int(state.original_rpm * new_factor)

        # Update state
        state.throttle_factor = new_factor
        state.current_rpm = new_rpm
        state.spike_count += 1
        state.last_spike_time = now
        state.consecutive_stable_minutes = 0
        state.is_throttled = new_rpm < state.original_rpm
        state.last_stability_reset = now
        state.last_error_time = None

        self.total_spikes += 1
        self.total_throttles += 1

        logger.warning(
            f" THROTTLE: '{provider_name}' reduced RPM: "
            f"{old_rpm}  {new_rpm} "
            f"(factor: {new_factor:.2f}, spike #{state.spike_count})"
        )

        # Send Slack alert (fire-and-forget, non-blocking)
        if self.slack_enabled and self.slack_webhook:
            try:
                asyncio.create_task(send_throttle_alert(
                    provider=provider_name,
                    error_count=error_count,
                    old_rpm=old_rpm,
                    new_rpm=new_rpm,
                    webhook_url=self.slack_webhook
                ))
                logger.debug(f"Slack throttle alert triggered for '{provider_name}'")
            except Exception as e:
                # Never crash rate limiting due to alert failure
                logger.error(f"Failed to send Slack alert: {e}")

    def check_restore(self, provider_name: str) -> bool:
        """
        Check if provider should have RPM restored

        Should be called periodically (e.g., every minute).

        Args:
            provider_name: Provider to check

        Returns:
            True if RPM was restored
        """
        if provider_name not in self.states:
            return False

        state = self.states[provider_name]

        # Only restore if throttled
        if not state.is_throttled:
            return False

        # Check if any errors since last stability reset
        if state.last_error_time and state.last_stability_reset and state.last_error_time > state.last_stability_reset:
            state.consecutive_stable_minutes = 0
            return False

        # Increment stable counter
        state.consecutive_stable_minutes += 1

        # Check if reached stable duration
        if state.consecutive_stable_minutes < self.stable_duration:
            logger.debug(
                f"'{provider_name}' stable for "
                f"{state.consecutive_stable_minutes}/{self.stable_duration} minutes"
            )
            return False

        # Restore RPM
        return self._restore_rpm(provider_name)

    def _restore_rpm(self, provider_name: str) -> bool:
        """
        Restore RPM for a provider

        Args:
            provider_name: Provider to restore

        Returns:
            True if restored
        """
        state = self.states[provider_name]

        # Calculate new RPM (increase by restore_increment)
        new_factor = state.throttle_factor * (1 + self.restore_increment)
        new_factor = min(1.0, new_factor)  # Cap at 100%

        old_rpm = state.current_rpm
        new_rpm = int(state.original_rpm * new_factor)

        # Update state
        state.throttle_factor = new_factor
        state.current_rpm = new_rpm
        state.consecutive_stable_minutes = 0
        state.is_throttled = new_rpm < state.original_rpm

        self.total_restores += 1

        # Reset stability tracking after each restore step
        state.last_stability_reset = time.time()
        state.last_error_time = None

        if new_rpm >= state.original_rpm:
            # Fully restored
            logger.info(
                f" RESTORE COMPLETE: '{provider_name}' back to "
                f"original RPM: {new_rpm}"
            )
        else:
            logger.info(
                f" RESTORE: '{provider_name}' increased RPM: "
                f"{old_rpm}  {new_rpm} "
                f"(factor: {new_factor:.2f})"
            )

        return True

    def get_current_rpm(self, provider_name: str) -> int:
        """Get current throttled RPM for provider"""
        if provider_name not in self.states:
            return 0
        return self.states[provider_name].current_rpm

    def is_throttled(self, provider_name: str) -> bool:
        """Check if provider is currently throttled"""
        if provider_name not in self.states:
            return False
        return self.states[provider_name].is_throttled

    def get_stats(self) -> Dict:
        """Get throttling statistics"""
        throttled_providers = [
            name for name, state in self.states.items()
            if state.is_throttled
        ]

        return {
            'total_spikes': self.total_spikes,
            'total_throttles': self.total_throttles,
            'total_restores': self.total_restores,
            'throttled_providers': throttled_providers,
            'provider_states': {
                name: {
                    'original_rpm': state.original_rpm,
                    'current_rpm': state.current_rpm,
                    'throttle_factor': state.throttle_factor,
                    'is_throttled': state.is_throttled,
                    'spike_count': state.spike_count
                }
                for name, state in self.states.items()
            }
        }


