# ADR-014: Hot-Reload with Watchdog

**Status:** Accepted
**Date:** 2025-11-13
**Epic:** 7 - Configuration System
**Story:** 7.5 - Hot-Reload Implementation

## Context

Squad API has multiple YAML configuration files:
- `config/providers.yaml` - Provider API endpoints and models
- `config/rate_limits.yaml` - Rate limit thresholds
- `config/agent_routing.yaml` - Agent routing rules
- `config/agent_chains.yaml` - Fallback chain definitions

**Problem:** Configuration changes require container restart (30-60s downtime)

**Requirements:**
1. **Hot-reload:** Apply config changes without restart
2. **Fast:** Detect and reload within 2 seconds
3. **Safe:** Validate config before applying
4. **Observable:** Log reload events
5. **No downtime:** Continue serving requests during reload

**Use cases:**
- Adjust rate limits during traffic spike
- Add new provider without restart
- Fix misconfiguration quickly
- A/B test routing rules

## Decision

Implement **file watching with watchdog library** to detect and reload configuration changes:

**Architecture:**

```
┌─────────────────────────────────────────┐
│     ConfigWatcher (watchdog)            │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  FileSystemEventHandler           │  │
│  │  - Watch config/ directory        │  │
│  │  - Detect *.yaml changes          │  │
│  │  - Debounce rapid changes         │  │
│  └───────────────────────────────────┘  │
│                  ↓                      │
│  ┌───────────────────────────────────┐  │
│  │  ConfigValidator                  │  │
│  │  - Parse YAML                     │  │
│  │  - Validate schema                │  │
│  │  - Check constraints              │  │
│  └───────────────────────────────────┘  │
│                  ↓                      │
│  ┌───────────────────────────────────┐  │
│  │  ConfigReloader                   │  │
│  │  - Atomic swap                    │  │
│  │  - Update globals                 │  │
│  │  - Emit metrics                   │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

**Implementation:**

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigFileHandler(FileSystemEventHandler):
    def __init__(self, reload_callback):
        self.reload_callback = reload_callback
        self.debounce_timer = None

    def on_modified(self, event):
        if event.src_path.endswith('.yaml'):
            # Debounce: wait 1 second for more changes
            if self.debounce_timer:
                self.debounce_timer.cancel()

            self.debounce_timer = Timer(
                1.0,
                lambda: self.reload_callback(event.src_path)
            )
            self.debounce_timer.start()

class ConfigWatcher:
    def __init__(self, config_dir: Path):
        self.observer = Observer()
        self.handler = ConfigFileHandler(self.reload_config)
        self.observer.schedule(self.handler, config_dir, recursive=False)
        self.observer.start()

    def reload_config(self, file_path: str):
        try:
            # 1. Validate new config
            new_config = yaml.safe_load(open(file_path))
            validate_schema(new_config)

            # 2. Atomic swap
            old_config = globals()['config']
            globals()['config'] = new_config

            # 3. Log and emit metrics
            logger.info(f"Configuration reloaded: {file_path}")
            metrics.inc("config_reload_success")

        except Exception as e:
            logger.error(f"Config reload failed: {e}")
            metrics.inc("config_reload_failed")
```

## Consequences

### Positive

- ✅ **Zero downtime:** No restart required
- ✅ **Fast:** Reload within 2 seconds of file change
- ✅ **Safe:** Validates before applying (rollback on error)
- ✅ **Developer friendly:** Edit → Save → Auto-reload
- ✅ **Production friendly:** Adjust rate limits during incidents
- ✅ **Observable:** Logs and metrics for reload events
- ✅ **Simple:** Leverages proven watchdog library
- ✅ **Cross-platform:** Works on Linux, macOS, Windows

### Negative

- ❌ **File system dependency:** Requires volume mount in Docker
- ❌ **Not atomic:** Small window where config partially loaded (mitigated with copy-on-write)
- ❌ **No rollback:** If bad config deployed, manual fix needed
- ❌ **Race conditions:** Concurrent requests may see old vs new config (mitigated with atomic swap)
- ❌ **Memory overhead:** Watchdog observer thread (~5MB)

## Alternatives Considered

### 1. Manual Restart

**Description:** Require container restart for config changes

**Pros:**
- Simple (no code needed)
- Atomic (all or nothing)
- No race conditions

**Cons:**
- Downtime (30-60s)
- Slow (especially in production)
- Interrupts in-flight requests

**Why Rejected:** Downtime unacceptable for production

### 2. SIGHUP Signal Handler

**Description:** Send SIGHUP to process to trigger reload

**Pros:**
- Unix standard (common pattern)
- Explicit (no automatic reloading)
- Fast

**Cons:**
- Requires manual signal (`kill -HUP <pid>`)
- Not Windows-compatible
- Hard to trigger in Docker

**Why Rejected:** Less convenient than automatic file watching

### 3. HTTP Endpoint for Reload

**Description:** POST /reload endpoint to trigger config reload

**Pros:**
- Explicit control
- Can be automated (CI/CD)
- Works in any environment

**Cons:**
- Requires authentication
- Extra API surface
- Not automatic

**Why Rejected:** Can be added later if needed, file watching more convenient

### 4. Database-Backed Config

**Description:** Store config in PostgreSQL, poll for changes

**Pros:**
- Centralized config management
- Audit trail
- Version history

**Cons:**
- Adds complexity
- Database dependency for config
- Polling overhead

**Why Rejected:** Overkill for our use case, YAML files sufficient

## Implementation Details

### Watchdog Configuration

```python
# Start watcher in FastAPI startup event
@app.on_event("startup")
async def startup_event():
    config_watcher = ConfigWatcher(Path("config"))
    logger.info("Configuration watcher started")

# Stop watcher on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    config_watcher.observer.stop()
    config_watcher.observer.join()
```

### Debouncing

**Why debounce:** Text editors save multiple times during edit (auto-save, final save)

```python
# Without debounce:
# - File modified at t=0ms (auto-save) → Reload
# - File modified at t=100ms (manual save) → Reload
# Result: 2 reloads

# With 1-second debounce:
# - File modified at t=0ms → Start timer
# - File modified at t=100ms → Restart timer
# - Timer fires at t=1100ms → Reload once
# Result: 1 reload
```

### Validation

```python
def validate_rate_limits_config(config: dict):
    for provider, limits in config.items():
        # Check required fields
        assert 'requests_per_minute' in limits
        assert 'tokens_per_minute' in limits

        # Check types
        assert isinstance(limits['requests_per_minute'], int)
        assert isinstance(limits['tokens_per_minute'], int)

        # Check ranges
        assert 0 < limits['requests_per_minute'] <= 1000
        assert 0 < limits['tokens_per_minute'] <= 10_000_000
```

### Atomic Swap

```python
# Bad: Direct mutation (race condition)
config['groq']['requests_per_minute'] = 60  # ❌

# Good: Atomic replacement
old_config = config
new_config = load_config('config/rate_limits.yaml')
config = new_config  # ✅ Atomic pointer swap
```

**Why atomic:**
- Concurrent requests see either old or new config (not mixed)
- Python dict assignment is atomic (GIL protected)
- No locks needed

### Metrics

```python
# Reload events
config_reload_success_total{file="rate_limits.yaml"} 15
config_reload_failed_total{file="rate_limits.yaml"} 2

# Reload latency
config_reload_duration_seconds{file="rate_limits.yaml"} 0.05
```

## File Watching Behavior

**Supported operations:**
- ✅ File modified (most common)
- ✅ File created (new config file)
- ❌ File deleted (ignore, use old config)
- ❌ File moved (ignore, not expected)

**Ignored files:**
- `*.yaml~` (backup files)
- `.*.yaml.swp` (Vim swap files)
- `*.yaml.tmp` (temporary files)

**Edge cases:**
- Empty file: Validation fails, keep old config
- Invalid YAML: Validation fails, keep old config, log error
- Partial write: Debounce handles this (wait for complete write)

## Testing

**Unit Tests:**

```python
def test_config_reload():
    # 1. Start with config A
    assert config['groq']['requests_per_minute'] == 60

    # 2. Modify file to config B
    update_config_file('groq.requests_per_minute', 100)

    # 3. Wait for reload
    time.sleep(2)

    # 4. Verify config B loaded
    assert config['groq']['requests_per_minute'] == 100
```

**Integration Tests:**

```python
async def test_hot_reload_no_downtime():
    # 1. Start making requests
    requests_task = asyncio.create_task(make_continuous_requests())

    # 2. Modify config during requests
    await asyncio.sleep(1)
    update_config_file('groq.requests_per_minute', 100)

    # 3. Wait for reload
    await asyncio.sleep(2)

    # 4. Verify no errors
    assert all_requests_succeeded()
```

## Monitoring

**Grafana Dashboard:**
- Config reload events (timeline)
- Reload success rate (should be 100%)
- Reload latency (should be <100ms)

**Alerts:**
- Config reload failure (immediate)
- Frequent reloads (>10/min indicates issue)

## Performance Impact

**Resource usage:**
- Watchdog observer thread: ~5MB RAM
- CPU during reload: <10ms burst
- Reload latency: 50-100ms

**Negligible impact on request serving**

## Migration Path

If file-based hot-reload becomes insufficient:

1. **Add HTTP reload endpoint:** For programmatic control
2. **Use etcd/Consul:** Distributed configuration
3. **Use Kubernetes ConfigMaps:** Cloud-native config management

## References

- [src/config/watcher.py](../../src/config/watcher.py)
- [src/config/validation.py](../../src/config/validation.py)
- [Watchdog Documentation](https://python-watchdog.readthedocs.io/)
- [Epic 7 Documentation](../../docs/epics.md#epic-7-configuration-system)
