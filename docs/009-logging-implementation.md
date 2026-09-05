# Logging Implementation

This document describes the current logging system used by the Student Performance Indicator project.

## Components

| File | Responsibility |
|---|---|
| `src/utils/logger.py` | Logger class, formatter, manager, and public logging API |
| `config/logger_config.yaml` | Handler, formatter, and logger configuration |
| `artifacts/logs/app.log` | JSON log output destination for local application runs |

The default logger name is `student_performance_indicator`.

## Logger architecture

The project logger is implemented in `src/utils/logger.py` and follows a structured-logging pattern:

- `ProjectLogger` subclasses `logging.Logger`.
- Each standard logging method (`debug`, `info`, `warning`, `error`, `exception`, `critical`) passes unknown keyword arguments into the logger as structured fields.
- `ProjectLogger._log_structured()` converts keyword arguments into an `extra` dictionary before delegating to `logging.Logger._log()`.
- `ProjectLogger.exception()` automatically sets `exc_info=True` when the caller does not provide it.
- `JsonFormatter` serializes each log record to a single JSON line.

`ProjectLoggerManager` reads a YAML config file, validates the required sections, ensures the log file directory exists, and applies the configuration with `logging.config.dictConfig()`. `get_logger()` creates a manager for the requested logger name and returns the configured logger instance.

## Configuration

The active logging configuration is defined in `config/logger_config.yaml` and is loaded from the project root. The config must contain:

- `version`
- `formatters`
- `handlers`
- `loggers`
- `root`

The current setup is:

| Handler | Level | Destination | Formatter |
|---|---|---|---|
| `console` | `INFO` | standard output | JSON |
| `file` | `INFO` | `artifacts/logs/app.log` | JSON |

The named logger `student_performance_indicator` is configured with `level: INFO`, `handlers: [console, file]`, and `propagate: false`. The root logger is also `INFO` and only writes to the console.

Because the logger is configured at `INFO`, `logger.debug(...)` calls are filtered out unless the logging level is lowered in the YAML file.

## Using the logger

### Default app logger

Use `get_logger()` for most application code:

```python
from src.utils.logger import get_logger

logger = get_logger()
logger.info("Data ingestion started")
logger.warning("Optional column is missing", column="parental_education")
```

### Custom logger name

The logger accepts a custom name if you need a separate logger instance:

```python
from src.utils.logger import get_logger

logger = get_logger("custom_logger")
logger.info("Training started", run_id="example-run")
```

### Direct manager configuration

Use `ProjectLoggerManager` when you need full control over the logger name or YAML path:

```python
from pathlib import Path

from src.utils.logger import ProjectLoggerManager

manager = ProjectLoggerManager(
    logger_name="student_performance_indicator",
    config_path=Path("config/logger_config.yaml"),
)
logger = manager.logger
logger.info("Pipeline started", run_id="example-run")
```

## Structured logging patterns

Every log method accepts a message plus keyword arguments. Those arguments are merged into the `extra` payload before the record is emitted:

```python
logger.info(
    "Student data loaded",
    extra={"source": "artifacts/train.csv"},
    row_count=1200,
)
```

When the same key exists in both `extra` and direct keyword arguments, the direct keyword argument wins because `extra_dict.update(kwargs)` is applied last.

Use the standard log levels like this:

```python
logger.debug("Detailed diagnostic information")
logger.info("Normal application progress")
logger.warning("Recoverable or unexpected condition")
logger.error("Operation failed")
logger.exception("Operation failed with traceback")
logger.critical("Severe application failure")
```

Inside an exception handler, prefer `logger.exception()` to emit the active traceback automatically:

```python
try:
    result = run_prediction(data)
except ValueError:
    logger.exception("Prediction failed", operation="run_prediction")
```

## JSON log payload

`JsonFormatter` produces one JSON object per log event. It includes the standard record metadata plus any custom structured keys.

The following fields are always emitted when available:

| Field | Description |
|---|---|
| `timestamp` | Log creation time formatted by Python's logging formatter |
| `level` | Log level such as `INFO`, `ERROR`, or `CRITICAL` |
| `logger` | Logger name |
| `message` | Rendered message text |
| `exception` | Structured exception summary if `exc_info` is present |
| `stack_info` | Stack trace text if requested |
| custom fields | Any extra attributes passed as keyword arguments |

`exception` is a dictionary with this structure:

```python
{
    "type": exc_type.__name__,
    "message": str(exc_value),
    "file": last_frame.filename,
    "line_no": last_frame.lineno,
    "function": last_frame.name,
}
```

This is built from the last frame in `traceback.extract_tb(exc_tb)`, so it captures the terminal frame in the traceback rather than the full stack trace object.

Example JSON payload:

```json
{
  "timestamp": "2026-09-04 12:00:00,000",
  "level": "INFO",
  "logger": "student_performance_indicator",
  "message": "Student data loaded",
  "source": "artifacts/train.csv",
  "row_count": 1200
}
```

Any value that cannot be serialized as JSON is converted using `json.dumps(..., default=str)`, so log payloads remain valid JSON even for non-standard objects.

## Operational guidance

- Use `get_logger()` instead of instantiating a separate logging configuration in application code.
- Keep messages concise and place diagnostic values in keyword arguments.
- Never log secrets such as passwords, tokens, or API keys.
- Use `logger.exception()` inside `except` blocks when traceback details matter.
- Review `artifacts/logs/app.log` when troubleshooting local pipeline failures.
- Adjust log levels and handlers in `config/logger_config.yaml`, not in individual call sites.

## Testing

The logger behavior is validated by the focused test suite:

```bash
pytest tests/test_logger.py -v
```

These tests cover logger creation, JSON serialization, metadata propagation, and exception payload generation.

**Last updated**: 2026-09-04
**Maintainer**: Adamu Joseph Ohigwere
