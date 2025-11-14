"""Alerting system for SQUAD API

This module handles external alerting integrations:
- Slack webhooks for critical events
- Email alerts (future)
- PagerDuty integration (future)
"""

from .slack import (
    send_throttle_alert,
    send_latency_alert,
    send_health_alert,
    send_alert,
    LATENCY_THRESHOLDS
)

__all__ = [
    'send_throttle_alert',
    'send_latency_alert',
    'send_health_alert',
    'send_alert',
    'LATENCY_THRESHOLDS'
]
