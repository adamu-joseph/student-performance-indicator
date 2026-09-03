# Architecture & Project Structure

## Table of Contents

1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [Key Components](#key-components)
4. [Workflow & Pipeline](#workflow--pipeline)

---

## Project Overview

The **Student Performance Indicator** is a machine learning project designed to predict and analyze student performance. It uses a complete ML pipeline that includes data ingestion, transformation, model training, and prediction capabilities.

### Key Features

- End-to-end ML pipeline implementation
- Exploratory Data Analysis (EDA) via Jupyter notebooks
- Multiple data transformation strategies
- CatBoost model training and evaluation
- Prediction pipeline for inference
- Modular, extensible architecture

---

## Project Structure

``` txt
student-performance-indicator/
├── src/                           # Main source code
│   ├── components/                # ML pipeline components
│   │   ├── data_ingestion.py      # Data loading & validation
│   │   ├── data_transformation.py # Feature engineering & preprocessing
│   │   └── model_trainer.py       # Model training & evaluation
│   ├── pipeline/                  # End-to-end pipelines
│   │   ├── train_pipeline.py      # Training workflow
│   │   └── predict_pipeline.py    # Inference workflow
│   ├── exception.py               # Custom exception handling
│   ├── logger.py                  # Logging configuration
│   └── utils.py                   # Utility functions
├── notebook/                      # Jupyter notebooks for exploration
│   ├── 1.EDA STUDENT PERFORMANCE.ipynb
│   ├── 2.MODEL TRAINING.ipynb
│   └── data/                      # Sample data for notebooks
├── artifacts/                     # Data files & trained models
│   ├── raw.csv                    # Raw dataset
│   ├── train.csv                  # Training set
│   └── test.csv                   # Test set
├── catboost_info/                 # CatBoost training artifacts
├── requirements.txt               # Project dependencies
├── setup.py                       # Package configuration
└── README.md                      # Project overview
```

---

## Key Components

### 1. Data Ingestion (`src/components/data_ingestion.py`)

Responsible for loading and validating raw data from various sources.

**Key Functions:**

- Load data from CSV, Excel, or databases
- Data validation and integrity checks
- Train-test split operations

### 2. Data Transformation (`src/components/data_transformation.py`)

Handles feature engineering, preprocessing, and data normalization.

**Key Functions:**

- Feature scaling and normalization
- Categorical encoding
- Missing value imputation
- Feature selection

### 3. Model Trainer (`src/components/model_trainer.py`)

Orchestrates model training, validation, and evaluation.

**Key Functions:**

- Model initialization and hyperparameter tuning
- Training and validation loops
- Model evaluation metrics
- Model serialization

---

## Workflow & Pipeline

### Training Pipeline (`src/pipeline/train_pipeline.py`)

Orchestrates the complete training workflow:

1. Data Ingestion → Load raw data
2. Data Transformation → Process & engineer features
3. Model Training → Train and evaluate models
4. Artifact Storage → Save models and preprocessors

### Prediction Pipeline (`src/pipeline/predict_pipeline.py`)

Handles inference using trained models:

1. Load preprocessors and models
2. Transform input data
3. Generate predictions
4. Return results

### Running Pipelines

```python
from src.pipeline.train_pipeline import TrainPipeline
from src.pipeline.predict_pipeline import PredictPipeline

# Training
train_pipeline = TrainPipeline()
train_pipeline.run()

# Prediction
predict_pipeline = PredictPipeline()
predictions = predict_pipeline.predict(input_data)
```

---

**Last Updated:** 2026-09-01  
**Maintainer:** Adamu Joseph Ohigwere