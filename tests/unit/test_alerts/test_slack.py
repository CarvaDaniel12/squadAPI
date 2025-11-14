"""Unit tests for Slack alerts module

Tests:
- send_alert() success case
- send_alert() timeout handling
- send_alert() HTTP error handling
- Alert throttling (cooldown logic)
- Integration with auto-throttler context
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientTimeout, ClientError

from src.alerts.slack import (
    send_alert,
    send_throttle_alert,
    send_latency_alert,
    send_health_alert,
    _should_throttle_alert,
    reset_cooldowns,
    ALERT_COOLDOWN_SECONDS,
    LATENCY_ALERT_COOLDOWN_SECONDS,
    HEALTH_ALERT_COOLDOWN_SECONDS,
    LATENCY_THRESHOLDS
)


@pytest.fixture(autouse=True)
def reset_alert_state():
    """Reset cooldown state before each test"""
    reset_cooldowns()
    yield
    reset_cooldowns()


@pytest.mark.asyncio
async def test_send_alert_success():
    """Test successful Slack alert delivery"""
    webhook_url = "https://hooks.slack.com/services/TEST/WEBHOOK"
    message = " Test Alert"

    # Mock aiohttp session
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = None

    mock_session = AsyncMock()
    mock_session.post.return_value = mock_response
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    with patch('aiohttp.ClientSession', return_value=mock_session):
        await send_alert(webhook_url, message)

    # Verify POST called with correct params
    mock_session.post.assert_called_once()
    call_args = mock_session.post.call_args
    assert call_args[0][0] == webhook_url
    assert call_args[1]['json'] == {"text": message}
    assert 'timeout' in call_args[1]


@pytest.mark.asyncio
async def test_send_alert_http_error():
    """Test Slack alert with HTTP error response"""
    webhook_url = "https://hooks.slack.com/services/TEST/WEBHOOK"
    message = " Test Alert"

    # Mock HTTP 500 response
    mock_response = AsyncMock()
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value="Internal Server Error")
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = None

    mock_session = AsyncMock()
    mock_session.post.return_value = mock_response
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    with patch('aiohttp.ClientSession', return_value=mock_session):
        # Should not raise exception
        await send_alert(webhook_url, message)

    # Error logged but no exception raised
    mock_session.post.assert_called_once()


@pytest.mark.asyncio
async def test_send_alert_timeout():
    """Test Slack alert timeout handling"""
    webhook_url = "https://hooks.slack.com/services/TEST/WEBHOOK"
    message = " Test Alert"

    # Mock timeout exception
    mock_session = AsyncMock()
    mock_session.post.side_effect = asyncio.TimeoutError()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    with patch('aiohttp.ClientSession', return_value=mock_session):
        # Should not raise exception
        await send_alert(webhook_url, message)

    # Timeout logged but no exception raised
    mock_session.post.assert_called_once()


@pytest.mark.asyncio
async def test_send_alert_network_error():
    """Test Slack alert with network error"""
    webhook_url = "https://hooks.slack.com/services/TEST/WEBHOOK"
    message = " Test Alert"

    # Mock network exception
    mock_session = AsyncMock()
    mock_session.post.side_effect = ClientError("Connection refused")
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    with patch('aiohttp.ClientSession', return_value=mock_session):
        # Should not raise exception
        await send_alert(webhook_url, message)

    # Error logged but no exception raised
    mock_session.post.assert_called_once()


@pytest.mark.asyncio
async def test_send_throttle_alert_first_time():
    """Test throttle alert sent on first occurrence"""
    webhook_url = "https://hooks.slack.com/services/TEST/WEBHOOK"

    # Mock successful send_alert
    with patch('src.alerts.slack.send_alert', new_callable=AsyncMock) as mock_send:
        await send_throttle_alert(
            provider="Groq",
            error_count=7,
            old_rpm=12,
            new_rpm=9,
            webhook_url=webhook_url
        )

    # Alert should be sent
    mock_send.assert_called_once()
    call_args = mock_send.call_args
    assert call_args[0][0] == webhook_url
    message = call_args[0][1]
    assert "Groq" in message
    assert "7" in message
    assert "12" in message
    assert "9" in message


@pytest.mark.asyncio
async def test_alert_throttling_cooldown():
    """Test alert throttling prevents spam"""
    webhook_url = "https://hooks.slack.com/services/TEST/WEBHOOK"

    with patch('src.alerts.slack.send_alert', new_callable=AsyncMock) as mock_send:
        # First alert - should send
        await send_throttle_alert(
            provider="Groq",
            error_count=5,
            old_rpm=12,
            new_rpm=10,
            webhook_url=webhook_url
        )
        assert mock_send.call_count == 1

        # Second alert immediately after - should skip (cooldown)
        await send_throttle_alert(
            provider="Groq",
            error_count=3,
            old_rpm=10,
            new_rpm=8,
            webhook_url=webhook_url
        )
        assert mock_send.call_count == 1  # Still 1 (not called again)

        # Different provider - should send
        await send_throttle_alert(
            provider="Cerebras",
            error_count=4,
            old_rpm=20,
            new_rpm=15,
            webhook_url=webhook_url
        )
        assert mock_send.call_count == 2  # Different provider


def test_should_throttle_alert_logic():
    """Test cooldown logic directly"""
    provider = "TestProvider"

    # First time - should not throttle
    assert _should_throttle_alert(provider) is False

    # Manually set last alert time
    from src.alerts.slack import _last_alert_times
    _last_alert_times[provider] = time.time()

    # Immediately after - should throttle
    assert _should_throttle_alert(provider) is True

    # Simulate cooldown expiry
    _last_alert_times[provider] = time.time() - (ALERT_COOLDOWN_SECONDS + 1)
    assert _should_throttle_alert(provider) is False


@pytest.mark.asyncio
async def test_send_throttle_alert_message_format():
    """Test throttle alert message formatting"""
    webhook_url = "https://hooks.slack.com/services/TEST/WEBHOOK"

    with patch('src.alerts.slack.send_alert', new_callable=AsyncMock) as mock_send:
        await send_throttle_alert(
            provider="Groq",
            error_count=10,
            old_rpm=15,
            new_rpm=12,
            webhook_url=webhook_url
        )

    # Verify message format
    message = mock_send.call_args[0][1]
    assert "" in message  # Warning emoji
    assert "Auto-Throttling Ativado" in message
    assert "Groq" in message  # Provider name
    assert "429 Errors: 10" in message or "429 Errors:* 10" in message  # Count
    assert "15" in message and "12" in message  # RPM values
    assert "Time:" in message
    assert "UTC" in message
@pytest.mark.asyncio
async def test_send_alert_empty_webhook():
    """Test send_alert with empty webhook URL"""
    # Should not crash, just log warning
    await send_alert(webhook_url="", message="Test")
    await send_alert(webhook_url=None, message="Test")
    # No exception raised


@pytest.mark.asyncio
async def test_send_latency_alert():
    """Test latency degradation alert"""
    webhook_url = "https://hooks.slack.com/services/TEST/WEBHOOK"

    with patch('src.alerts.slack.send_alert', new_callable=AsyncMock) as mock_send:
        await send_latency_alert(
            provider="Groq",
            avg_latency=3.2,
            p95_latency=4.8,
            sample_size=45,
            threshold=2.0,
            webhook_url=webhook_url
        )

    # Alert should be sent
    mock_send.assert_called_once()
    call_args = mock_send.call_args
    assert call_args[0][0] == webhook_url
    message = call_args[0][1]

    # Verify message format
    assert "" in message or "Latncia" in message
    assert "Groq" in message
    assert "3.2" in message or "3.20" in message  # avg latency
    assert "4.8" in message or "4.80" in message  # P95
    assert "45" in message  # sample size
    assert "2.0" in message or "2s" in message or "<2" in message  # threshold


@pytest.mark.asyncio
async def test_send_health_alert():
    """Test provider health alert"""
    webhook_url = "https://hooks.slack.com/services/TEST/WEBHOOK"

    with patch('src.alerts.slack.send_alert', new_callable=AsyncMock) as mock_send:
        await send_health_alert(
            provider="Cerebras",
            error_type="Connection timeout",
            fallback_provider="Groq",
            webhook_url=webhook_url
        )

    # Alert should be sent
    mock_send.assert_called_once()
    call_args = mock_send.call_args
    assert call_args[0][0] == webhook_url
    message = call_args[0][1]

    # Verify message format
    assert "" in message or "Provider Unreachable" in message
    assert "Cerebras" in message
    assert "Connection timeout" in message
    assert "Groq" in message  # fallback


@pytest.mark.asyncio
async def test_alert_type_cooldown():
    """Test per-type alert throttling"""
    webhook_url = "https://hooks.slack.com/services/TEST/WEBHOOK"

    with patch('src.alerts.slack.send_alert', new_callable=AsyncMock) as mock_send:
        # Send throttle alert for Groq
        await send_throttle_alert(
            provider="Groq",
            error_count=5,
            old_rpm=12,
            new_rpm=10,
            webhook_url=webhook_url
        )
        assert mock_send.call_count == 1

        # Send latency alert for Groq - should work (different type)
        await send_latency_alert(
            provider="Groq",
            avg_latency=3.0,
            p95_latency=4.0,
            sample_size=20,
            threshold=2.0,
            webhook_url=webhook_url
        )
        assert mock_send.call_count == 2  # Both sent

        # Send health alert for Groq - should work (different type)
        await send_health_alert(
            provider="Groq",
            error_type="Timeout",
            fallback_provider="Cerebras",
            webhook_url=webhook_url
        )
        assert mock_send.call_count == 3  # All three sent

        # Send another throttle alert - should skip (cooldown)
        await send_throttle_alert(
            provider="Groq",
            error_count=3,
            old_rpm=10,
            new_rpm=8,
            webhook_url=webhook_url
        )
        assert mock_send.call_count == 3  # Still 3 (throttle blocked)


def test_latency_threshold_tiers():
    """Test latency threshold configuration"""
    # Fast providers
    assert LATENCY_THRESHOLDS["Groq"] == 2.0
    assert LATENCY_THRESHOLDS["Cerebras"] == 2.0

    # Standard providers
    assert LATENCY_THRESHOLDS["Gemini"] == 5.0
    assert LATENCY_THRESHOLDS["OpenRouter"] == 5.0


def test_alert_cooldown_durations():
    """Test different cooldown durations per alert type"""
    # Throttle alerts: 5 minutes
    assert ALERT_COOLDOWN_SECONDS == 300

    # Latency alerts: 15 minutes
    assert LATENCY_ALERT_COOLDOWN_SECONDS == 900

    # Health alerts: 15 minutes
    assert HEALTH_ALERT_COOLDOWN_SECONDS == 900

