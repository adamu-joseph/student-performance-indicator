# Project Structure

Status: Not accepted

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

**Last Updated:** 2026-09
**Maintainer:** Adamu Joseph Ohigwere
