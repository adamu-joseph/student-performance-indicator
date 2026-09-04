"""Project logger configuration and utilities.

This module provides a reusable, structured logging setup for the
student performance indicator project. It reads a YAML-based configuration
file and exposes a configured logger instance.
"""

from __future__ import annotations

# The project logger intentionally extends Logger methods with structured fields.
# pyright: reportIncompatibleMethodOverride=false
import json
import logging
import logging.config
import traceback
from pathlib import Path
from typing import Any, cast

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "logger_config.yaml"


class JsonFormatter(logging.Formatter):
    """Format log records as JSON strings."""

    # Standard LogRecord attributes that should not be duplicated
    # as custom structured fields.
    STANDARD_LOG_RECORD_FIELDS = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "taskName",
        "message",
        "asctime",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Convert a log record into a JSON payload."""

        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            # payload["exception"] = self.formatException(record.exc_info)
            exc_type, exc_value, exc_tb = record.exc_info

            tb = traceback.extract_tb(exc_tb)
            last_frame = tb[-1] if tb else None

            payload["exception"] = {
                "type": exc_type.__name__ if exc_type else None,
                "message": str(exc_value) if exc_value else None,
                "file": last_frame.filename if last_frame else None,
                "line_no": last_frame.lineno if last_frame else None,
                "function": last_frame.name if last_frame else None,
            }

        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)

        # Add custom structured logging fields such as:
        # user_id=42, student_id=123, prediction=85.5, etc.
        for key, value in record.__dict__.items():
            if key not in self.STANDARD_LOG_RECORD_FIELDS:
                payload[key] = value

        return json.dumps(payload, default=str)


class ProjectLogger(logging.Logger):
    """Application logger supporting structured keyword arguments."""

    def _log_structured(
        self,
        level: int,
        message: object,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> None:
        """Log a message while converting custom kwargs into ``extra``."""

        extra = kwargs.pop("extra", None)

        if extra is None:
            extra_dict: dict[str, Any] = {}
        elif isinstance(extra, dict):
            extra_dict = dict(extra)
        else:
            raise TypeError("extra must be a dictionary")

        # Extract standard logging keyword arguments.
        exc_info = kwargs.pop("exc_info", None)
        stack_info = kwargs.pop("stack_info", False)
        stacklevel = kwargs.pop("stacklevel", 1)

        # Everything remaining becomes structured log data.
        extra_dict.update(kwargs)

        try:
            super()._log(
                level,
                message,
                args,
                exc_info=exc_info,
                extra=extra_dict,
                stack_info=stack_info,
                stacklevel=stacklevel,
            )
        except Exception as error:
            print(f"[CRITICAL] Failed to log message: {error}")
            raise RuntimeError(f"Failed to log message: {error}") from error

    def debug(  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        message: object,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Log a DEBUG message with optional structured fields."""
        self._log_structured(logging.DEBUG, message, args, kwargs)

    def info(  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        message: object,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Log an INFO message with optional structured fields."""
        self._log_structured(logging.INFO, message, args, kwargs)

    def warning(  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        message: object,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Log a WARNING message with optional structured fields."""
        self._log_structured(logging.WARNING, message, args, kwargs)

    def error(  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        message: object,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Log an ERROR message with optional structured fields."""
        self._log_structured(logging.ERROR, message, args, kwargs)

    def exception(  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        message: object,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Log an ERROR message with exception information."""

        if "exc_info" not in kwargs:
            kwargs["exc_info"] = True

        self._log_structured(logging.ERROR, message, args, kwargs)

    def critical(  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        message: object,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Log a CRITICAL message with optional structured fields."""
        self._log_structured(logging.CRITICAL, message, args, kwargs)


# Make logging.getLogger() create ProjectLogger instances.
logging.setLoggerClass(ProjectLogger)


class ProjectLoggerManager:
    """Manage configuration of the application logger."""

    def __init__(
        self,
        logger_name: str = "student_performance_indicator",
        config_path: Path | str | None = None,
    ) -> None:
        """Initialize the logger manager.

        Args:
            logger_name: Name given to the logger.
            config_path: Optional path to the YAML configuration file.
        """
        self.logger_name = logger_name
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        self.logger = self._configure_logger()

    def _load_config(self) -> dict[str, Any]:
        """Load logger configuration from the YAML file."""

        if not self.config_path.exists():
            raise FileNotFoundError(f"Logger config file not found: {self.config_path}")

        try:
            with self.config_path.open("r", encoding="utf-8") as config_file:
                config = yaml.safe_load(config_file) or {}
        except yaml.YAMLError as error:
            raise ValueError(f"Error parsing logger config file: {error}") from error

        if not isinstance(config, dict):
            raise TypeError("Logger config must be a dictionary")

        print(f"[INFO] Loaded logger config from {self.config_path}")
        return config

    def _validate_config(self, config: dict[str, Any]) -> None:
        """Validate the logger configuration."""

        if not config.get("handlers"):
            raise ValueError("Logger config must define at least one handler")

        if not config.get("formatters"):
            raise ValueError("Logger config must define at least one formatter")

        if not config.get("loggers"):
            raise ValueError("Logger config must define at least one logger")

        if not config.get("root"):
            raise ValueError("Logger config must define a root logger")

        if "version" not in config:
            raise ValueError("Logger config must specify a version number")

        # Ensure the directory for the file handler exists.
        file_handler = config.get("handlers", {}).get("file", {})

        if file_handler and "filename" in file_handler:
            log_file_path = Path(file_handler["filename"])
            log_file_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        else:
            raise ValueError(
                "Logger config must define a 'file' handler with a 'filename'"
            )

        print("[INFO] Logger configuration validated successfully.")

    def _configure_logger(self) -> ProjectLogger:
        """Configure and return the application logger."""

        config = self._load_config()
        self._validate_config(config)

        try:
            logging.config.dictConfig(config)
            logger = logging.getLogger(self.logger_name)
        except Exception as error:
            raise ValueError(f"Error configuring logger: {error}") from error

        if not isinstance(logger, logging.Logger):
            raise TypeError(f"Expected Logger, got {type(logger).__name__}")

        print(f"[INFO] Logger '{self.logger_name}' configured successfully.")
        return cast(ProjectLogger, logger)


def get_logger(
    name: str = "student_performance_indicator",
) -> ProjectLogger:
    """Return the configured project logger."""

    print(f"[INFO] Retrieving logger '{name}'")
    manager = ProjectLoggerManager(logger_name=name)
    return manager.logger


__all__ = [
    "JsonFormatter",
    "ProjectLogger",
    "ProjectLoggerManager",
    "get_logger",
]
