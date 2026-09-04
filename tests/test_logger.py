"""Tests for the project logger."""

import json
import logging
from pathlib import Path

from src.utils.logger import get_logger


def test_project_logger_returns_configured_logger() -> None:
    """The logger should be created with a valid project name and handler set."""
    logger = get_logger()

    assert isinstance(logger, logging.Logger)
    assert logger.name == "student_performance_indicator"
    assert logger.handlers


# Fixed the test function name to be more descriptive and added a docstring for clarity.
def test_project_logger_writes_json_log_entry() -> None:
    """The logger should write JSON-formatted log records to file output."""

    logger = get_logger()

    log_file = Path("artifacts/logs/app.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info("logger test message", user_id=42)

    with log_file.open("r", encoding="utf-8") as log_handle:
        # contents = log_handle.read().strip()
        payload = json.load(log_handle)

    assert payload["level"] == "INFO"
    assert payload["logger"] == "student_performance_indicator"
    assert payload["message"] == "logger test message"
    assert payload["user_id"] == 42


def test_project_exception_logging() -> None:
    """The logger should log exceptions with structured information."""

    logger = get_logger()
    try:
        raise ValueError("Test exception for logging")
    except ValueError:
        logger.error("An exception occurred", exc_info=True, user_id=99)

    log_file = Path("artifacts/logs/app.log")
    with log_file.open("r", encoding="utf-8") as log_handle:
        payload = json.load(log_handle)

    assert payload["level"] == "ERROR"
    assert payload["logger"] == "student_performance_indicator"
    assert payload["message"] == "An exception occurred"
    assert "exception" in payload
    assert "ValueError: Test exception for logging" in payload["exception"]
    assert payload["user_id"] == 99
