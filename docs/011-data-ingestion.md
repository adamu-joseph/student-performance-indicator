# Data Ingestion

This document describes how the Student Performance Indicator project acquires, validates, cleans, and versions the raw dataset before it is passed to downstream transformation and training stages.

## Overview

The data ingestion workflow is implemented in `src/components/data_ingestion.py`. It is responsible for the following:

- loading a dataset from either a local device path or a Kaggle dataset URL
- validating the dataset configuration from YAML
- normalizing column names and removing unusable rows
- ensuring the configured target column exists and is valid
- writing a versioned CSV file plus a manifest JSON file to the processed data folder

The ingestion component acts as the boundary between raw data and the ML pipeline. It does not perform feature engineering; it only prepares a clean, versioned, useable dataset for later processing.

---

## Components

| File | Responsibility |
|---|---|
| `src/components/data_ingestion.py` | Dataset acquisition, validation, cleaning, and versioning |
| `config/data_ingestion_config.yaml` | Runtime configuration for data source and versioning |
| `artifacts/data/processed/` | Versioned processed datasets and manifests |

---

## Configuration model

The project uses a dataclass-based configuration object named `DataIngestionConfig`.

### Required settings

The configuration must provide:

- `source`
- `input_path`
- `kaggle_url`
- `output_dir`
- `dataset_version`

---

### Validation rules

`DataIngestionConfig.from_yaml()` validates the config before it is used:

- the YAML file must exist and parse successfully
- `config.source` must be either `device` or `kaggle`
- the dataset config must contain the required keys
- `data.target_column` must be present and non-empty
- `data.type` must be present and non-empty
- the file type list is normalized to lowercase values
- all relative paths are resolved from the project root

The helper `_resolve_path()` makes config paths project-root relative when the YAML uses a relative path.

---

## Data source modes

The ingestion component supports two acquisition modes.

### 1. Local device mode

When `source: device` is configured, the system reads the dataset directly from `input_path`.

Required behavior:

- the file must exist
- the file extension must be supported
- the current support list is `.csv`
- the file is loaded with `pd.read_csv(input_path)`

If the path is missing or the extension is unsupported, the component raises `FileNotFoundError` or `ValueError` respectively.

### 2. Kaggle mode

When `source: kaggle` is configured, the system attempts to download the dataset from the URL in `kaggle_url`.

The implementation:

- extracts the dataset slug from the Kaggle URL using a regex pattern
- rewrites it to the Kaggle API download URL
- requests the file with `requests.get(..., timeout=...)`
- saves the raw download to a temporary file
- reads either a CSV directly or the first CSV contained in a ZIP archive

This is designed for Kaggle-hosted datasets where the final artifact may be downloaded as a direct CSV or a zipped bundle.

---

## Dataset cleaning and labeling

The `DataIngestion.clean_and_label()` method is responsible for preparing the raw dataset for the next stage.

### Cleaning steps

The method performs the following operations in order:

1. Makes a copy of the input DataFrame
2. Trims whitespace from all column names
3. Drops rows where all values are missing
4. Removes duplicate rows
5. Resets the row index
6. Verifies the configured target column is present
7. Converts the target column to numeric values when the config requires it
8. Drops rows where the target value is still missing after conversion
9. Trips leading and trailing whitespace from object/string columns
10. Rejects the dataset if it becomes empty

### Target handling

The configuration includes:

```yaml
data:
  target_column: exam_score
  type: int
```

When `data.type` is an integer-like value, the code runs:

```python
cleaned[self.config.target_column] = pd.to_numeric(
    cleaned[self.config.target_column], errors="coerce"
)
```

This is important because many student performance datasets may contain strings such as `"75"`, `"80.0"`, or blank values. The conversion step normalizes the target into a numeric column and removes unusable rows.

---

## Validation behavior

The ingestion component fails fast when the input data does not meet the required contract.

### Common validation failures

- missing config file
- invalid YAML structure
- unknown source value
- missing required config keys
- absent target column
- dataset empty after cleaning
- unsupported file extension for local data
- Kaggle archive without a CSV file

The system uses structured logging to record errors and makes these failures explicit with descriptive exceptions.

---

## Dataset versioning

`DataIngestion.save_versioned_dataset()` writes the processed dataset to disk and produces a metadata manifest.

### Output structure

The output directory is created automatically.

Example output:

```text
artifacts/data/processed/
├── student_performance_v2.0.0.csv
└── student_performance_v2.0.0.json
```

### Saved CSV

The cleaned DataFrame is written as a CSV file using:

```python
data.to_csv(dataset_path, index=False)
```

This ensures the processed dataset is flattened and ready for downstream training or validation steps.

### Manifest JSON

The system writes a JSON metadata file containing:

```json
{
  "dataset_version": "2.0.0",
  "source": "device",
  "target_column": "exam_score",
  "row_count": 1000,
  "columns": ["gender", "race_ethnicity", "parental_level_of_education", "lunch", "test_preparation_course", "exam_score"],
  "sha256": "..."
}
```

This manifest captures:

- version identifier
- data source used
- target column name
- final row count
- schema columns
- checksum for integrity tracking

The checksum is computed using a SHA-256 hash of the saved dataset file.

---

## Internal helper functions

### `_kaggle_download_url()`

This helper converts a Kaggle dataset page link into the API download URL pattern used by Kaggle's dataset endpoints.

Example conversion:

```python
https://www.kaggle.com/datasets/whenamancodes/student-performance-indicator
```

becomes:

```python
https://www.kaggle.com/api/v1/datasets/download/whenamancodes/student-performance-indicator
```

### `_read_downloaded_dataset()`

This static method handles the downloaded artifact:

- if the downloaded file is a ZIP, it opens it and reads the first CSV found inside
- if the file is not a ZIP, it requires the file extension to be `.csv`
- it raises clear errors when a Kaggle download is malformed or does not contain a CSV

### `_sha256()`

This helper generates a SHA-256 digest for file integrity checks and version metadata.

---

## Typical usage pattern

The ingestion workflow is usually used in a pipeline like this:

```python
from src.components.data_ingestion import DataIngestion

ingestion = DataIngestion()
raw_df = ingestion.acquire_data()
clean_df = ingestion.clean_and_label(raw_df)
output_path = ingestion.save_versioned_dataset(clean_df)

print(f"Prepared dataset saved to: {output_path}")
```

This pattern keeps the lifecycle explicit:

1. acquire raw data
2. validate and clean it
3. persist a versioned dataset artifact

---

## Logging and observability

The module uses the project logger (`get_logger()`) to emit diagnostic information about:

- datasets loaded from device or Kaggle
- invalid config or missing files
- unsupported file types
- empty or invalid data after cleaning
- successful output artifact creation

This is useful during debugging or pipeline audits because each stage logs both the action and the relevant metadata.

---

## Design decisions

The current implementation follows a simple and reliable pattern:

- configuration-first design through YAML
- explicit validation before processing
- strict data integrity checks for the target column
- deterministic output versioning using a versioned filename and manifest
- lightweight dataset cleanup without modifying the business logic of later stages

This keeps the ingestion component easy to reason about and suitable for a modular ML pipeline.

---

## Operational guidance

- Keep the dataset source consistent with the environment: use `device` for local data and `kaggle` for remote dataset fetches.
- Ensure the `target_column` exactly matches the dataset schema.
- Validate the raw dataset before training because downstream steps rely on clean numeric targets.
- Review the generated manifest for dataset lineage, versioning, and integrity checks.
- Prefer controlled file naming and version updates when changing the underlying dataset.

---

**Last updated**: 2026-09-11
**Maintainer**: Adamu Joseph Ohigwere
