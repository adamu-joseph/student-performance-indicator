"""Data validation checks for schema consistency, missing values, and data quality."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

import pandas as pd
import yaml

from utils.logger import get_logger

PROJECT_ROOT = Path(__file__).resolve().parents[2]
logger = get_logger()


@dataclass(frozen=True)
class DataValidationConfig:
    """Configuration for dataset validation rules and thresholds."""

    output_dir: Path
    target_column: str
    numeric_columns: tuple[str, ...]
    categorical_columns: tuple[str, ...]
    expected_categories: dict[str, tuple[str, ...]]
    max_missing_pct: float
    min_row_count: int
    numeric_ranges: dict[str, tuple[float, float]]

    required: ClassVar[frozenset[str]] = frozenset({"output_dir"})

    @classmethod
    def from_yaml(cls, config_path: Path | str) -> DataValidationConfig:
        """Load and validate data validation settings from YAML.

        Args:
            config_path: Path to the YAML configuration file.

        Returns:
            A validated DataValidationConfig instance.
        """

        path = Path(config_path)
        if not path.exists():
            logger.error("Validation config not found", path=str(path))
            raise FileNotFoundError(f"Validation config not found: {path}")

        try:
            with path.open("r", encoding="utf-8") as config_file:
                raw = yaml.safe_load(config_file) or {}
        except yaml.YAMLError as error:
            logger.error("Failed to parse validation YAML", path=str(path))
            raise ValueError(f"Invalid validation YAML: {path}") from error

        config = raw.get("config", {})
        schema = raw.get("schema", {})
        thresholds = raw.get("thresholds", {})

        if not isinstance(config, dict):
            raise ValueError("Validation config section must be a mapping")

        missing = cls.required.difference(config)
        if missing:
            logger.error("Missing validation config keys", missing=sorted(missing))
            raise ValueError(f"Missing validation config keys: {sorted(missing)}")

        expected_cats = {
            key: tuple(values)
            for key, values in schema.get("expected_categories", {}).items()
        }

        ranges = {
            key: (float(bounds[0]), float(bounds[1]))
            for key, bounds in thresholds.get("numeric_ranges", {}).items()
        }

        return cls(
            output_dir=_resolve_path(config["output_dir"]),
            target_column=str(schema.get("target_column")),
            numeric_columns=tuple(schema.get("numeric_columns", [])),
            categorical_columns=tuple(schema.get("categorical_columns", [])),
            expected_categories=expected_cats,
            max_missing_pct=float(thresholds.get("max_missing_pct")),
            min_row_count=int(thresholds.get("min_row_count")),
            numeric_ranges=ranges,
        )


def _resolve_path(value: str | Path) -> Path:
    """Resolve relative configuration paths from the project root."""

    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


class DataValidation:
    """Validate dataset schema, missing values, ranges, and data quality."""

    def __init__(self, config_path: Path | str) -> None:
        """Initialize validation from the configured YAML file.

        Args:
            config_path: Path to the YAML configuration file.
        """

        self.config = DataValidationConfig.from_yaml(config_path)

    def validate(self, data: pd.DataFrame) -> dict[str, Any]:
        """Run all validation checks and return a consolidated report.

        Args:
            data: The dataset to validate.

        Returns:
            A dictionary containing results for each validation check and
            an overall ``passed`` flag.
        """

        logger.info("Started data validation...")

        report: dict[str, Any] = {
            "row_count": self._validate_row_count(data),
            "schema": self._validate_schema(data),
            "missing_values": self._validate_missing(data),
            "numeric_ranges": self._validate_ranges(data),
            "categorical_values": self._validate_categories(data),
            "target": self._validate_target(data),
        }

        report["passed"] = all(
            check.get("passed", False)
            for check in report.values()
            if isinstance(check, dict) and "passed" in check
        )

        status = "passed" if report["passed"] else "failed"
        logger.info("Data validation complete", status=status)
        return report

    def _validate_row_count(self, data: pd.DataFrame) -> dict[str, Any]:
        """Check that the dataset meets the minimum row count."""

        count = len(data)
        passed = count >= self.config.min_row_count
        result = {
            "passed": passed,
            "row_count": count,
            "minimum_required": self.config.min_row_count,
        }
        if not passed:
            logger.warning(
                "Insufficient rows",
                row_count=count,
                minimum=self.config.min_row_count,
            )
        return result

    def _validate_schema(self, data: pd.DataFrame) -> dict[str, Any]:
        """Check that expected columns exist and data types are correct."""

        expected = (
            set(self.config.numeric_columns)
            | set(self.config.categorical_columns)
            | {self.config.target_column}
        )
        actual = set(data.columns)

        missing_cols = sorted(expected - actual)
        extra_cols = sorted(actual - expected)

        type_issues = []
        for col in self.config.numeric_columns:
            if col in actual and not pd.api.types.is_numeric_dtype(data[col]):
                type_issues.append(f"{col}: expected numeric, got {data[col].dtype}")

        passed = len(missing_cols) == 0 and len(type_issues) == 0
        result = {
            "passed": passed,
            "missing_columns": missing_cols,
            "extra_columns": extra_cols,
            "type_issues": type_issues,
        }
        if not passed:
            logger.warning("Schema validation failed", issues=result)
        return result

    def _validate_missing(self, data: pd.DataFrame) -> dict[str, Any]:
        """Check missing-value percentages against the configured threshold."""

        missing_pct = data.isna().mean() * 100
        columns_with_missing = {
            col: round(float(pct), 2) for col, pct in missing_pct.items() if pct > 0
        }
        threshold_violations = {
            col: pct
            for col, pct in columns_with_missing.items()
            if pct > self.config.max_missing_pct
        }

        passed = len(threshold_violations) == 0
        result = {
            "passed": passed,
            "columns_with_missing": columns_with_missing,
            "threshold_violations": threshold_violations,
            "max_allowed_pct": self.config.max_missing_pct,
        }
        if not passed:
            logger.warning(
                "Missing value threshold exceeded", violations=threshold_violations
            )
        return result

    def _validate_ranges(self, data: pd.DataFrame) -> dict[str, Any]:
        """Check that numeric columns fall within expected ranges."""

        violations = {}
        for col, (low, high) in self.config.numeric_ranges.items():
            if col not in data.columns:
                continue
            col_min = float(data[col].min())
            col_max = float(data[col].max())
            if col_min < low or col_max > high:
                violations[col] = {
                    "expected": [low, high],
                    "actual": [col_min, col_max],
                }

        passed = len(violations) == 0
        result = {"passed": passed, "violations": violations}
        if not passed:
            logger.warning("Numeric range violations found", violations=violations)
        return result

    def _validate_categories(self, data: pd.DataFrame) -> dict[str, Any]:
        """Check that categorical columns contain only expected values."""

        violations = {}
        for col, expected_values in self.config.expected_categories.items():
            if col not in data.columns:
                continue
            actual = set(data[col].dropna().unique())
            unexpected = sorted(actual - set(expected_values))
            if unexpected:
                violations[col] = {
                    "unexpected_values": unexpected,
                    "expected_values": list(expected_values),
                }

        passed = len(violations) == 0
        result = {"passed": passed, "violations": violations}
        if not passed:
            logger.warning("Unexpected categorical values", violations=violations)
        return result

    def _validate_target(self, data: pd.DataFrame) -> dict[str, Any]:
        """Validate that the target column exists, is numeric, and complete."""

        target = self.config.target_column
        if target not in data.columns:
            logger.error("Target column missing from dataset", target=target)
            return {"passed": False, "error": f"Target column '{target}' not found"}

        missing_count = int(data[target].isna().sum())
        is_numeric = bool(pd.api.types.is_numeric_dtype(data[target]))
        passed = missing_count == 0 and is_numeric

        result: dict[str, Any] = {
            "passed": passed,
            "missing_count": missing_count,
            "is_numeric": is_numeric,
        }
        if is_numeric:
            result["min"] = float(data[target].min())
            result["max"] = float(data[target].max())

        if not passed:
            logger.warning("Target validation failed", **result)
        return result

    def save_report(self, report: dict[str, Any]) -> Path:
        """Persist the validation report as JSON.

        Args:
            report: The validation report dictionary.

        Returns:
            Path to the saved report file.
        """

        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        report_path = self.config.output_dir / "validation_report.json"
        report_path.write_text(
            json.dumps(report, indent=2, default=str), encoding="utf-8"
        )
        logger.info("Validation report saved", path=str(report_path))
        return report_path


__all__ = ["DataValidation", "DataValidationConfig"]
