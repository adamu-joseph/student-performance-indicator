# Data Ingestion

This document describes the data acquisition, validation, cleaning, and versioning pipeline used by the Student Performance Indicator project. The ingestion layer is the first step in the ML workflow and ensures that only a valid, normalized dataset reaches the transformation and training stages.

## Overview

The implementation lives in `src/components/data_ingestion.py`. It is responsible for:

- loading raw data from either a local CSV file or a Kaggle dataset source
- validating configuration values from YAML
- checking that required schema elements such as the target column are present
- cleaning invalid rows and normalizing field values
- writing a versioned dataset artifact and a JSON manifest for reproducibility

This stage does not perform feature engineering or model training. Its purpose is to convert raw data into a reliable tabular input for downstream tasks.

---

## Relevant project files

| File | Responsibility |
| --- | --- |
| `src/components/data_ingestion.py` | Acquisition, validation, cleaning, and versioning logic |
| `config/data_ingestion_config.yaml` | Runtime configuration for the data source and target column |
| `artifacts/data/raw/` | Raw source dataset files |
| `artifacts/data/processed/` | Versioned cleaned CSVs and metadata manifests |

---

## Configuration contract

The system loads its settings through `DataIngestionConfig.from_yaml()`. The configuration file is expected to follow the structure defined in `config/data_ingestion_config.yaml`.

### Current project YAML

```yaml
config:
  source: device
  input_path: artifacts/data/raw/dataset.csv
  kaggle_url: https://www.kaggle.com/datasets/whenamancodes/student-performance-indicator
  output_dir: artifacts/data/processed
  dataset_version: 2.0.0
  request_timeout: 30

supported_file_types:
  - .csv

data:
  target_column: exam_score
  type: int
```

### Supported configuration values

The dataclass validates the following:

- `config.source` must be either `device` or `kaggle`
- `config.input_path` must exist when using local data
- `config.kaggle_url` must be present for Kaggle downloads
- `config.output_dir` is where processed artifacts are saved
- `config.dataset_version` is used in the output filename
- `data.target_column` must be non-empty and must exactly match the dataset schema
- `data.type` defines how the target is cast prior to modeling
- `supported_file_types` is normalized to lowercase values and defaults to `.csv` support

Relative paths are resolved against the project root using `_resolve_path()` so configuration remains portable across environments.

---

## Data acquisition workflow

The public entry point is `DataIngestion.acquire_data()`.

### 1. Local-device mode

When `source: device` is selected, the code performs a direct file check:

- verifies the input file exists
- verifies the file extension is accepted
- loads the content with `pd.read_csv(input_path)`

If the file is missing, a `FileNotFoundError` is raised. If the file extension is not supported, a `ValueError` is raised.

### 2. Kaggle mode

When `source: kaggle` is selected, the code does the following:

1. converts the dataset page URL into a Kaggle API download URL using a regex-based helper
2. sends a `requests.get()` request with a timeout
3. writes the response body to a temporary file
4. reads either:
   - a direct CSV file, or
   - the first CSV inside a ZIP archive

This is useful because Kaggle dataset downloads may be packaged as archives rather than a single CSV file.

---

## Cleaning and validation logic

The `DataIngestion.clean_and_label()` method prepares the data before it is stored or modeled.

### Cleaning steps performed in order

1. creates a working copy of the DataFrame
2. strips whitespace from column names
3. removes rows where all values are missing
4. drops duplicate rows
5. resets the index
6. checks whether the configured target column exists
7. converts the target column to numeric values when the config requires it
8. removes rows whose target value is still missing after conversion
9. strips whitespace from object columns
10. raises an error if the cleaned dataset is empty

### Target-column handling

The target column is treated as the label for supervised learning. The project configuration supports a numeric target through `data.type`, and the implementation uses:

```python
cleaned[self.config.target_column] = pd.to_numeric(
    cleaned[self.config.target_column], errors="coerce"
)
```

This step is important because raw labels may arrive as strings like `"75"`, `"80.0"`, or empty values. The conversion keeps the dataset consistent and ensures that invalid labels are removed rather than silently carried into training.

---

## Validation behavior and failure modes

The ingestion component fails fast when the dataset or configuration is invalid. Typical reasons include:

- missing or unreadable YAML file
- invalid YAML syntax
- unsupported source value
- missing required keys in the YAML config
- absent target column in the dataset
- empty dataset after cleaning
- unsupported extension for local input files
- Kaggle archive that does not contain a CSV file

Errors are logged using the project logger and raised as explicit exceptions so that the pipeline stops before bad data reaches downstream stages.

---

## Versioned dataset output

After cleaning, `DataIngestion.save_versioned_dataset()` writes the data to disk and creates a manifest.

### Output directory

The output directory is created automatically if it does not already exist.

Example structure:

```text
artifacts/data/processed/
├── student_performance_v2.0.0.csv
└── student_performance_v2.0.0.json
```

### CSV output

The cleaned DataFrame is saved with:

```python
data.to_csv(dataset_path, index=False)
```

This ensures the processed artifact is flat, reusable, and ready for later transformation or modeling steps.

### Manifest JSON

The metadata file captures:

- dataset version
- data source
- target column name
- number of rows
- column names
- SHA-256 checksum of the saved CSV

Example schema:

```json
{
  "dataset_version": "2.0.0",
  "source": "device",
  "target_column": "exam_score",
  "row_count": 6607,
  "columns": [
    "Hours_Studied",
    "Attendance",
    "Parental_Involvement",
    "Exam_Score"
  ],
  "sha256": "..."
}
```

The checksum allows the project to verify that the processed dataset has not been modified unexpectedly after creation.

---

## Helper functions

### `_kaggle_download_url()`

This helper converts a Kaggle dataset page URL into the API download URL pattern used by Kaggle.

Example:

```python
https://www.kaggle.com/datasets/whenamancodes/student-performance-indicator
```

becomes:

```python
https://www.kaggle.com/api/v1/datasets/download/whenamancodes/student-performance-indicator
```

### `_read_downloaded_dataset()`

This static method reads the downloaded artifact and handles both CSV and ZIP formats. It extracts the first CSV inside a ZIP archive when needed and raises descriptive errors when the download is malformed.

### `_sha256()`

This helper computes the file checksum used in the manifest JSON for dataset integrity tracking.

---

## Typical pipeline usage

The normal lifecycle is:

```python
from src.components.data_ingestion import DataIngestion

ingestion = DataIngestion()
raw_df = ingestion.acquire_data()
clean_df = ingestion.clean_and_label(raw_df)
output_path = ingestion.save_versioned_dataset(clean_df)

print(f"Prepared dataset saved to: {output_path}")
```

This sequence keeps the process clear and reproducible:

1. load raw data from source
2. validate and clean it
3. store a versioned artifact
4. pass the prepared dataset to the next pipeline stage

---

## Best practices

- keep the YAML source and output paths consistent with the project structure
- use `device` mode for local files and `kaggle` mode for remote access
- confirm that `target_column` exactly matches the dataset schema
- version the dataset whenever the raw source changes
- review the manifest after generation to confirm row counts and checksums are valid

The ingestion layer is intentionally lightweight and strict. This keeps the pipeline reliable and prevents invalid data from reaching modeling or evaluation.

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
