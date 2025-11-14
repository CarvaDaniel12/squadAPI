"""
Configuration file watcher for hot-reload capability.

Story 7.5: Config Change Monitoring
Monitors config/*.yaml files for changes and triggers validation + reload.
"""

import logging
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from watchdog.events import FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class ConfigFileHandler(FileSystemEventHandler):
    """Handles file system events for configuration files."""

    def __init__(
        self, on_change: Callable[[list[str]], None], debounce_seconds: float = 0.3
    ):
        """
        Initialize the file handler.

        Args:
            on_change: Callback function to call with list of changed file paths
            debounce_seconds: Time to wait before triggering reload (batches rapid changes)
        """
        self.on_change = on_change
        self.debounce_seconds = debounce_seconds
        self._debounce_timer: Optional[threading.Timer] = None
        self._pending_files: set[str] = set()
        self._lock = threading.Lock()

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Ignore temporary files
        if file_path.suffix in {".tmp", ".swp", ".bak"} or file_path.name.startswith(
            "~"
        ):
            logger.debug(f"Ignoring temporary file: {file_path.name}")
            return

        # Only watch YAML files
        if file_path.suffix not in {".yaml", ".yml"}:
            logger.debug(f"Ignoring non-YAML file: {file_path.name}")
            return

        logger.debug(f"Config file modified: {file_path.name}")
        self._schedule_reload(str(file_path))

    def _schedule_reload(self, file_path: str):
        """
        Schedule a reload after debounce period.

        Multiple rapid changes are batched into a single reload.
        """
        with self._lock:
            self._pending_files.add(file_path)

            # Cancel existing timer
            if self._debounce_timer:
                self._debounce_timer.cancel()

            # Schedule new reload
            self._debounce_timer = threading.Timer(
                self.debounce_seconds, self._trigger_reload
            )
            self._debounce_timer.start()

    def _trigger_reload(self):
        """Trigger reload after debounce period expires."""
        with self._lock:
            files = list(self._pending_files)
            self._pending_files.clear()

        if files:
            file_names = [Path(f).name for f in files]
            logger.info(
                f"Triggering config reload for {len(files)} file(s): {', '.join(file_names)}"
            )
            self.on_change(files)


class ConfigWatcher:
    """Watches configuration files and triggers hot reload on changes."""

    def __init__(
        self,
        config_dir: str,
        on_reload: Callable[[dict], None],
        debounce_seconds: float = 0.3,
    ):
        """
        Initialize the configuration watcher.

        Args:
            config_dir: Directory containing configuration files to watch
            on_reload: Callback function to call with new validated config
            debounce_seconds: Time to wait before triggering reload (batches rapid changes)
        """
        self.config_dir = Path(config_dir)
        self.on_reload = on_reload
        self.observer = Observer()
        self.handler = ConfigFileHandler(
            on_change=self._handle_change, debounce_seconds=debounce_seconds
        )
        self._running = False

    def _handle_change(self, changed_files: list[str]):
        """
        Handle configuration file changes.

        Validates new configuration and triggers reload if valid.
        Keeps previous configuration if validation fails.
        """
        try:
            file_names = [Path(f).name for f in changed_files]
            logger.info(f"Configuration changed: {', '.join(file_names)}")

            # Import here to avoid circular dependency
            from src.config.validation import ConfigurationError, validate_config

            # Validate new configuration
            logger.info("Validating new configuration...")
            config_bundle = validate_config(str(self.config_dir))

            # Call reload callback with new config
            self.on_reload(
                {
                    "settings": config_bundle.settings,
                    "rate_limits": config_bundle.rate_limits,
                    "agent_chains": config_bundle.agent_chains,
                    "providers": config_bundle.providers,
                }
            )

            logger.info(" Configuration reloaded successfully")

        except ConfigurationError as e:
            logger.error(f" Configuration validation failed: {e}")
            logger.error("Keeping previous configuration")
            # TODO Story 8.x: Send Slack alert if enabled

        except Exception as e:
            logger.error(
                f" Unexpected error during config reload: {e}", exc_info=True
            )
            logger.error("Keeping previous configuration")

    def start(self):
        """Start watching configuration files."""
        if self._running:
            logger.warning("ConfigWatcher already running")
            return

        if not self.config_dir.exists():
            logger.warning(f"Config directory does not exist: {self.config_dir}")
            return

        logger.info(f"Starting config watcher for: {self.config_dir}")
        self.observer.schedule(self.handler, str(self.config_dir), recursive=False)
        self.observer.start()
        self._running = True
        logger.info(" Config watcher started")

    def stop(self):
        """Stop watching configuration files."""
        if not self._running:
            return

        logger.info("Stopping config watcher...")
        self.observer.stop()
        self.observer.join()
        self._running = False
        logger.info(" Config watcher stopped")

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

