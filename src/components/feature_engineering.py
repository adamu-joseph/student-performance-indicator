"""Feature engineering: imputation, encoding, scaling, and feature store registration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

import numpy as np
import pandas as pd
import yaml
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    FunctionTransformer,
    OneHotEncoder,
    OrdinalEncoder,
    RobustScaler,
)

from utils.logger import get_logger
from utils.utils import save_object

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "feature_engineering_config.yaml"
logger = get_logger()


@dataclass(frozen=True)
class FeatureEngineeringConfig:
    """Configuration for feature transformation and storage."""

    input_dir: Path
    output_dir: Path
    test_size: float
    random_state: int
    target_column: str
    ordinal_mappings: dict[str, list[str]]
    nominal_mappings: dict[str, list[str]]
    binary_mappings: dict[str, list[str]]
    scaling_columns: tuple[str, ...]
    scaling_method: str
    missing_indicator_columns: tuple[str, ...]

    required: ClassVar[frozenset[str]] = frozenset(
        {"input_dir", "output_dir", "test_size", "random_state"}
    )

    @classmethod
    def from_yaml(
        cls, config_path: Path | str = DEFAULT_CONFIG_PATH
    ) -> FeatureEngineeringConfig:
        """Load and validate feature engineering settings from YAML.

        Args:
            config_path: Path to the YAML configuration file.

        Returns:
            A validated FeatureEngineeringConfig instance.
        """

        path = Path(config_path)
        if not path.exists():
            logger.error("Feature engineering config not found", path=str(path))
            raise FileNotFoundError(f"Feature engineering config not found: {path}")

        try:
            with path.open("r", encoding="utf-8") as config_file:
                raw = yaml.safe_load(config_file) or {}
        except yaml.YAMLError as error:
            logger.error("Failed to parse feature engineering YAML", path=str(path))
            raise ValueError(f"Invalid feature engineering YAML: {path}") from error

        config = raw.get("config", {})
        encoding = raw.get("encoding", {})
        scaling = raw.get("scaling", {})
        imputation = raw.get("imputation", {})

        if not isinstance(config, dict):
            logger.error("Feature engineering config must be a mapping")
            raise ValueError("Feature engineering config must be a mapping")

        missing = cls.required.difference(config)
        if missing:
            logger.error(
                "Missing feature engineering config keys", missing=sorted(missing)
            )
            raise ValueError(
                f"Missing feature engineering config keys: {sorted(missing)}"
            )

        # For ordinal features: keep explicit order
        ordinal_raw = encoding.get("ordinal", {})
        ordinal_mappings = {
            col: list(mapping.keys()) if isinstance(mapping, dict) else list(mapping)
            for col, mapping in ordinal_raw.items()
        }

        # For nominal features: keep categories as strings (no numeric mapping)
        nominal_raw = encoding.get("nominal", {})
        nominal_mappings = {
            col: list(mapping.keys()) if isinstance(mapping, dict) else list(mapping)
            for col, mapping in nominal_raw.items()
        }

        binary_raw = encoding.get("binary", {})
        binary_mappings = {
            col: list(mapping.keys()) for col, mapping in binary_raw.items()
        }

        return cls(
            input_dir=_resolve_path(config["input_dir"]),
            output_dir=_resolve_path(config["output_dir"]),
            test_size=float(config["test_size"]),
            random_state=int(config["random_state"]),
            target_column=str(config.get("target_column", "Exam_Score")),
            ordinal_mappings=ordinal_mappings,
            nominal_mappings=nominal_mappings,
            binary_mappings=binary_mappings,
            scaling_columns=tuple(scaling.get("columns", [])),
            scaling_method=str(scaling.get("method")),
            missing_indicator_columns=tuple(
                imputation.get("missing_indicator_columns", [])
            ),
        )


def _resolve_path(value: str | Path) -> Path:
    """Resolve relative configuration paths from the project root."""

    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


class FeatureEngineering:
    """Transform raw data into model-ready features with versioned artifacts."""

    def __init__(self, config_path: Path | str = DEFAULT_CONFIG_PATH) -> None:
        """Initialize feature engineering from the configured YAML file.

        Args:
            config_path: Path to the YAML configuration file.
        """

        self.config = FeatureEngineeringConfig.from_yaml(config_path)

    def split_data(
        self, data: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Split the dataset into train and test partitions.

        Args:
            data: The full dataset including the target column.

        Returns:
            A tuple of (X_train, X_test, y_train, y_test).
        """

        target = self.config.target_column
        if target not in data.columns:
            logger.error("Target column not found in data", target=target)
            raise ValueError(f"Target column '{target}' not found in data")

        features = data.drop(columns=[target])
        labels = data[target]

        x_train, x_test, y_train, y_test = train_test_split(
            features,
            labels,
            test_size=self.config.test_size,
            random_state=self.config.random_state,
        )

        logger.info(
            "Data split complete",
            train_size=len(x_train),
            test_size=len(x_test),
        )

        return x_train, x_test, y_train, y_test

    def create_missing_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add binary flags for columns where missingness may be informative.

        Args:
            data: Feature DataFrame (without target).

        Returns:
            A copy of the DataFrame with additional ``*_missing`` columns.
        """

        result = data.copy()
        for col in self.config.missing_indicator_columns:
            if col in result.columns:
                result[f"{col}_missing"] = result[col].isna().astype(int)
        return result

    def build_preprocessor(self, x_train: pd.DataFrame) -> ColumnTransformer:
        """Build a sklearn preprocessing pipeline from configuration.

        Args:
            x_train: Training feature DataFrame used to determine column presence.

        Returns:
            A configured but unfitted ColumnTransformer.
        """

        transformers: list[tuple[str, Any, list[str]]] = []

        numeric_cols = [
            col
            for col in self.config.scaling_columns
            if col in x_train.columns and col != "Tutoring_Sessions"
        ]

        # Map string names to actual scaler classes
        scaler_map = {
            "functiontransformer": FunctionTransformer,
            "onehotencoder": OneHotEncoder,
            "ordinalencoder": OrdinalEncoder,
            "robustscaler": RobustScaler,
        }

        # Get the scaler class from the config string
        scaler_class = scaler_map.get(self.config.scaling_method.lower(), None)

        if scaler_class is None:
            logger.error("Unknown scaling method", method=self.config.scaling_method)
            raise ValueError(f"Unknown scaling method: {self.config.scaling_method}")

        # Instantiate the scaler
        scaler = scaler_class()

        if numeric_cols:
            numeric_pipeline = Pipeline(
                [
                    (
                        "imputer",
                        SimpleImputer(strategy="median"),
                    ),  # handles missing values
                    ("scaler", scaler),  # scales the data
                ]
            )
            transformers.append(("numeric", numeric_pipeline, numeric_cols))
            logger.info(
                "Numeric features pipeline initialized", numeric_count=len(numeric_cols)
            )

        if "Tutoring_Sessions" in x_train.columns:
            tutoring_pipeline = Pipeline(
                [
                    (
                        "imputer",
                        SimpleImputer(strategy="median"),
                    ),  # handles missing values
                    (
                        "log",
                        FunctionTransformer(
                            func=np.log1p, inverse_func=np.expm1, validate=True
                        ),
                    ),  # reduce skewness
                    ("scaler", scaler),  # scales the data
                ]
            )
            transformers.append(("tutoring", tutoring_pipeline, ["Tutoring_Sessions"]))
            logger.info("Tutoring_Sessions pipeline initialized")

        else:
            logger.critical(
                "Tutoring_Sessions column missing from training data; cannot apply log transformation"
            )

        ordinal_cols = [
            col for col in self.config.ordinal_mappings if col in x_train.columns
        ]
        if ordinal_cols:
            ordinal_categories = [
                self.config.ordinal_mappings[col] for col in ordinal_cols
            ]
            ordinal_pipeline = Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    (
                        "encoder",
                        OrdinalEncoder(
                            categories=ordinal_categories,
                            handle_unknown="use_encoded_value",
                            unknown_value=-1,
                        ),
                    ),
                ]
            )
            transformers.append(("ordinal", ordinal_pipeline, ordinal_cols))
            logger.info(
                "Ordinal features pipeline initialized", ordinal_count=len(ordinal_cols)
            )

        # Collect nominal columns that exist in the training set
        nominal_cols = [
            col for col in self.config.nominal_mappings if col in x_train.columns
        ]

        if nominal_cols:
            # Extract categories for each nominal column
            nominal_categories = [
                self.config.nominal_mappings[col] for col in nominal_cols
            ]

            # Build pipeline for nominal features
            nominal_pipeline = Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    (
                        "encoder",
                        OneHotEncoder(
                            drop="if_binary",
                            categories=nominal_categories,
                            handle_unknown="ignore",
                            sparse_output=False,
                        ),
                    ),
                ]
            )

            # Add to transformers list
            transformers.append(("nominal", nominal_pipeline, nominal_cols))
            logger.info(
                "Nominal features pipeline initialized", nominal_count=len(nominal_cols)
            )

        binary_cols = [
            col for col in self.config.binary_mappings if col in x_train.columns
        ]
        if binary_cols:
            binary_categories = [
                self.config.binary_mappings[col] for col in binary_cols
            ]
            binary_pipeline = Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    (
                        "encoder",
                        OneHotEncoder(
                            drop="if_binary",
                            categories=binary_categories,
                            handle_unknown="ignore",
                            sparse_output=False,
                        ),
                    ),
                ]
            )
            transformers.append(("binary", binary_pipeline, binary_cols))
            logger.info(
                "Binary features pipeline initialized", binary_count=len(binary_cols)
            )

        indicator_cols = [
            f"{col}_missing"
            for col in self.config.missing_indicator_columns
            if f"{col}_missing" in x_train.columns
        ]
        if indicator_cols:
            transformers.append(("indicators", "passthrough", indicator_cols))
            logger.info(
                "Missing indicator features included",
                indicator_count=len(indicator_cols),
            )

        preprocessor = ColumnTransformer(
            transformers=transformers,
            remainder="drop",
        )

        logger.info(
            "Preprocessor built",
            numeric_count=len(numeric_cols),
            kurt_count=len(["Tutoring_Sessions"]),
            ordinal_count=len(ordinal_cols),
            nominal_count=len(nominal_cols),
            binary_count=len(binary_cols),
            indicator_count=len(indicator_cols),
        )
        return preprocessor

    def fit_transform(
        self,
        x_train: pd.DataFrame,
        x_test: pd.DataFrame,
    ) -> tuple[np.ndarray, np.ndarray, ColumnTransformer]:
        """Create missing indicators, build the preprocessor, fit, and transform.

        Args:
            x_train: Training feature DataFrame.
            x_test: Test feature DataFrame.

        Returns:
            A tuple of (X_train_processed, X_test_processed, fitted_preprocessor).
        """

        x_train = self.create_missing_indicators(x_train)
        x_test = self.create_missing_indicators(x_test)

        preprocessor = self.build_preprocessor(x_train)
        x_train_processed = preprocessor.fit_transform(x_train)
        x_test_processed = preprocessor.transform(x_test)

        logger.info(
            "Feature transformation complete",
            train_shape=x_train_processed.shape,
            test_shape=x_test_processed.shape,
        )
        return x_train_processed, x_test_processed, preprocessor

    def get_feature_names(self, preprocessor: ColumnTransformer) -> list[str]:
        """Extract ordered feature names from a fitted preprocessor.

        Args:
            preprocessor: A fitted ColumnTransformer.

        Returns:
            List of feature names in output column order.
        """

        return list(preprocessor.get_feature_names_out())

    def save_artifacts(
        self,
        preprocessor: ColumnTransformer,
        x_train: np.ndarray,
        x_test: np.ndarray,
        y_train: pd.Series,
        y_test: pd.Series,
    ) -> dict[str, Path]:
        """Save the fitted preprocessor and processed arrays to the feature store.

        Args:
            preprocessor: The fitted ColumnTransformer.
            x_train: Processed training features.
            x_test: Processed test features.
            y_train: Training labels.
            y_test: Test labels.

        Returns:
            A mapping of artifact names to their file paths.
        """

        output = self.config.output_dir
        output.mkdir(parents=True, exist_ok=True)

        paths = {
            "preprocessor": output / "preprocessor.dill",
            "X_train": output / "X_train.npy",
            "X_test": output / "X_test.npy",
            "y_train": output / "y_train.npy",
            "y_test": output / "y_test.npy",
        }

        save_object(paths["preprocessor"], preprocessor)
        np.save(paths["X_train"], x_train)
        np.save(paths["X_test"], x_test)
        np.save(paths["y_train"], y_train.values)
        np.save(paths["y_test"], y_test.values)

        logger.info("Feature artifacts saved", output_dir=str(output))
        return paths


__all__ = ["FeatureEngineering", "FeatureEngineeringConfig"]
