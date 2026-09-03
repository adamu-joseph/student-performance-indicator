# MLOps Design

Status: Not Accepted

## Table of Contents

- [Context](#context)
- [Decision](#decision)
- [Mlops Processes](#mlops-processes)
- [ZenML Pipeline Orchestration](#zenml-pipeline-orchestration)
- [Parameters and Metrics Logging](#parameters-and-metrics-logging)
- [Reproducibility](#reproducibility)
- [Consequences](#consequences)
- [Future Enhancements](#future-enhancements)

## Context

The Student Grade Prediction project requires a robust MLOps solution to ensure reproducibility, experiment tracking, artifact management, model versioning, deployment readiness, and governance throughout the machine learning lifecycle.

To achieve these goals, the project will use ZenML as the machine learning pipeline orchestration framework and MLflow as the experiment tracking and model management backend.

ZenML provides pipeline orchestration, artifact lineage, reproducibility, and workflow management, while MLflow provides experiment tracking, artifact storage, model packaging, and model registry capabilities.

## Decision

ZenML will be adopted as the primary MLOps framework for orchestrating machine learning workflows.

MLflow will be integrated with ZenML and used for:

- Experiment tracking
- Parameter logging
- Metric logging
- Model logging
- Model versioning
- Model registry

All machine learning workflows must be executed through ZenML pipelines.

## MLops Processes

### Main Processes

- Data Ingestion and labelling
- Feature engineering
- model training and experimentation
- Validation and Testing
- Packaging and CI/CD
- Deployment and Rollout
- Monitoring and Observability
- Feedback and Retraining
- Governance and Compliance

#### 1. Data Ingestion & Labeling

- Collect raw data from logs, databases, APIs, or sensors.  
- Clean, annotate, and version datasets.  
- **Output:** versioned datasets ready for feature engineering.  

#### 2. Feature Engineering

- Transform raw data into usable features (normalization, encoding, aggregation).  
- Register features in a feature store for reuse and consistency.  

#### 3. Model Training & Experimentation

- Train models with different algorithms and hyperparameters.  
- Track experiments, datasets, and model versions.  
- **Output:** trained model artifacts (weights, checkpoints).  

#### 4. Validation & Testing

- Evaluate models against test data.  
- Measure accuracy, fairness, bias, and robustness.  
- **Output:** validation reports and metrics.  

#### 5. Packaging & CI/CD

- Package models into deployable artifacts (e.g., Docker containers).  
- Push to a model registry for version control.  
- Integrate with CI/CD pipelines for automated deployment.  

#### 6. Deployment & Rollout

- Deploy models to production (REST APIs, batch services, streaming).  
- Use strategies like canary releases or blue-green deployments to reduce risk.  

#### 7. Monitoring & Observability

- Track system health (latency, error rates).  
- Monitor ML-specific metrics: prediction quality, data drift, concept drift.  
- Detect when retraining is needed.  

#### 8. Feedback & Retraining

- Collect new labeled data.  
- Retrain models periodically or on demand.  
- Maintain continuous improvement.  

#### 9. Governance & Compliance

- Human-in-the-loop reviews.  
- Documentation (model cards, data sheets).  
- Automated policy checks for fairness, reproducibility, and auditability.  

## ZenML Pipeline Orchestration

ZenML is responsible for orchestrating all machine learning workflows.

Responsibilities include:

- Pipeline execution
- Step dependency management
- Artifact lineage tracking
- Pipeline reproducibility
- Workflow standardization
- Integration with MLflow

Each stage of the workflow will be implemented as an independent and reusable ZenML step.

### ZenML Stack

ZenML is the backbone of the project.

It should manage

pipeline execution
step orchestration
artifact tracking
lineage
caching
reproducibility

Every operation should be a ZenML Step.

#### Orchestrator

Local Machine

#### Artifact store

Local

Artifacts generated during training and evaluation must be stored and tracked.

Examples include:

- Evaluation reports
- SHAP explanation reports
- Feature importance plots
- Data validation reports
- Trained models
- Model cards
- Raw datasets
- Validated datasets
- Processed datasets
- Training logs
- Dataset schema reports
- EDA reports

Artifact Lineage
Artifact lineage enables:

- Traceability
- Reproducibility
- Auditing
- Debugging

Every artifact must be traceable to the pipeline run that created it.

#### Experiment Tracker

Mlflow

Experiment tracking will be performed using MLflow.

Information captured includes:

- Experiment name
- Run ID
- Start time
- End time
- Run status
- Training configuration
- Source code version

Experiment tracking enables reproducibility and comparison between multiple model runs.

#### Model Registry

MLflow Model Registry will serve as the source of truth for model versions.

Capabilities include:

- Version management
- Lifecycle management
- Promotion workflows
- Rollback support
- Production model tracking

Model lifecycle stages:

```text
Development
    ↓
Staging
    ↓
Production
    ↓
Archived
```

Only validated models may be promoted to Production.

#### Container Registry

Docker Hub will be used to store Docker Images ensuring that pipelines run remotely and can run anyway.
This ensures pipeline execution is reproducible.

#### Infrastructure

Execution happens in the following environments in their respective stages

Development: Laptop
Production: AWS cloud

#### Deployment

Deployment-ready models will be produced through the ZenML pipeline and registered in MLflow.

Deployment requirements include:

- Reproducible model packaging
- Version-controlled releases
- Registry-based model retrieval
- Automated deployment readiness checks

Models promoted to Production must satisfy predefined validation and performance requirements.

Docker:
    will be used for containerizing the application and its dependencies, ensuring consistency across development and production environments.
Flask:
    will be used to build and expose RESTful API endpoints for model inference and application interaction.
AWS:
    will serve as the cloud platform for hosting, deploying, and scaling the application in a production environment.

## Parameters and Metrics Logging

All model parameters and evaluation metrics must be logged.

### Parameters

Examples include:

- Model type
- Learning rate
- Number of estimators
- Maximum tree depth
- Random seed
- Feature selection configuration

## Reproducibility

All pipeline executions must be reproducible.

Reproducibility is achieved through:

- Version-controlled source code
- Fixed random seeds
- Logged parameters
- Versioned artifacts
- Registered models
- Tracked pipeline runs

Every model version must be traceable to:

- Source code version
- Dataset version
- Pipeline run
- Hyperparameter configuration

## Consequences

### Positive

- Reproducible machine learning workflows
- Standardized pipeline execution
- Improved experiment tracking
- Improved model governance
- Artifact lineage visibility
- Easier collaboration
- Simplified deployment workflows
- Faster rollback and recovery

### Negative

- Additional infrastructure requirements
- Increased storage usage
- Additional operational complexity
- Learning curve for ZenML and MLflow
- Longer initial project setup time

**Last Updated:** 2026-09
**Maintainer:** Adamu Joseph Ohigwere
