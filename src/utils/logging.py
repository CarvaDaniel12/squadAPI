"""
Structured JSON Logging

Implements JSON-formatted logging for easy parsing and analysis.
Supports request tracing via context variables.
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from contextvars import ContextVar


# Context variables for request tracing
request_id_ctx: ContextVar[str] = ContextVar('request_id', default='')
agent_id_ctx: ContextVar[str] = ContextVar('agent_id', default='')
provider_ctx: ContextVar[str] = ContextVar('provider', default='')


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter

    Formats log records as JSON objects for easy parsing and analysis.
    Includes context variables (request_id, agent, provider) automatically.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add context variables (if set)
        request_id = request_id_ctx.get()
        if request_id:
            log_data["request_id"] = request_id

        agent_id = agent_id_ctx.get()
        if agent_id:
            log_data["agent"] = agent_id

        provider = provider_ctx.get()
        if provider:
            log_data["provider"] = provider

        # Add extra fields from record
        extra_fields = [
            'status', 'latency_ms', 'tokens_in', 'tokens_out',
            'error_type', 'fallback_provider', 'tier'
        ]

        for field in extra_fields:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


def setup_json_logging(
    log_file: Optional[str] = None,
    log_level: str = "INFO",
    console_output: bool = True
) -> logging.Logger:
    """
    Setup JSON logging for the application

    Args:
        log_file: Path to log file (optional, uses ./logs/squad-api.log if None)
        log_level: Logging level (DEBUG, INFO, WARN, ERROR)
        console_output: Whether to also log to console

    Returns:
        Configured logger
    """
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # JSON formatter
    json_formatter = JSONFormatter()

    # File handler (JSON format) with rotation
    if log_file:
        from pathlib import Path
        from logging.handlers import TimedRotatingFileHandler

        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Use TimedRotatingFileHandler for daily rotation with 30-day retention
        file_handler = TimedRotatingFileHandler(
            log_file,
            when='midnight',      # Rotate at midnight
            interval=1,           # Every 1 day
            backupCount=30,       # Keep 30 days of logs
            encoding='utf-8'
        )
        file_handler.setFormatter(json_formatter)
        logger.addHandler(file_handler)

    # Console handler (optional, also JSON)
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(json_formatter)
        logger.addHandler(console_handler)

    return logger


def set_request_context(request_id: str, agent: str, provider: str):
    """
    Set request context for logging

    Args:
        request_id: Request ID
        agent: Agent ID
        provider: Provider name
    """
    request_id_ctx.set(request_id)
    agent_id_ctx.set(agent)
    provider_ctx.set(provider)


def clear_request_context():
    """Clear request context"""
    request_id_ctx.set('')
    agent_id_ctx.set('')
    provider_ctx.set('')


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **extra_fields
):
    """
    Log message with extra fields

    Args:
        logger: Logger instance
        level: Log level ('debug', 'info', 'warning', 'error')
        message: Log message
        **extra_fields: Additional fields to include in log
    """
    log_func = getattr(logger, level.lower())
    log_func(message, extra=extra_fields)




