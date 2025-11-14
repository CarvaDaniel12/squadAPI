"""Slack webhook alerts for SQUAD API

Sends formatted alerts to Slack channels for critical events:
- Auto-throttling activation (429 spikes)
- Latency degradation (Story 6.6)
- Provider health issues (Story 6.6)

Features:
- Alert throttling (cooldown) to prevent spam
- Async/non-blocking webhook calls
- Graceful error handling
- Configurable via environment variables
"""

import aiohttp
import asyncio
import time
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Alert cooldown tracking (in-memory)
# Structure: {provider_name: last_alert_timestamp}
_last_alert_times: dict[str, float] = {}

# Configuration constants
ALERT_COOLDOWN_SECONDS = 300  # 5 minutes for throttle alerts
LATENCY_ALERT_COOLDOWN_SECONDS = 900  # 15 minutes for latency alerts
HEALTH_ALERT_COOLDOWN_SECONDS = 900   # 15 minutes for health alerts
SLACK_TIMEOUT_SECONDS = 5     # Max time to wait for Slack response

# Provider latency thresholds (seconds)
LATENCY_THRESHOLDS = {
    "Groq": 2.0,        # Fast provider
    "Cerebras": 2.0,    # Fast provider
    "Gemini": 5.0,      # Standard provider
    "OpenRouter": 5.0   # Standard provider
}


async def send_throttle_alert(
    provider: str,
    error_count: int,
    old_rpm: int,
    new_rpm: int,
    webhook_url: str
) -> None:
    """Send auto-throttling alert to Slack

    Triggered when AutoThrottler detects 429 spike and reduces RPM.
    Includes cooldown logic to prevent spam.

    Args:
        provider: Provider name (e.g., "Groq", "Cerebras")
        error_count: Number of 429 errors in detection window
        old_rpm: Previous RPM limit
        new_rpm: New (reduced) RPM limit
        webhook_url: Slack webhook URL

    Example:
        await send_throttle_alert(
            provider="Groq",
            error_count=7,
            old_rpm=12,
            new_rpm=9,
            webhook_url="https://hooks.slack.com/services/..."
        )

    Cooldown:
        Max 1 alert per provider per 5 minutes to avoid spam.
        Skipped alerts are logged for debugging.
    """
    # Check cooldown
    alert_key = f"{provider}:throttle"
    if _should_throttle_alert(alert_key, ALERT_COOLDOWN_SECONDS):
        logger.debug(
            f"Skipping throttle alert for '{provider}' - "
            f"cooldown active ({ALERT_COOLDOWN_SECONDS}s)"
        )
        return

    # Build formatted message
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    message = (
        f" *Auto-Throttling Ativado*\n"
        f"*Provider:* {provider}\n"
        f"*429 Errors:* {error_count} em ltimo minuto\n"
        f"*Action:* RPM reduzido de {old_rpm}  {new_rpm}\n"
        f"*Time:* {timestamp}"
    )

    # Send alert
    logger.info(f"Sending throttle alert for '{provider}': {error_count} 429s")
    await send_alert(webhook_url, message)

    # Update cooldown tracker
    _last_alert_times[alert_key] = time.time()


async def send_alert(webhook_url: str, message: str) -> None:
    """Generic Slack webhook sender

    Sends formatted message to Slack webhook URL.
    Non-blocking, with timeout and error handling.

    Args:
        webhook_url: Slack webhook URL (from app config)
        message: Text message to send (Markdown supported)

    Raises:
        No exceptions raised - failures are logged only

    Example:
        await send_alert(
            webhook_url="https://hooks.slack.com/services/...",
            message=" *Alert*\nSomething happened"
        )

    Error Handling:
        - HTTP errors: Logged, not raised
        - Timeouts: 5s max wait
        - Network errors: Logged, not raised

    Performance:
        - Async/non-blocking
        - No retry logic (fire-and-forget)
        - Does not block rate limiting
    """
    if not webhook_url:
        logger.warning("Slack webhook URL not configured - alert not sent")
        return

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json={"text": message},
                timeout=aiohttp.ClientTimeout(total=SLACK_TIMEOUT_SECONDS)
            ) as response:
                if response.status == 200:
                    logger.debug("Slack alert sent successfully")
                else:
                    body = await response.text()
                    logger.error(
                        f"Slack alert failed: HTTP {response.status}, "
                        f"body: {body}"
                    )
    except asyncio.TimeoutError:
        logger.error(
            f"Slack alert timeout after {SLACK_TIMEOUT_SECONDS}s - "
            "webhook unreachable"
        )
    except aiohttp.ClientError as e:
        logger.error(f"Slack alert network error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending Slack alert: {e}")


async def send_latency_alert(
    provider: str,
    avg_latency: float,
    p95_latency: float,
    sample_size: int,
    threshold: float,
    webhook_url: str
) -> None:
    """Send latency degradation alert to Slack

    Triggered when average latency exceeds threshold for a provider.
    Uses 15-minute cooldown to prevent spam.

    Args:
        provider: Provider name (e.g., "Groq", "Cerebras")
        avg_latency: Average latency in seconds
        p95_latency: 95th percentile latency in seconds
        sample_size: Number of requests in measurement window
        threshold: Latency threshold that was exceeded
        webhook_url: Slack webhook URL

    Example:
        await send_latency_alert(
            provider="Groq",
            avg_latency=3.2,
            p95_latency=4.8,
            sample_size=45,
            threshold=2.0,
            webhook_url="https://hooks.slack.com/services/..."
        )

    Cooldown:
        Max 1 latency alert per provider per 15 minutes.
    """
    # Check cooldown (per provider, per type)
    alert_key = f"{provider}:latency"
    if _should_throttle_alert(alert_key, LATENCY_ALERT_COOLDOWN_SECONDS):
        logger.debug(
            f"Skipping latency alert for '{provider}' - "
            f"cooldown active ({LATENCY_ALERT_COOLDOWN_SECONDS}s)"
        )
        return

    # Build formatted message
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    message = (
        f" *Latncia Alta Detectada*\n"
        f"*Provider:* {provider}\n"
        f"*Avg Latency:* {avg_latency:.2f}s (esperado: <{threshold}s)\n"
        f"*P95 Latency:* {p95_latency:.2f}s\n"
        f"*Requests:* {sample_size} em ltimos 5min\n"
        f"*Time:* {timestamp}"
    )

    # Send alert
    logger.info(f"Sending latency alert for '{provider}': {avg_latency:.2f}s")
    await send_alert(webhook_url, message)

    # Update cooldown tracker
    _last_alert_times[alert_key] = time.time()


async def send_health_alert(
    provider: str,
    error_type: str,
    fallback_provider: str,
    webhook_url: str
) -> None:
    """Send provider health alert to Slack

    Triggered when a provider becomes unreachable and fallback is activated.
    Uses 15-minute cooldown to prevent spam.

    Args:
        provider: Provider that failed
        error_type: Type of error encountered
        fallback_provider: Provider used as fallback
        webhook_url: Slack webhook URL

    Example:
        await send_health_alert(
            provider="Cerebras",
            error_type="Connection timeout",
            fallback_provider="Groq",
            webhook_url="https://hooks.slack.com/services/..."
        )

    Cooldown:
        Max 1 health alert per provider per 15 minutes.
    """
    # Check cooldown (per provider, per type)
    alert_key = f"{provider}:health"
    if _should_throttle_alert(alert_key, HEALTH_ALERT_COOLDOWN_SECONDS):
        logger.debug(
            f"Skipping health alert for '{provider}' - "
            f"cooldown active ({HEALTH_ALERT_COOLDOWN_SECONDS}s)"
        )
        return

    # Build formatted message
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    message = (
        f" *Provider Unreachable*\n"
        f"*Provider:* {provider}\n"
        f"*Error:* {error_type}\n"
        f"*Fallback:* {fallback_provider}\n"
        f"*Time:* {timestamp}"
    )

    # Send alert
    logger.warning(f"Sending health alert for '{provider}': {error_type}")
    await send_alert(webhook_url, message)

    # Update cooldown tracker
    _last_alert_times[alert_key] = time.time()


def _should_throttle_alert(alert_key: str, cooldown_seconds: int = ALERT_COOLDOWN_SECONDS) -> bool:
    """Check if alert should be throttled (cooldown active)

    Args:
        alert_key: Alert key (provider or "provider:type")
        cooldown_seconds: Cooldown duration in seconds

    Returns:
        True if alert should be skipped (cooldown active)
        False if alert should be sent

    Cooldown Logic:
        - Tracks last alert time per key
        - Configurable cooldown duration
        - First alert always sent (no history)
        - Supports per-type keys: "Groq:latency", "Groq:health"

    Example:
        if _should_throttle_alert("Groq:latency", 900):
            return  # Skip alert
    """
    if alert_key not in _last_alert_times:
        return False  # No history - send alert

    elapsed = time.time() - _last_alert_times[alert_key]
    return elapsed < cooldown_seconds


def reset_cooldowns() -> None:
    """Reset all alert cooldowns (for testing)

    Clears cooldown tracker. Used in unit tests to ensure
    clean state between test runs.
    """
    _last_alert_times.clear()

