"""
Unit tests for Structured JSON Logging (Story 5.4)

Tests the JSON logging implementation in src/utils/logging.py
"""

import pytest
import logging
import json
import tempfile
import time
from pathlib import Path
from datetime import datetime

from src.utils.logging import (
    JSONFormatter,
    setup_json_logging,
    set_request_context,
    clear_request_context,
    log_with_context,
    request_id_ctx,
    agent_id_ctx,
    provider_ctx
)


class TestJSONFormatter:
    """Test JSON log formatter"""

    def test_basic_json_format(self):
        """Should format log record as valid JSON"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None
        )

        # Format the record
        output = formatter.format(record)

        # Should be valid JSON
        log_data = json.loads(output)

        # Verify required fields
        assert 'timestamp' in log_data
        assert 'level' in log_data
        assert 'logger' in log_data
        assert 'message' in log_data

        assert log_data['level'] == 'INFO'
        assert log_data['logger'] == 'test_logger'
        assert log_data['message'] == 'Test message'

    def test_context_variables_inclusion(self):
        """Should include context variables in log output"""
        formatter = JSONFormatter()

        # Set context
        set_request_context('req-123', 'analyst', 'groq')

        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Context test',
            args=(),
            exc_info=None
        )

        output = formatter.format(record)
        log_data = json.loads(output)

        # Verify context variables are included
        assert log_data['request_id'] == 'req-123'
        assert log_data['agent'] == 'analyst'
        assert log_data['provider'] == 'groq'

        # Cleanup
        clear_request_context()

    def test_extra_fields(self):
        """Should include extra fields from record"""
        formatter = JSONFormatter()

        record = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='test.py',
            lineno=1,
            msg='Error with extras',
            args=(),
            exc_info=None
        )

        # Add extra fields
        record.status = 'failure'
        record.latency_ms = 1500
        record.tokens_in = 2000
        record.tokens_out = 500
        record.error_type = 'timeout'

        output = formatter.format(record)
        log_data = json.loads(output)

        # Verify extra fields
        assert log_data['status'] == 'failure'
        assert log_data['latency_ms'] == 1500
        assert log_data['tokens_in'] == 2000
        assert log_data['tokens_out'] == 500
        assert log_data['error_type'] == 'timeout'

    def test_all_log_levels(self):
        """Should handle all log levels correctly"""
        formatter = JSONFormatter()

        levels = [
            (logging.DEBUG, 'DEBUG'),
            (logging.INFO, 'INFO'),
            (logging.WARNING, 'WARNING'),
            (logging.ERROR, 'ERROR'),
            (logging.CRITICAL, 'CRITICAL')
        ]

        for level_int, level_str in levels:
            record = logging.LogRecord(
                name='test',
                level=level_int,
                pathname='test.py',
                lineno=1,
                msg=f'{level_str} message',
                args=(),
                exc_info=None
            )

            output = formatter.format(record)
            log_data = json.loads(output)

            assert log_data['level'] == level_str
            assert log_data['message'] == f'{level_str} message'

    def test_exception_handling(self):
        """Should include exception info when present"""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

            record = logging.LogRecord(
                name='test',
                level=logging.ERROR,
                pathname='test.py',
                lineno=1,
                msg='Exception occurred',
                args=(),
                exc_info=exc_info
            )

            output = formatter.format(record)
            log_data = json.loads(output)

            assert 'exception' in log_data
            assert 'ValueError' in log_data['exception']
            assert 'Test exception' in log_data['exception']


class TestSetupJSONLogging:
    """Test logging setup function"""

    def test_setup_with_file(self):
        """Should create file handler with rotation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'test.log'

            logger = setup_json_logging(
                log_file=str(log_file),
                log_level='INFO',
                console_output=False
            )

            # Verify logger configured
            assert logger.level == logging.INFO

            # Verify file handler added
            assert len(logger.handlers) == 1
            handler = logger.handlers[0]

            # Verify it's a TimedRotatingFileHandler
            from logging.handlers import TimedRotatingFileHandler
            assert isinstance(handler, TimedRotatingFileHandler)

            # Verify rotation settings
            assert handler.when == 'MIDNIGHT'
            # interval is in seconds (86400 = 1 day)
            assert handler.interval == 86400
            assert handler.backupCount == 30

            # Close handler before cleanup
            for h in logger.handlers:
                h.close()
            logger.handlers.clear()

    def test_setup_console_only(self):
        """Should work without file (console only)"""
        logger = setup_json_logging(
            log_file=None,
            log_level='DEBUG',
            console_output=True
        )

        assert logger.level == logging.DEBUG
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_logging_output_to_file(self):
        """Should write JSON logs to file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'test.log'

            logger = setup_json_logging(
                log_file=str(log_file),
                log_level='INFO',
                console_output=False
            )

            # Log some messages
            logger.info('Test message 1')
            logger.warning('Test message 2')

            # Flush handlers
            for handler in logger.handlers:
                handler.flush()

            # Verify file exists and contains JSON
            assert log_file.exists()

            with open(log_file, 'r') as f:
                lines = f.readlines()

            assert len(lines) == 2

            # Verify each line is valid JSON
            for line in lines:
                log_data = json.loads(line.strip())
                assert 'timestamp' in log_data
                assert 'level' in log_data
                assert 'message' in log_data

            # Close handler before cleanup
            for h in logger.handlers:
                h.close()
            logger.handlers.clear()


class TestContextFunctions:
    """Test context management functions"""

    def test_set_request_context(self):
        """Should set all context variables"""
        set_request_context('req-456', 'pm', 'cerebras')

        assert request_id_ctx.get() == 'req-456'
        assert agent_id_ctx.get() == 'pm'
        assert provider_ctx.get() == 'cerebras'

        clear_request_context()

    def test_clear_request_context(self):
        """Should clear all context variables"""
        set_request_context('req-789', 'architect', 'gemini')
        clear_request_context()

        assert request_id_ctx.get() == ''
        assert agent_id_ctx.get() == ''
        assert provider_ctx.get() == ''

    def test_log_with_context(self):
        """Should log with extra fields"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'context_test.log'

            logger = setup_json_logging(
                log_file=str(log_file),
                log_level='INFO',
                console_output=False
            )

            # Log with extra fields
            log_with_context(
                logger,
                'info',
                'Test with extras',
                status='success',
                latency_ms=250
            )

            # Flush
            for handler in logger.handlers:
                handler.flush()

            # Read and verify
            with open(log_file, 'r') as f:
                line = f.readline()

            log_data = json.loads(line.strip())
            assert log_data['message'] == 'Test with extras'
            assert log_data['status'] == 'success'
            assert log_data['latency_ms'] == 250

            # Close handler before cleanup
            for h in logger.handlers:
                h.close()
            logger.handlers.clear()


class TestJQCompatibility:
    """Test jq command compatibility"""

    def test_jq_parseable_output(self):
        """Should produce jq-parseable JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'jq_test.log'

            logger = setup_json_logging(
                log_file=str(log_file),
                log_level='INFO',
                console_output=False
            )

            # Log messages with different statuses
            set_request_context('req-1', 'analyst', 'groq')
            logger.info('Success message', extra={'status': 'success'})

            set_request_context('req-2', 'pm', 'cerebras')
            logger.error('Error message', extra={'status': 'error'})

            set_request_context('req-3', 'architect', 'gemini')
            logger.info('Another success', extra={'status': 'success'})

            clear_request_context()

            # Flush
            for handler in logger.handlers:
                handler.flush()

            # Read all lines
            with open(log_file, 'r') as f:
                lines = f.readlines()

            # Each line should be valid JSON
            log_entries = []
            for line in lines:
                log_data = json.loads(line.strip())
                log_entries.append(log_data)

            assert len(log_entries) == 3

            # Simulate jq filter: select status == "error"
            errors = [entry for entry in log_entries if entry.get('status') == 'error']
            assert len(errors) == 1
            assert errors[0]['message'] == 'Error message'

            # Simulate jq filter: select status == "success"
            successes = [entry for entry in log_entries if entry.get('status') == 'success']
            assert len(successes) == 2

            # Close handler before cleanup
            for h in logger.handlers:
                h.close()
            logger.handlers.clear()
