"""
Unit tests for configuration file watcher.

Story 7.5: Config Change Monitoring
Tests ConfigFileHandler and ConfigWatcher classes.
"""

import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from watchdog.events import FileModifiedEvent

from src.config.watcher import ConfigFileHandler, ConfigWatcher


class TestConfigFileHandler:
    """Test suite for ConfigFileHandler."""

    def test_detects_yaml_file_changes(self, tmp_path):
        """Test that handler detects YAML file modifications."""
        changes = []

        def on_change(files):
            changes.extend(files)

        handler = ConfigFileHandler(on_change=on_change, debounce_seconds=0.1)

        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("test: 123")

        # Simulate modification event
        event = FileModifiedEvent(str(yaml_file))
        handler.on_modified(event)

        # Wait for debounce
        time.sleep(0.2)

        assert len(changes) > 0
        assert str(yaml_file) in changes

    def test_ignores_temporary_files(self, tmp_path):
        """Test that handler ignores temporary files."""
        changes = []
        handler = ConfigFileHandler(on_change=lambda files: changes.extend(files))

        # Test various temporary file extensions
        temp_files = [
            tmp_path / "test.tmp",
            tmp_path / "test.swp",
            tmp_path / "test.bak",
            tmp_path / "~test.yaml",
        ]

        for temp_file in temp_files:
            temp_file.write_text("temp")
            event = FileModifiedEvent(str(temp_file))
            handler.on_modified(event)

        time.sleep(0.4)

        assert len(changes) == 0

    def test_ignores_non_yaml_files(self, tmp_path):
        """Test that handler ignores non-YAML files."""
        changes = []
        handler = ConfigFileHandler(on_change=lambda files: changes.extend(files))

        # Test various non-YAML files
        non_yaml_files = [
            tmp_path / "test.txt",
            tmp_path / "test.json",
            tmp_path / "test.py",
        ]

        for file in non_yaml_files:
            file.write_text("test")
            event = FileModifiedEvent(str(file))
            handler.on_modified(event)

        time.sleep(0.4)

        assert len(changes) == 0

    def test_debounces_rapid_changes(self, tmp_path):
        """Test that multiple rapid changes are debounced to a single reload."""
        reload_count = [0]

        def on_change(files):
            reload_count[0] += 1

        handler = ConfigFileHandler(on_change=on_change, debounce_seconds=0.2)

        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("test: 123")

        # Trigger multiple rapid changes
        for i in range(5):
            event = FileModifiedEvent(str(yaml_file))
            handler.on_modified(event)
            time.sleep(0.03)  # 30ms between changes

        # Wait for debounce
        time.sleep(0.3)

        # Should only reload once due to debouncing
        assert reload_count[0] == 1

    def test_batches_multiple_file_changes(self, tmp_path):
        """Test that changes to multiple files are batched together."""
        changes = []

        def on_change(files):
            changes.append(files)

        handler = ConfigFileHandler(on_change=on_change, debounce_seconds=0.2)

        # Create multiple YAML files
        yaml_files = [
            tmp_path / "rate_limits.yaml",
            tmp_path / "agent_chains.yaml",
            tmp_path / "providers.yaml",
        ]

        for yaml_file in yaml_files:
            yaml_file.write_text("test: 123")

        # Trigger changes to all files rapidly
        for yaml_file in yaml_files:
            event = FileModifiedEvent(str(yaml_file))
            handler.on_modified(event)
            time.sleep(0.03)

        # Wait for debounce
        time.sleep(0.3)

        # Should have one reload with all files
        assert len(changes) == 1
        assert len(changes[0]) == 3

    def test_ignores_directory_events(self, tmp_path):
        """Test that handler ignores directory modification events."""
        changes = []
        handler = ConfigFileHandler(on_change=lambda files: changes.extend(files))

        # Create a directory
        test_dir = tmp_path / "subdir"
        test_dir.mkdir()

        # Simulate directory modification event
        from watchdog.events import DirModifiedEvent

        event = DirModifiedEvent(str(test_dir))
        handler.on_modified(event)

        time.sleep(0.4)

        assert len(changes) == 0


class TestConfigWatcher:
    """Test suite for ConfigWatcher."""

    def test_watcher_starts_and_stops(self, tmp_path):
        """Test that watcher can start and stop cleanly."""
        mock_reload = MagicMock()

        watcher = ConfigWatcher(config_dir=str(tmp_path), on_reload=mock_reload)

        assert not watcher._running

        watcher.start()
        assert watcher._running

        watcher.stop()
        assert not watcher._running

    def test_watcher_context_manager(self, tmp_path):
        """Test that watcher works as a context manager."""
        mock_reload = MagicMock()

        watcher = ConfigWatcher(config_dir=str(tmp_path), on_reload=mock_reload)

        assert not watcher._running

        with watcher:
            assert watcher._running

        assert not watcher._running

    def test_watcher_detects_file_changes(self, tmp_path):
        """Test that watcher detects real file changes."""
        reload_calls = []

        def on_reload(config):
            reload_calls.append(config)

        # Create minimal valid config files
        (tmp_path / "rate_limits.yaml").write_text(
            """
groq:
  rpm: 30
  burst: 30
  tokens_per_minute: 100000
cerebras:
  rpm: 30
  burst: 30
  tokens_per_minute: 100000
gemini:
  rpm: 15
  burst: 15
  tokens_per_minute: 1000000
openrouter:
  rpm: 200
  burst: 200
  tokens_per_minute: 100000
"""
    )

        (tmp_path / "agent_chains.yaml").write_text(
            """
mary:
  primary: groq
  fallbacks:
    - cerebras
    - gemini
john:
  primary: groq
  fallbacks:
    - cerebras
alex:
  primary: groq
  fallbacks:
    - cerebras
"""
        )

        (tmp_path / "providers.yaml").write_text(
            """
groq:
  enabled: true
  model: llama-3.1-8b-instant
  api_key_env: GROQ_API_KEY
  base_url: https://api.groq.com/openai/v1
  timeout: 30

cerebras:
  enabled: true
  model: llama3.1-8b
  api_key_env: CEREBRAS_API_KEY
  base_url: https://api.cerebras.ai/v1
  timeout: 30

gemini:
  enabled: true
  model: gemini-1.5-flash
  api_key_env: GEMINI_API_KEY
  base_url: https://generativelanguage.googleapis.com/v1beta
  timeout: 30

openrouter:
  enabled: true
  model: meta-llama/llama-3.1-8b-instruct:free
  api_key_env: OPENROUTER_API_KEY
  base_url: https://openrouter.ai/api/v1
  timeout: 30
"""
        )

        # Need to set environment variables for validation
        import os

        os.environ["GROQ_API_KEY"] = "test-key-groq"
        os.environ["CEREBRAS_API_KEY"] = "test-key-cerebras"
        os.environ["GEMINI_API_KEY"] = "test-key-gemini"
        os.environ["OPENROUTER_API_KEY"] = "test-key-openrouter"

        watcher = ConfigWatcher(config_dir=str(tmp_path), on_reload=on_reload)
        watcher.start()

        try:
            # Modify a file
            (tmp_path / "rate_limits.yaml").write_text(
                """
groq:
  rpm: 60
  burst: 60
  tokens_per_minute: 200000
cerebras:
  rpm: 30
  burst: 30
  tokens_per_minute: 100000
gemini:
  rpm: 15
  burst: 15
  tokens_per_minute: 1000000
openrouter:
  rpm: 200
  burst: 200
  tokens_per_minute: 100000
"""
            )

            # Wait for detection and reload
            time.sleep(1.0)

            # Should have triggered reload
            assert len(reload_calls) > 0
            assert "rate_limits" in reload_calls[0]

        finally:
            watcher.stop()
            # Cleanup environment variables
            del os.environ["GROQ_API_KEY"]
            del os.environ["CEREBRAS_API_KEY"]
            del os.environ["GEMINI_API_KEY"]
            del os.environ["OPENROUTER_API_KEY"]

    def test_watcher_rejects_invalid_config(self, tmp_path, caplog):
        """Test that watcher rejects invalid configuration and keeps old config."""
        reload_calls = []

        def on_reload(config):
            reload_calls.append(config)

        # Create valid initial config
        (tmp_path / "rate_limits.yaml").write_text(
            """
groq:
  rpm: 30
  burst: 30
  tokens_per_minute: 100000
cerebras:
  rpm: 30
  burst: 30
  tokens_per_minute: 100000
gemini:
  rpm: 15
  burst: 15
  tokens_per_minute: 1000000
openrouter:
  rpm: 200
  burst: 200
  tokens_per_minute: 100000
"""
        )

        (tmp_path / "agent_chains.yaml").write_text(
            """
mary:
  primary: groq
  fallbacks:
    - cerebras
"""
        )

        (tmp_path / "providers.yaml").write_text(
            """
groq:
  enabled: true
  model: llama-3.1-8b-instant
  api_key_env: GROQ_API_KEY
  base_url: https://api.groq.com/openai/v1
  timeout: 30

cerebras:
  enabled: true
  model: llama3.1-8b
  api_key_env: CEREBRAS_API_KEY
  base_url: https://api.cerebras.ai/v1
  timeout: 30

gemini:
  enabled: true
  model: gemini-1.5-flash
  api_key_env: GEMINI_API_KEY
  base_url: https://generativelanguage.googleapis.com/v1beta
  timeout: 30

openrouter:
  enabled: true
  model: meta-llama/llama-3.1-8b-instruct:free
  api_key_env: OPENROUTER_API_KEY
  base_url: https://openrouter.ai/api/v1
  timeout: 30
"""
        )

        import os

        os.environ["GROQ_API_KEY"] = "test-key"
        os.environ["CEREBRAS_API_KEY"] = "test-key"
        os.environ["GEMINI_API_KEY"] = "test-key"
        os.environ["OPENROUTER_API_KEY"] = "test-key"

        watcher = ConfigWatcher(config_dir=str(tmp_path), on_reload=on_reload)
        watcher.start()

        try:
            # Create invalid config (rpm = 0)
            (tmp_path / "rate_limits.yaml").write_text(
                """
groq:
  rpm: 0
  burst: 30
  tokens_per_minute: 100000
"""
            )

            # Wait for detection
            time.sleep(1.0)

            # Should NOT have triggered reload
            assert len(reload_calls) == 0

            # Should have logged error
            assert "validation failed" in caplog.text.lower()

        finally:
            watcher.stop()
            del os.environ["GROQ_API_KEY"]
            del os.environ["CEREBRAS_API_KEY"]
            del os.environ["GEMINI_API_KEY"]
            del os.environ["OPENROUTER_API_KEY"]

    def test_watcher_handles_yaml_parse_errors(self, tmp_path, caplog):
        """Test that watcher handles YAML syntax errors gracefully."""
        reload_calls = []

        watcher = ConfigWatcher(
            config_dir=str(tmp_path), on_reload=lambda c: reload_calls.append(c)
        )

        # Create file with invalid YAML syntax
        (tmp_path / "rate_limits.yaml").write_text(
            """
groq:
  rpm: [invalid yaml syntax
"""
        )

        watcher.start()

        try:
            # Trigger change
            (tmp_path / "rate_limits.yaml").touch()

            time.sleep(1.0)

            # Should NOT reload
            assert len(reload_calls) == 0

            # Should log error
            assert "error" in caplog.text.lower()

        finally:
            watcher.stop()

    def test_watcher_warns_on_double_start(self, tmp_path, caplog):
        """Test that watcher warns if started twice."""
        mock_reload = MagicMock()

        watcher = ConfigWatcher(config_dir=str(tmp_path), on_reload=mock_reload)

        watcher.start()
        watcher.start()  # Second start

        assert "already running" in caplog.text.lower()

        watcher.stop()

    def test_watcher_handles_missing_config_dir(self, caplog):
        """Test that watcher handles missing config directory gracefully."""
        mock_reload = MagicMock()

        watcher = ConfigWatcher(
            config_dir="/nonexistent/path", on_reload=mock_reload
        )

        watcher.start()

        assert "does not exist" in caplog.text.lower()

        watcher.stop()
