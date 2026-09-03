# Mlops Architecture

## Context

                         GitHub
                            │
                            │
                     Source Code Version
                            │
                            ▼
                   ZenML Pipeline
                            │
        ┌───────────────────┼────────────────────┐
        │                   │                    │
        ▼                   ▼                    ▼
 Data Pipeline        Training Pipeline     Evaluation Pipeline
        │                   │                    │
        │                   │                    │
        ▼                   ▼                    ▼
 Local Artifact Store    MLflow Tracker    MLflow Registry
        │                   │                    │
        └───────────────┬───┴────────────────────┘
                        │
                        ▼
                  Deployment Package
                        │
                    Docker Image
                        │
                    Docker Hub
                        │
                        ▼
                     AWS + Flask