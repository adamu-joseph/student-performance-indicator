"""Project logger configuration and utilities.

This module provides a reusable, object-oriented logging setup for the
student performance indicator project. It reads a YAML-based configuration
file and exposes a configured logger instance for the rest of the codebase.
"""

from __future__ import annotations

import json
import logging as std_logging
import logging.config as logging_config
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "logger_config.yaml"


class JsonFormatter(std_logging.Formatter):
    """Format log records as JSON strings."""

    def format(self, record: std_logging.LogRecord) -> str:
        """Convert a log record into a JSON payload."""
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(payload, default=str)


class ProjectLogger:
    """Object-oriented manager for the application's logger."""

    def __init__(
        self,
        logger_name: str = "student_performance_indicator",
        config_path: Path | str | None = None,
    ) -> None:
        """Initialize the project logger manager.

        Args:
            logger_name: Name given to the logger.
            config_path: Optional path to the YAML configuration file.
        """
        self.logger_name = logger_name
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        self.mylogger = self._configure_logger()

    def _load_config(self) -> dict[str, Any]:
        """Load logger configuration from the YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Logger config file not found: {self.config_path}")

        try:
            with self.config_path.open("r", encoding="utf-8") as config_file:
                config = yaml.safe_load(config_file) or {}

        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing logger config file: {e}") from e

        print(f"[INFO] Logger configuration loaded from {self.config_path}")
        return config

    def _validate_config(self, config: dict[str, Any]) -> None:
        """Validate the logger configuration."""
        if not isinstance(config, dict):
            raise TypeError("Logger config must be a dictionary")

        if not config.get("handlers"):
            raise ValueError("Logger config must define at least one handler")

        if not config.get("formatters"):
            raise ValueError("Logger config must define at least one formatter")

        if not config.get("loggers"):
            raise ValueError("Logger config must define at least one logger")

        if not config.get("root"):
            raise ValueError("Logger config must define a root logger")

        if not config.get("version"):
            raise ValueError("Logger config must specify version a version number")

        print("[INFO] Logger configuration validated successfully")

    def _configure_logger(self) -> std_logging.Logger:
        """Configure logger using dictConfig from YAML."""
        config = self._load_config()
        self._validate_config(config)

        try:
            logging_config.dictConfig(config)
            logger = std_logging.getLogger(self.logger_name)
        except Exception as e:
            raise ValueError(f"Error configuring logger: {e}") from e

        print(f"[INFO] Logger '{self.logger_name}' configured successfully")
        return logger

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an informational message and include structured kwargs in payload."""
        extra = kwargs.pop("extra", {})
        extra = {**extra, **kwargs}
        self.mylogger.info(message, extra=extra)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message and include structured kwargs in payload."""
        extra = kwargs.pop("extra", {})
        extra = {**extra, **kwargs}
        self.mylogger.warning(message, extra=extra)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message and include structured kwargs in payload."""
        extra = kwargs.pop("extra", {})
        extra = {**extra, **kwargs}
        self.mylogger.error(message, extra=extra)

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log an exception message with traceback and structured kwargs."""
        extra = kwargs.pop("extra", {})
        extra = {**extra, **kwargs}
        self.mylogger.exception(message, extra=extra)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log a critical message and include structured kwargs in payload."""
        extra = kwargs.pop("extra", {})
        extra = {**extra, **kwargs}
        self.mylogger.critical(message, extra=extra)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message and include structured kwargs in payload."""
        extra = kwargs.pop("extra", {})
        extra = {**extra, **kwargs}
        self.mylogger.debug(message, extra=extra)


def get_logger(name: str = "student_performance_indicator") -> ProjectLogger:
    """Return a configured project logger instance."""
    return ProjectLogger(logger_name=name)


logging = get_logger()

__all__ = ["JsonFormatter", "ProjectLogger", "get_logger", "logging"]
