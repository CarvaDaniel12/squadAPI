# Story 7.5: Config Change Monitoring

**Epic:** Epic 7 - Configuration System
**Story Points:** 5
**Priority:** Medium
**Status:** In Progress

## Story Description

As a **system administrator**, I want the **application to automatically detect and reload configuration changes** so that I can **update rate limits, agent chains, and provider settings without restarting the service**.

## Business Value

- **Zero-Downtime Updates:** Modify configuration without service interruption
- **Operational Efficiency:** Adjust rate limits in real-time based on monitoring
- **Development Velocity:** Iterate on agent chains without constant restarts
- **Production Safety:** Test configuration changes with immediate feedback

## Acceptance Criteria

### AC1: Watch Configuration Files
- **Given** the application is running
- **When** any YAML file in `config/` directory changes
- **Then** the system detects the change within 1 second
- **And** logs the detected file path and change type

**Implementation Requirements:**
- Use `watchdog` library for file system monitoring
- Monitor `config/rate_limits.yaml`, `config/agent_chains.yaml`, `config/providers.yaml`
- Debounce multiple rapid changes (300ms window)
- Ignore temporary files (`.tmp`, `.swp`, `~`)
- Handle file move/rename events

**Test Cases:**
1. Modify `rate_limits.yaml` → change detected
2. Modify `agent_chains.yaml` → change detected
3. Modify `providers.yaml` → change detected
4. Modify `.env` → no detection (env vars require restart)
5. Create temporary file → ignored
6. Multiple rapid edits → debounced to single reload

### AC2: Validate Before Reload
- **Given** a configuration file change is detected
- **When** the system attempts to reload
- **Then** the new configuration is validated first
- **And** invalid configuration is rejected with error logging
- **And** the application continues with the previous valid configuration

**Implementation Requirements:**
- Reuse `validate_config()` from Story 7.3
- Validate all YAML files together (cross-validation)
- Log validation errors with file name and error details
- Keep current configuration if validation fails
- Emit metrics for successful/failed reloads

**Test Cases:**
1. Valid config change → validation passes → reload succeeds
2. Invalid rate limits (rpm=0) → validation fails → old config retained
3. Unknown provider in chain → validation fails → old config retained
4. Missing API key for enabled provider → validation fails → old config retained
5. Syntax error in YAML → parsing fails → old config retained

### AC3: Hot Reload Configuration
- **Given** a valid configuration change is detected
- **When** validation passes
- **Then** the new configuration is applied to running components
- **And** existing rate limiters are updated with new values
- **And** agent chains are updated with new provider lists
- **And** all changes are logged

**Implementation Requirements:**
- Update `RateLimiter` instances with new rpm/burst/tokens values
- Update `AgentOrchestrator` with new agent chains
- Update `ProviderFactory` with new provider settings
- Thread-safe configuration updates (use locks)
- Log old → new values for auditing
- Emit reload metrics (duration, files changed)

**Test Cases:**
1. Update rate limit → existing RateLimiter reflects new values
2. Update agent chain → next agent request uses new chain
3. Update provider settings → new requests use updated config
4. Concurrent requests during reload → no errors or data races
5. Multiple files change → single atomic reload

### AC4: Graceful Error Handling
- **Given** an error occurs during reload
- **When** the error is caught
- **Then** the system logs the error with full context
- **And** the application continues running with previous configuration
- **And** an alert is sent (if Slack alerts enabled)

**Implementation Requirements:**
- Try-catch around reload logic
- Log error type, file path, stack trace
- Send Slack alert for reload failures (if configured)
- Emit error metrics
- Retry logic for transient errors (e.g., file locked)

**Test Cases:**
1. File read error → logged, old config retained
2. YAML parse error → logged, old config retained
3. Validation error → logged, old config retained
4. Reload timeout → logged, old config retained
5. Slack alert enabled → error notification sent

## Technical Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Startup                      │
│  1. Load initial config with validate_config()              │
│  2. Start ConfigWatcher in background thread                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      ConfigWatcher                           │
│  - Observer thread monitors config/*.yaml                   │
│  - FileSystemEventHandler receives events                   │
│  - Debounce timer (300ms) batches rapid changes             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  File Changed?  │
                    └─────────────────┘
                        │           │
                   Yes  │           │  No (temp file)
                        ▼           ▼
              ┌──────────────┐  Ignore
              │  Debounce    │
              │  (300ms)     │
              └──────────────┘
                        │
                        ▼
              ┌──────────────────────┐
              │  validate_config()   │
              │  - Parse YAML        │
              │  - Pydantic models   │
              │  - Cross-validate    │
              └──────────────────────┘
                    │           │
              Valid │           │ Invalid
                    ▼           ▼
          ┌──────────────┐  ┌──────────────┐
          │ Hot Reload   │  │ Log Error    │
          │ - Rate       │  │ Keep Old     │
          │   Limiters   │  │ Config       │
          │ - Chains     │  │ Send Alert   │
          │ - Providers  │  └──────────────┘
          └──────────────┘
                    │
                    ▼
          ┌──────────────────┐
          │ Log Success      │
          │ Emit Metrics     │
          └──────────────────┘
```

### Component Design

#### 1. ConfigWatcher Class

```python
# src/config/watcher.py

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
import threading
import time
from pathlib import Path
from typing import Callable, Optional
import logging

logger = logging.getLogger(__name__)

class ConfigFileHandler(FileSystemEventHandler):
    """Handles file system events for config files."""

    def __init__(self, on_change: Callable[[str], None], debounce_seconds: float = 0.3):
        self.on_change = on_change
        self.debounce_seconds = debounce_seconds
        self._debounce_timer: Optional[threading.Timer] = None
        self._pending_files: set[str] = set()
        self._lock = threading.Lock()

    def on_modified(self, event):
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Ignore temporary files
        if file_path.suffix in {'.tmp', '.swp', '.bak'} or file_path.name.startswith('~'):
            return

        # Only watch YAML files
        if file_path.suffix not in {'.yaml', '.yml'}:
            return

        logger.debug(f"Config file modified: {file_path}")
        self._schedule_reload(str(file_path))

    def _schedule_reload(self, file_path: str):
        """Debounce multiple rapid changes."""
        with self._lock:
            self._pending_files.add(file_path)

            # Cancel existing timer
            if self._debounce_timer:
                self._debounce_timer.cancel()

            # Schedule new reload
            self._debounce_timer = threading.Timer(
                self.debounce_seconds,
                self._trigger_reload
            )
            self._debounce_timer.start()

    def _trigger_reload(self):
        """Trigger reload after debounce period."""
        with self._lock:
            files = list(self._pending_files)
            self._pending_files.clear()

        if files:
            logger.info(f"Triggering config reload for {len(files)} file(s)")
            self.on_change(files)


class ConfigWatcher:
    """Watches configuration files and triggers hot reload."""

    def __init__(
        self,
        config_dir: str,
        on_reload: Callable[[dict], None],
        debounce_seconds: float = 0.3
    ):
        self.config_dir = Path(config_dir)
        self.on_reload = on_reload
        self.observer = Observer()
        self.handler = ConfigFileHandler(
            on_change=self._handle_change,
            debounce_seconds=debounce_seconds
        )
        self._running = False

    def _handle_change(self, changed_files: list[str]):
        """Handle configuration file changes."""
        try:
            logger.info(f"Configuration changed: {', '.join(Path(f).name for f in changed_files)}")

            # Import here to avoid circular dependency
            from src.config.validation import validate_config, ConfigurationError

            # Validate new configuration
            logger.info("Validating new configuration...")
            config_bundle = validate_config(str(self.config_dir))

            # Call reload callback with new config
            self.on_reload({
                'settings': config_bundle.settings,
                'rate_limits': config_bundle.rate_limits,
                'agent_chains': config_bundle.agent_chains,
                'providers': config_bundle.providers
            })

            logger.info("✅ Configuration reloaded successfully")

        except ConfigurationError as e:
            logger.error(f"❌ Configuration validation failed: {e}")
            logger.error("Keeping previous configuration")
            # TODO: Send Slack alert if enabled

        except Exception as e:
            logger.error(f"❌ Unexpected error during config reload: {e}", exc_info=True)
            logger.error("Keeping previous configuration")

    def start(self):
        """Start watching configuration files."""
        if self._running:
            logger.warning("ConfigWatcher already running")
            return

        logger.info(f"Starting config watcher for: {self.config_dir}")
        self.observer.schedule(self.handler, str(self.config_dir), recursive=False)
        self.observer.start()
        self._running = True
        logger.info("✅ Config watcher started")

    def stop(self):
        """Stop watching configuration files."""
        if not self._running:
            return

        logger.info("Stopping config watcher...")
        self.observer.stop()
        self.observer.join()
        self._running = False
        logger.info("✅ Config watcher stopped")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
```

#### 2. Reload Handler Integration

```python
# src/config/reload.py

import logging
from typing import Dict, Any
from threading import Lock

logger = logging.getLogger(__name__)

class ConfigReloadHandler:
    """Handles hot reload of configuration components."""

    def __init__(self):
        self._lock = Lock()
        self._rate_limiters: Dict[str, Any] = {}
        self._orchestrator: Any = None
        self._provider_factory: Any = None

    def register_rate_limiters(self, rate_limiters: Dict[str, Any]):
        """Register rate limiters for updates."""
        with self._lock:
            self._rate_limiters = rate_limiters
            logger.debug(f"Registered {len(rate_limiters)} rate limiters")

    def register_orchestrator(self, orchestrator: Any):
        """Register orchestrator for chain updates."""
        with self._lock:
            self._orchestrator = orchestrator
            logger.debug("Registered orchestrator")

    def register_provider_factory(self, factory: Any):
        """Register provider factory for updates."""
        with self._lock:
            self._provider_factory = factory
            logger.debug("Registered provider factory")

    def reload(self, new_config: Dict[str, Any]):
        """Apply new configuration to all components."""
        with self._lock:
            logger.info("Applying new configuration...")

            # Update rate limiters
            if 'rate_limits' in new_config:
                self._update_rate_limiters(new_config['rate_limits'])

            # Update agent chains
            if 'agent_chains' in new_config and self._orchestrator:
                self._update_orchestrator(new_config['agent_chains'])

            # Update providers
            if 'providers' in new_config and self._provider_factory:
                self._update_providers(new_config['providers'])

            logger.info("✅ Configuration applied successfully")

    def _update_rate_limiters(self, rate_limits_config):
        """Update rate limiter values."""
        for provider_name, rate_limiter in self._rate_limiters.items():
            if hasattr(rate_limits_config, provider_name):
                limits = getattr(rate_limits_config, provider_name)
                old_rpm = rate_limiter.rpm if hasattr(rate_limiter, 'rpm') else 'N/A'
                new_rpm = limits.rpm

                # Update rate limiter (implementation depends on RateLimiter API)
                if hasattr(rate_limiter, 'update_limits'):
                    rate_limiter.update_limits(
                        rpm=limits.rpm,
                        burst=limits.burst,
                        tokens_per_minute=limits.tokens_per_minute
                    )
                    logger.info(f"Updated {provider_name}: {old_rpm} → {new_rpm} rpm")

    def _update_orchestrator(self, agent_chains_config):
        """Update agent chains in orchestrator."""
        if hasattr(self._orchestrator, 'update_chains'):
            self._orchestrator.update_chains(agent_chains_config)
            logger.info("Updated agent chains")

    def _update_providers(self, providers_config):
        """Update provider settings in factory."""
        if hasattr(self._provider_factory, 'update_providers'):
            self._provider_factory.update_providers(providers_config)
            logger.info("Updated provider settings")
```

#### 3. Main Integration

```python
# src/main.py updates

from src.config.watcher import ConfigWatcher
from src.config.reload import ConfigReloadHandler

# Global reload handler
reload_handler = ConfigReloadHandler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with config validation and hot reload."""
    # Validate configuration on startup
    logger.info("Validating configuration...")
    config_bundle = validate_config(config_dir="config")

    # ... initialize components ...

    # Register components with reload handler
    reload_handler.register_rate_limiters(rate_limiters)
    reload_handler.register_orchestrator(orchestrator)
    reload_handler.register_provider_factory(provider_factory)

    # Start config watcher
    config_watcher = ConfigWatcher(
        config_dir="config",
        on_reload=reload_handler.reload
    )
    config_watcher.start()

    yield

    # Cleanup
    config_watcher.stop()
```

### Dependencies

Add to `requirements.txt`:
```
watchdog>=3.0.0  # File system monitoring
```

## Test Plan

### Unit Tests

**File:** `tests/unit/test_config/test_watcher.py`

```python
import pytest
import time
from pathlib import Path
from src.config.watcher import ConfigFileHandler, ConfigWatcher

def test_config_file_handler_detects_yaml_changes(tmp_path):
    """Test that handler detects YAML file modifications."""
    changes = []
    handler = ConfigFileHandler(on_change=lambda files: changes.extend(files))

    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text("test: 123")

    # Simulate modification event
    from watchdog.events import FileModifiedEvent
    event = FileModifiedEvent(str(yaml_file))
    handler.on_modified(event)

    # Wait for debounce
    time.sleep(0.4)

    assert len(changes) > 0
    assert str(yaml_file) in changes

def test_config_file_handler_ignores_temp_files(tmp_path):
    """Test that handler ignores temporary files."""
    changes = []
    handler = ConfigFileHandler(on_change=lambda files: changes.extend(files))

    temp_file = tmp_path / "test.tmp"
    temp_file.write_text("temp")

    from watchdog.events import FileModifiedEvent
    event = FileModifiedEvent(str(temp_file))
    handler.on_modified(event)

    time.sleep(0.4)

    assert len(changes) == 0

def test_config_file_handler_debounces_rapid_changes(tmp_path):
    """Test that multiple rapid changes are debounced."""
    reload_count = [0]
    def on_change(files):
        reload_count[0] += 1

    handler = ConfigFileHandler(on_change=on_change, debounce_seconds=0.3)

    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text("test: 123")

    from watchdog.events import FileModifiedEvent

    # Trigger multiple rapid changes
    for i in range(5):
        event = FileModifiedEvent(str(yaml_file))
        handler.on_modified(event)
        time.sleep(0.05)  # 50ms between changes

    # Wait for debounce
    time.sleep(0.4)

    # Should only reload once due to debouncing
    assert reload_count[0] == 1

def test_config_watcher_validates_before_reload(tmp_path, monkeypatch):
    """Test that watcher validates config before reloading."""
    reload_called = []

    def mock_on_reload(config):
        reload_called.append(config)

    watcher = ConfigWatcher(
        config_dir=str(tmp_path),
        on_reload=mock_on_reload
    )

    # Create valid config files
    (tmp_path / "rate_limits.yaml").write_text("""
    groq:
      rpm: 30
      burst: 30
      tokens_per_minute: 100000
    """)

    # Start watcher
    watcher.start()

    # Modify file
    (tmp_path / "rate_limits.yaml").write_text("""
    groq:
      rpm: 60
      burst: 60
      tokens_per_minute: 200000
    """)

    # Wait for detection and reload
    time.sleep(0.5)

    # Should have called reload
    assert len(reload_called) > 0

    watcher.stop()

def test_config_watcher_rejects_invalid_config(tmp_path, caplog):
    """Test that watcher rejects invalid configuration."""
    reload_called = []

    watcher = ConfigWatcher(
        config_dir=str(tmp_path),
        on_reload=lambda c: reload_called.append(c)
    )

    # Create invalid config (rpm = 0)
    (tmp_path / "rate_limits.yaml").write_text("""
    groq:
      rpm: 0
      burst: 30
      tokens_per_minute: 100000
    """)

    watcher.start()

    # Trigger change
    (tmp_path / "rate_limits.yaml").touch()

    time.sleep(0.5)

    # Should NOT reload
    assert len(reload_called) == 0

    # Should log error
    assert "validation failed" in caplog.text.lower()

    watcher.stop()
```

**File:** `tests/unit/test_config/test_reload.py`

```python
import pytest
from src.config.reload import ConfigReloadHandler

def test_reload_handler_updates_rate_limiters():
    """Test that reload handler updates rate limiters."""
    # Mock rate limiter
    class MockRateLimiter:
        def __init__(self):
            self.rpm = 30
            self.burst = 30
            self.tokens_per_minute = 100000

        def update_limits(self, rpm, burst, tokens_per_minute):
            self.rpm = rpm
            self.burst = burst
            self.tokens_per_minute = tokens_per_minute

    limiter = MockRateLimiter()
    handler = ConfigReloadHandler()
    handler.register_rate_limiters({'groq': limiter})

    # Mock new config
    class RateLimitConfig:
        rpm = 60
        burst = 60
        tokens_per_minute = 200000

    class NewConfig:
        groq = RateLimitConfig()

    handler.reload({'rate_limits': NewConfig()})

    # Verify update
    assert limiter.rpm == 60
    assert limiter.burst == 60
    assert limiter.tokens_per_minute == 200000

def test_reload_handler_thread_safe():
    """Test that reload handler is thread-safe."""
    import threading

    handler = ConfigReloadHandler()
    errors = []

    def reload_config():
        try:
            handler.reload({})
        except Exception as e:
            errors.append(e)

    # Concurrent reloads
    threads = [threading.Thread(target=reload_config) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
```

### Integration Tests

**File:** `tests/integration/test_config_hot_reload.py`

```python
import pytest
import time
from pathlib import Path

@pytest.mark.integration
def test_hot_reload_rate_limits(test_app, tmp_config_dir):
    """Test hot reload of rate limits."""
    # Initial request
    response = test_app.get("/api/agents")
    assert response.status_code == 200

    # Update rate limits
    rate_limits_file = tmp_config_dir / "rate_limits.yaml"
    rate_limits_file.write_text("""
    groq:
      rpm: 120
      burst: 120
      tokens_per_minute: 500000
    """)

    # Wait for reload
    time.sleep(1)

    # Verify new limits applied (would need metrics endpoint)
    # This is a placeholder - actual verification depends on implementation

@pytest.mark.integration
def test_hot_reload_agent_chains(test_app, tmp_config_dir):
    """Test hot reload of agent chains."""
    # Update agent chains
    chains_file = tmp_config_dir / "agent_chains.yaml"
    chains_file.write_text("""
    mary:
      primary: cerebras
      fallbacks:
        - groq
        - gemini
    """)

    # Wait for reload
    time.sleep(1)

    # Make request to mary
    response = test_app.post("/api/chat", json={
        "agent_name": "mary",
        "message": "test"
    })

    # Should use new chain (cerebras first)
    # Verification depends on logging/metrics
```

## Definition of Done

- [x] Story artifact created with AC1-AC4
- [ ] `ConfigWatcher` class implemented in `src/config/watcher.py`
- [ ] `ConfigReloadHandler` class implemented in `src/config/reload.py`
- [ ] File system monitoring with watchdog
- [ ] Debouncing logic (300ms window)
- [ ] Validation before reload (reuse `validate_config()`)
- [ ] Hot reload for rate limiters
- [ ] Hot reload for agent chains
- [ ] Hot reload for provider settings
- [ ] Thread-safe reload with locks
- [ ] Error handling with logging
- [ ] Unit tests: 12+ tests passing
- [ ] Integration tests: 2+ scenarios
- [ ] Test coverage: >85% for new code
- [ ] `watchdog` dependency added to requirements.txt
- [ ] Integration with main.py lifespan
- [ ] Manual testing: modify config files while app running
- [ ] Documentation updated in configuration.md
- [ ] Metrics emitted for reload success/failure
- [ ] Sprint status updated

## Testing Checklist

### Manual Testing
- [ ] Start application
- [ ] Modify `rate_limits.yaml` → reload detected and applied
- [ ] Modify `agent_chains.yaml` → reload detected and applied
- [ ] Modify `providers.yaml` → reload detected and applied
- [ ] Introduce invalid config → validation fails, old config retained
- [ ] Multiple rapid edits → debounced to single reload
- [ ] Check logs for reload messages
- [ ] Verify no application errors during reload

### Automated Testing
- [ ] Unit tests for ConfigFileHandler
- [ ] Unit tests for ConfigWatcher
- [ ] Unit tests for ConfigReloadHandler
- [ ] Integration tests for full reload flow
- [ ] Test debouncing behavior
- [ ] Test validation errors
- [ ] Test thread safety

## Dependencies

- **Story 7.1:** YAML Config Loader (provides config loading)
- **Story 7.3:** Config Validation (provides validation logic)
- **External:** `watchdog` library for file monitoring

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Race conditions during reload | High | Use threading.Lock for all updates |
| Invalid config breaks app | High | Validate before applying, keep old config on failure |
| File system events missed | Medium | Use reliable watchdog Observer, log all events |
| Memory leaks from observers | Medium | Proper cleanup in lifespan shutdown |
| Slow validation blocks threads | Medium | Run validation in background, use timeouts |

## Notes

- Environment variables (`.env`) still require restart - hot reload only for YAML
- Consider adding `/api/config/reload` endpoint for manual reload trigger
- Future: Add configuration versioning for rollback capability
- Future: Add configuration diff in logs (old → new values)
- Metrics integration will be added for monitoring reload events

## References

- [Watchdog Documentation](https://python-watchdog.readthedocs.io/)
- Epic 7: Configuration System
- Story 7.1: YAML Config Loader
- Story 7.3: Config Validation on Startup
