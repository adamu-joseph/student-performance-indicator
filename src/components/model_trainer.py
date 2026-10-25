"""Train a configured regression model and register it with MLflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

import mlflow
import mlflow.sklearn
import numpy as np
import yaml
from mlflow.models import infer_signature
from sklearn.neighbors import KNeighborsRegressor

from utils.logger import get_logger

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "model_trainer_config.yaml"
logger = get_logger()


# Add future supported estimator classes to this registry.
MODEL_REGISTRY = {
    "KNeighborsRegressor": KNeighborsRegressor,
}


def _resolve_path(value: str | Path) -> Path:
    """Resolve relative paths from the project root."""

    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


@dataclass(frozen=True)
class ModelTrainerConfig:
    """Validated settings for model training and MLflow logging."""

    input_dir: Path
    preprocessor_path: Path
    tracking_uri: str
    experiment_name: str
    active_model: str
    registered_model_name: str
    models: dict[str, dict[str, Any]]

    required: ClassVar[frozenset[str]] = frozenset(
        {
            "input_dir",
            "preprocessor_path",
            "tracking_uri",
            "experiment_name",
            "active_model",
            "registered_model_name",
            "models",
        }
    )

    @classmethod
    def from_yaml(
        cls, config_path: Path | str = DEFAULT_CONFIG_PATH
    ) -> ModelTrainerConfig:
        """Load and validate model trainer settings from YAML."""

        path = _resolve_path(config_path)
        if not path.is_file():
            logger.error("Model trainer config not found", path=str(path))
            raise FileNotFoundError(f"Model trainer config not found: {path}")

        try:
            with path.open("r", encoding="utf-8") as config_file:
                raw = yaml.safe_load(config_file) or {}
        except yaml.YAMLError as error:
            logger.error("Failed to parse model trainer YAML", path=str(path))
            raise ValueError(f"Invalid model trainer YAML: {path}") from error

        config = raw.get("config", {})
        if not isinstance(config, dict):
            raise ValueError("The 'config' section must be a mapping")

        missing = cls.required.difference(config)
        if missing:
            raise ValueError(
                f"Missing model trainer config keys: {sorted(missing)}"
            )

        models = config["models"]
        if not isinstance(models, dict) or not models:
            raise ValueError("'models' must be a non-empty mapping")

        active_model = str(config["active_model"])
        if active_model not in models:
            raise ValueError(
                f"Active model '{active_model}' is not defined in 'models'"
            )

        for model_name, model_config in models.items():
            if not isinstance(model_config, dict):
                raise ValueError(
                    f"Configuration for model '{model_name}' must be a mapping"
                )
            estimator_name = str(model_config.get("class", ""))
            if estimator_name not in MODEL_REGISTRY:
                supported = ", ".join(sorted(MODEL_REGISTRY))
                raise ValueError(
                    f"Unsupported model class '{estimator_name}' for "
                    f"'{model_name}'. Supported classes: {supported}"
                )
            params = model_config.get("params", {})
            if not isinstance(params, dict):
                raise ValueError(
                    f"'params' for model '{model_name}' must be a mapping"
                )

        return cls(
            input_dir=_resolve_path(config["input_dir"]),
            preprocessor_path=_resolve_path(config["preprocessor_path"]),
            tracking_uri=str(config["tracking_uri"]),
            experiment_name=str(config["experiment_name"]),
            active_model=active_model,
            registered_model_name=str(config["registered_model_name"]),
            models=models,
        )

    @property
    def active_model_config(self) -> dict[str, Any]:
        """Return the selected model's configuration."""

        return self.models[self.active_model]


class ModelTrainer:
    """Load processed data, train the selected estimator, and log it to MLflow."""

    def __init__(
        self, config_path: Path | str = DEFAULT_CONFIG_PATH
    ) -> None:
        """Initialize the trainer using a YAML configuration file."""

        self.config = ModelTrainerConfig.from_yaml(config_path)

    def _load_training_data(self) -> tuple[np.ndarray, np.ndarray]:
        """Load and validate the training arrays produced by feature engineering."""

        x_path = self.config.input_dir / "X_train.npy"
        y_path = self.config.input_dir / "y_train.npy"

        missing = [str(path) for path in (x_path, y_path) if not path.is_file()]
        if missing:
            logger.error("Training artifacts are missing", files=missing)
            raise FileNotFoundError(
                "Missing training artifacts: " + ", ".join(missing)
            )

        x_train = np.load(x_path, allow_pickle=False)
        y_train = np.load(y_path, allow_pickle=False).ravel()

        if x_train.ndim != 2:
            raise ValueError("X_train must be a two-dimensional array")
        if len(x_train) != len(y_train):
            raise ValueError("X_train and y_train have different row counts")
        if len(x_train) == 0:
            raise ValueError("Training data is empty")
        if not np.isfinite(x_train).all():
            raise ValueError("X_train contains NaN or infinite values")
        if not np.isfinite(y_train).all():
            raise ValueError("y_train contains NaN or infinite values")

        logger.info(
            "Training data loaded",
            train_shape=x_train.shape,
            target_shape=y_train.shape,
        )
        return x_train, y_train

    def train(self) -> str:
        """Fit the configured model and log/register it in MLflow.

        Returns:
            The MLflow model URI for the logged model artifact.
        """

        x_train, y_train = self._load_training_data()
        model_config = self.config.active_model_config
        estimator_name = str(model_config["class"])
        estimator_params = model_config.get("params", {})
        estimator_class = MODEL_REGISTRY[estimator_name]

        try:
            model = estimator_class(**estimator_params)
        except TypeError as error:
            logger.error(
                "Invalid estimator parameters",
                model=estimator_name,
                params=estimator_params,
            )
            raise ValueError(
                f"Invalid parameters for {estimator_name}: {error}"
            ) from error

        mlflow.set_tracking_uri(self.config.tracking_uri)
        mlflow.set_experiment(self.config.experiment_name)

        logger.info(
            "Model training started",
            model=self.config.active_model,
            estimator=estimator_name,
            params=estimator_params,
            experiment=self.config.experiment_name,
        )

        with mlflow.start_run(run_name=self.config.active_model) as run:
            model.fit(x_train, y_train)

            mlflow.log_params(
                {
                    "active_model": self.config.active_model,
                    "estimator_class": estimator_name,
                    **{
                        key: value
                        for key, value in estimator_params.items()
                        if isinstance(value, (str, int, float, bool))
                        or value is None
                    },
                }
            )
            mlflow.log_param("training_rows", len(x_train))
            mlflow.log_param("feature_count", x_train.shape[1])

            # Infer the model signature using a small sample to avoid predicting
            # over the full training dataset just to create the signature.
            signature_input = x_train[: min(5, len(x_train))]
            signature_output = model.predict(signature_input)
            signature = infer_signature(signature_input, signature_output)

            model_info = mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path="model",
                registered_model_name=self.config.registered_model_name,
                signature=signature,
                input_example=signature_input,
            )

            # Log the fitted preprocessing object as a run artifact so the
            # inference workflow can retrieve the same fitted transformer.
            if self.config.preprocessor_path.is_file():
                mlflow.log_artifact(
                    str(self.config.preprocessor_path),
                    artifact_path="preprocessing",
                )
            else:
                logger.warning(
                    "Fitted preprocessor artifact not found; model was logged "
                    "without it",
                    preprocessor_path=str(self.config.preprocessor_path),
                )

            mlflow.set_tag("project", "student-performance-indicator")
            mlflow.set_tag("model_name", self.config.active_model)

            model_uri = model_info.model_uri
            run_id = run.info.run_id

        logger.info(
            "Model training and MLflow logging completed",
            model=self.config.active_model,
            registered_model_name=self.config.registered_model_name,
            run_id=run_id,
            model_uri=model_uri,
        )
        return model_uri


__all__ = ["ModelTrainer", "ModelTrainerConfig"]
