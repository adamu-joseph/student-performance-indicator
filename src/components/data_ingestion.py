"""Data ingestion, cleaning, labeling, and dataset versioning."""

# Import required modules
from __future__ import annotations

import hashlib
import json
import re
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

import pandas as pd
import requests
import yaml

from utils.logger import get_logger

PROJECT_ROOT = Path(__file__).resolve().parents[2]
logger = get_logger()


@dataclass(frozen=True)
class DataIngestionConfig:
    """Configuration required to acquire and version a dataset."""

    # Define variables
    source: str
    input_path: Path
    kaggle_url: str
    output_dir: Path
    dataset_version: str
    target_column: str
    supported_file_types: tuple[str, ...]
    dtype_target: str
    request_timeout: int = 30
    required: ClassVar[frozenset[str]] = frozenset(
        {
            "source",
            "input_path",
            "kaggle_url",
            "output_dir",
            "dataset_version",
        }
    )

    @classmethod
    def from_yaml(cls, config_path: Path | str) -> DataIngestionConfig:
        """Load and validate ingestion settings from from the config folder.

        "Args:
            config_path: Path to the YAML configuration file.

        Returns:
            An instance of DataIngestionConfig with validated settings.
        """

        path = Path(config_path)
        # Validate path exists
        if not path.exists():
            logger.error("Data ingestion configuration file not found", path=str(path))
            raise FileNotFoundError(
                f"Data ingestion configuration file not found: {path}"
            )

        # Load the config file
        try:
            with path.open("r", encoding="utf-8") as config_file:
                raw_config: dict[str, Any] = yaml.safe_load(config_file) or {}

        except yaml.YAMLError as error:
            logger.error(
                "Failed to parse data ingestion YAML configuration", path=str(path)
            )
            raise ValueError(f"Invalid data ingestion file.: {path}") from error

        # Get the required keys from the file
        try:
            values = raw_config.get("config")
            data = raw_config.get("data")
        except KeyError as exc:
            logger.error(
                "Could not find required keys ['config', 'data'] in config file"
            )
            raise KeyError(
                "Could not find required keys ['config', 'data'] in config file"
            ) from exc

        if not isinstance(values, dict) or not isinstance(data, dict):
            raise ValueError("Expected 'config' and 'data' to be mappings")

        # confirm keys exists and validate type
        if not values or not data:
            logger.error(
                "Empty values from 'config' or 'data' key in the data ingestion configuration."
            )
            raise ValueError(
                "Empty values from 'config' or 'data' key in the data ingestion configuration."
            )

        # validate data from the config file
        configured_types: list = values.get("supported_file_types", [])
        missing = cls.required.difference(values)
        if missing:
            logger.error(
                "Missing data ingestion configuration values", missing=sorted(missing)
            )
            raise ValueError(
                f"Missing data ingestion configuration values: {sorted(missing)}"
            )

        source = str(values["source"]).lower().strip()
        if source not in {"device", "kaggle"}:
            raise ValueError(
                "Data ingestion source must be either 'device' or 'kaggle'"
            )

        supported_types = tuple(
            str(file_type).lower() for file_type in configured_types
        )

        if not data["target_column"]:
            logger.error("Missing 'target_column' for data ingestion configuration")
            raise ValueError("Missing 'target_column' in data ingestion configuration")
        if not data["type"]:
            logger.error("Missing 'dtype_target' for data ingestion configuration")
            raise ValueError("Missing 'dtype_target' in data ingestion configuration")

        # Return the configuration data
        return cls(
            source=source,
            input_path=_resolve_path(values["input_path"]),
            kaggle_url=str(values["kaggle_url"]),
            output_dir=_resolve_path(values["output_dir"]),
            dataset_version=str(values["dataset_version"]),
            target_column=str(values["data"]["target_column"]),
            supported_file_types=supported_types,
            request_timeout=int(values.get("request_timeout", 30)),
            dtype_target=values["data"]["type"],
        )


def _resolve_path(value: str | Path) -> Path:
    """Resolve relative configuration paths from the project root."""

    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


class DataIngestion:
    """Acquire, prepare, and persist versioned student performance data."""

    def __init__(self, config_path: Path | str) -> None:
        """Initialize ingestion from the configured YAML file.

        Args:
            config_path: Path to the YAML configuration file.

        Returns:
            None
        """

        # Acquire the validated configuration
        self.config = DataIngestionConfig.from_yaml(config_path)

    def acquire_data(self) -> pd.DataFrame:
        """Get the dataset from device path or Kaggle

        Returns:
            The acquired dataset as pd.Dataframe.
        """

        # Get the dataset from device
        if self.config.source == "device":
            input_path = self.config.input_path

            # confirm path exists
            if not input_path.exists():
                logger.error(f"Configured input dataset does not exist: {input_path}")
                raise FileNotFoundError(
                    f"Configured input dataset does not exist: {input_path}"
                )

            # confirm dataset file is a supported file type
            if input_path.suffix.lower() not in self.config.supported_file_types:
                logger.error(
                    f"Unsupported input file type: {input_path.suffix.lower()}"
                )
                raise ValueError(
                    f"Unsupported input file type: {input_path.suffix.lower()}"
                )

            # Load dataset into pandas dataframe
            logger.info("Loading dataset from device", input_path=str(input_path))
            return pd.read_csv(input_path)

        # Download the dataset from kaggle
        logger.info("Downloading dataset from Kaggle", url=self.config.kaggle_url)
        with tempfile.TemporaryDirectory() as temporary_directory:
            download_path = Path(temporary_directory) / "dataset.download"
            response = requests.get(
                self._kaggle_download_url(), timeout=self.config.request_timeout
            )
            # raise error if download not successful
            response.raise_for_status()
            download_path.write_bytes(response.content)

            # Return pandas dataframe
            return self._read_downloaded_dataset(download_path)

    def clean_and_label(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean records

        Args:
            data: The raw dataset (pd.DataFrame) to clean and label.

        Returns:
            A cleaned and labeled pd.DataFrame."""

        cleaned = data.copy()
        cleaned.columns = [str(column).strip() for column in cleaned.columns]
        cleaned = cleaned.dropna(how="all").drop_duplicates().reset_index(drop=True)

        if self.config.target_column not in cleaned.columns:
            logger.error(f"Dataset must contain '{self.config.target_column}'")
            raise ValueError(f"Dataset must contain '{self.config.target_column}'")

        if isinstance(self.config.dtype_target, int):
            logger.info(
                f"Converting target column '{self.config.target_column}' to numeric values"
            )

            try:
                cleaned[self.config.target_column] = pd.to_numeric(
                    cleaned[self.config.target_column], errors="coerce"
                )
            except ValueError as exc:
                raise ValueError(
                    f"Target column '{self.config.target_column}' contains an unconvertable data field"
                ) from exc

        cleaned = cleaned.dropna(subset=[self.config.target_column]).copy()
        for column in cleaned.select_dtypes(include="object").columns:
            cleaned[column] = cleaned[column].astype(str).str.strip()

        if cleaned.empty:
            logger.error("Dataset contains no valid records after cleaning")
            raise ValueError("Dataset contains no valid records after cleaning")

        return cleaned

    def save_versioned_dataset(self, data: pd.DataFrame) -> Path:
        """Write the prepared CSV and its JSON metadata manifest."""

        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        version = self.config.dataset_version
        dataset_path = self.config.output_dir / f"student_performance_v{version}.csv"

        # write to file
        data.to_csv(dataset_path, index=False)

        manifest = {
            "dataset_version": version,
            "source": self.config.source,
            "target_column": self.config.target_column,
            "row_count": len(data),
            "columns": list(data.columns),
            "sha256": _sha256(dataset_path),
        }

        manifest_path = self.config.output_dir / f"student_performance_v{version}.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        logger.info(
            "Versioned dataset saved",
            dataset_path=str(dataset_path),
            row_count=len(data),
        )

        return dataset_path

    def _kaggle_download_url(self) -> str:
        """Convert a Kaggle dataset page URL to its API download URL."""

        # get url
        match = re.search(
            r"kaggle\.com/datasets/([^/]+/[^/?#]+)", self.config.kaggle_url
        )
        return (
            f"https://www.kaggle.com/api/v1/datasets/download/{match.group(1)}"
            if match
            else self.config.kaggle_url
        )

    @staticmethod
    def _read_downloaded_dataset(download_path: Path) -> pd.DataFrame:
        """Read the first CSV from a downloaded CSV or ZIP archive."""

        logger.info(
            "Reading downloaded Kaggle dataset", download_path=str(download_path)
        )
        if zipfile.is_zipfile(download_path):
            with zipfile.ZipFile(download_path) as archive:
                # get the csv file inside the zip file
                csv_names = [
                    name for name in archive.namelist() if name.lower().endswith(".csv")
                ]
                if not csv_names:
                    logger.error(
                        "Downloaded kaggle archive does not contain a CSV file"
                    )
                    raise ValueError(
                        "Downloaded Kaggle archive does not contain a CSV file"
                    )

                # Read the csv file as pandas dataframe
                try:
                    with archive.open(csv_names[0]) as csv_file:
                        return pd.read_csv(csv_file)
                except Exception as error:
                    logger.exception("Could not read downloaded kaggle dataset")
                    raise Exception(
                        f"Could not read downloaded Kaggle dataset, {error}"
                    ) from error

        if download_path.suffix.lower() != ".csv":
            logger.error("Downloaded kaggle dataset file is not a CSV")
            raise ValueError("Downloaded Kaggle dataset file is not a CSV")

        # Read normally if the downloaded path is not a csv file
        try:
            return pd.read_csv(download_path)
        except Exception as error:
            raise Exception("Could not read downloaded kaggle dataset") from error


def _sha256(path: Path) -> str:
    """Return the SHA-256 digest of a file."""

    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = ["DataIngestion", "DataIngestionConfig"]
