# Logging Implementation

This document describes the logging system used by the Student Performance Indicator project.

## Components

| File | Responsibility |
|---|---|
| `src/utils/logger.py` | Logger manager, JSON formatter, and public logging API |
| `config/logger_config.yaml` | Logger levels, handlers, destinations, and formatter configuration |
| `artifacts/logs/app.log` | File destination for application logs |

The default logger name is `student_performance_indicator`.

## Configuration

`ProjectLogger` loads `config/logger_config.yaml` from the project root and applies it with Python's `logging.config.dictConfig`.

The configuration must contain a version, formatter, handler, named logger, and root logger. Invalid configuration raises an exception during initialization.

The current handlers are:

| Handler | Level | Destination | Format |
|---|---|---|---|
| `console` | `INFO` | Standard output | JSON |
| `file` | `INFO` | `artifacts/logs/app.log` | JSON |

The project and root loggers are configured at `INFO`. Consequently, `DEBUG` messages are filtered with the current configuration even though the `debug` method is available in the Python API.

## Using the logger

### Module-level logger

Use the configured module-level logger for normal application code:

```python
from src.utils.logger import logging

logging.info("Data ingestion started")
logging.warning("Optional column is missing", column="parental_education")
```

### `get_logger`

Use `get_logger` when a specific logger name is required:

```python
from src.utils.logger import get_logger

logger = get_logger("student_performance_indicator")
logger.info("Training started")
```

### `ProjectLogger`

`ProjectLogger` provides an object-oriented wrapper and accepts an optional configuration path:

```python
from pathlib import Path

from src.utils.logger import ProjectLogger

logger = ProjectLogger(
    logger_name="student_performance_indicator",
    config_path=Path("config/logger_config.yaml"),
)
logger.info("Pipeline started", run_id="example-run")
```

## Log levels

The wrapper provides the standard logging levels:

```python
logger.debug("Detailed diagnostic information")
logger.info("Normal application progress")
logger.warning("Recoverable or unexpected condition")
logger.error("Operation failed")
logger.exception("Operation failed with traceback")
logger.critical("Severe application failure")
```

Every method accepts a message and keyword arguments. The keyword arguments are merged into the `extra` mapping passed to the underlying Python logger:

```python
logger.info(
    "Student data loaded",
    extra={"source": "artifacts/train.csv"},
    row_count=1200,
)
```

If a key is present in both `extra` and direct keyword arguments, the direct keyword argument takes precedence.

Use `exception` inside an exception handler to include the active traceback:

```python
try:
    result = run_prediction(data)
except ValueError:
    logger.exception("Prediction failed", operation="run_prediction")
```

## JSON format

`JsonFormatter` serializes the following record fields:

| Field | Description |
|---|---|
| `timestamp` | Formatted record creation time |
| `level` | Level name, such as `INFO` or `ERROR` |
| `logger` | Logger name |
| `module` | Module that emitted the record |
| `function` | Function that emitted the record |
| `line` | Source line that emitted the record |
| `message` | Rendered log message |
| `exception` | Formatted traceback when exception information exists |
| `stack_info` | Stack information when requested |

Example output:

```json
{
  "timestamp": "2026-09-04 12:00:00,000",
  "level": "INFO",
  "logger": "student_performance_indicator",
  "module": "data_ingestion",
  "function": "ingest_data",
  "line": 42,
  "message": "Student data loaded"
}
```

The formatter uses `json.dumps(..., default=str)` so values that are not natively JSON serializable can be represented as strings.

The wrapper passes keyword arguments to the log record as `extra` attributes. The current formatter emits the fixed fields listed above and does not automatically copy arbitrary `extra` attributes into the JSON payload. Extend `JsonFormatter.format` if custom fields must be serialized in the log output.

## Operational guidance

- Use the project logger instead of creating separate logger configurations.
- Keep messages concise and place useful context in keyword fields.
- Never log passwords, tokens, API keys, or other sensitive values.
- Use `exception` when a traceback is needed for diagnosis.
- Review `artifacts/logs/app.log` when investigating local pipeline failures.
- Change levels and destinations in `config/logger_config.yaml`, not at individual call sites.

## Testing

Run the focused logger tests with:

```bash
pytest tests/test_logger.py -v
```

These tests verify logger creation, handler configuration, JSON output, metadata, and exception serialization. Run the complete suite after changing shared logging behavior:

```bash
pytest
```
