# Exploratory Data Analysis (EDA) Report

**Project Name:** Student Performance Indicator  
**Data Snapshot/Version:** Raw dataset loaded from `artifacts/data/raw/dataset.csv`  
**Author:** Adamu Joseph Ohigwere
**Date:** 2026-09-15  

---

## 1. Executive Summary

This analysis examines student-performance records before feature engineering and model training. The dataset combines numeric study-related variables with categorical information about student context, resources, support, and learning conditions. The prediction target is `Exam_Score`, making this a supervised regression problem.

The target is concentrated around the high 60s, with a limited observed range and potential extreme values requiring validation. `Attendance` and `Hours_Studied` show the clearest linear relationships with exam performance, while `Previous_Scores` and `Tutoring_Sessions` show weaker positive relationships.

**Core Recommendation:** Use a regression pipeline that handles mixed data types, skewness and kurtosis, explicitly addresses missing values, encodes categorical features, and compares multiple models using MAE, RMSE, and \(R^2\). Tree-based models should be included because correlation analysis may not capture nonlinear relationships or feature interactions. We basically use two models for predictions. One linear and one tree model, this is because linear models can extrapolate while the tree model will not.

---

## 2. Dataset Overview & Shape

- **Total Records (Rows):** 6607
- **Total Attributes (Columns):** 20
- **Target Variable:** `Exam_Score` — Regression

The dataset contains student behavior, academic history, support, and demographic/context variables.

### Data Type Breakdown

| Data Type | Count | Column Names |
| :--- | :---: | :--- |
| **Numerical** | 7 | Study hours, attendance, prior scores, tutoring, sleep, physical activity, and `Exam_Score` |
| **Categorical** | 13 | Parental involvement, resources, motivation, teacher quality, peer influence, school type, gender, learning disabilities, and other categorical variables |
| **Datetime** | 0 | None identified |

The notebook uses pandas data types to distinguish numeric and categorical columns. Ordinal concepts such as motivation, parental involvement, and teacher quality are currently treated as categorical variables and may require deliberate ordinal encoding during feature engineering.

---

## 3. Data Quality Audit & Anomalies

### 3.1 Missing Values

Missingness was measured for every column using both counts and percentages. Three categorical columns contain missing values; all numeric columns and the target are complete.

| Column | Type | Missing Count | Missing % | Unique Values |
| :--- | :---: | ---: | ---: | ---: |
| `Parental_Education_Level` | str | 90 | 1.36 | 3 |
| `Teacher_Quality` | str | 78 | 1.18 | 3 |
| `Distance_from_Home` | str | 67 | 1.01 | 3 |
| `Extracurricular_Activities` | str | 0 | 0.00 | 2 |
| `Internet_Access` | str | 0 | 0.00 | 2 |
| `School_Type` | str | 0 | 0.00 | 2 |
| `Learning_Disabilities` | str | 0 | 0.00 | 2 |
| `Gender` | str | 0 | 0.00 | 2 |
| `Parental_Involvement` | str | 0 | 0.00 | 3 |
| `Access_to_Resources` | str | 0 | 0.00 | 3 |
| `Motivation_Level` | str | 0 | 0.00 | 3 |
| `Family_Income` | str | 0 | 0.00 | 3 |
| `Peer_Influence` | str | 0 | 0.00 | 3 |
| `Sleep_Hours` | int64 | 0 | 0.00 | 7 |
| `Physical_Activity` | int64 | 0 | 0.00 | 7 |
| `Tutoring_Sessions` | int64 | 0 | 0.00 | 9 |
| `Hours_Studied` | int64 | 0 | 0.00 | 41 |
| `Attendance` | int64 | 0 | 0.00 | 41 |
| `Exam_Score` | int64 | 0 | 0.00 | 45 |
| `Previous_Scores` | int64 | 0 | 0.00 | 51 |

**Summary:** Total missingness is 235 values across 3 columns (all categorical, all under 1.4%). The target variable `Exam_Score` has zero missing values. All 7 numeric columns are complete.

**Recommended Actions:**

1. Impute `Parental_Education_Level`, `Teacher_Quality`, and `Distance_from_Home` using the most frequent category or an explicit `"Missing"` level within the training pipeline.
2. Consider adding missingness indicator flags for these three columns if missingness carries predictive signal.
3. Calculate imputation values using training data only to prevent data leakage.

### 3.2 Outliers & Extremes

- `Exam_Score` is concentrated around the high 60s.
- The observed maximum is above the central target range and should be checked for validity.
- Boxplots and histograms were used to identify possible extreme values.
- Numeric feature distributions vary in scale and spread.

**Impact:** Extreme observations may influence linear regression and error metrics.

**Action:**

1. Confirm that extreme values are valid observations rather than data-entry errors.
2. Do not remove valid observations automatically.
3. Compare models with and without robust preprocessing.
4. Consider robust scaling for linear models if feature distributions require it.
5. Evaluate residuals after model training.

### 3.3 Duplication & Leakage

- **Duplicate Rows Found:** 0.
- **Data Leakage Risks:**
  - Ensure that `Exam_Score` is excluded from model features.
  - Fit imputers, encoders, scalers, and feature selectors only on training data.
  - Confirm that no post-exam information is included in the predictors.
  - Validate that identifier-like columns are not used as predictive features without justification.

---

## 4. Target Variable Analysis

The target variable is `Exam_Score`.

### Regression Analysis

- **Distribution shape:** Concentrated around the high 60s with a restricted range.
- **Center:** Mean and median are calculated in the notebook.
- **Range:** Minimum and maximum are calculated in the notebook.
- **Unique values:** Calculated in the notebook.
- **Missing values:** Checked explicitly.
- **Skewness and kurtosis:** Reported in the numeric summary table.

The distribution should be considered during model evaluation because a concentrated target can make a baseline model appear competitive while still producing poor predictions for less-represented score ranges.

### Modeling Implications

- Use MAE to provide an interpretable average prediction error.
- Use RMSE to penalize larger prediction errors.
- Use \(R^2\) to measure explained variance relative to a mean-prediction baseline.
- Compare predictions across the full target range, not only near the mean.
- Inspect residuals for systematic underprediction or overprediction.

A target transformation is not recommended by default. It should only be introduced if validation demonstrates a clear benefit and the transformed predictions can be converted back to the original score scale correctly.

---

## 5. Feature Relationships & Hypotheses

### 5.1 Numerical-to-Target Insights

The notebook calculates Pearson correlations between numeric predictors and `Exam_Score`.

Key observations:

- `Attendance` shows one of the strongest positive linear relationships with `Exam_Score`.
- `Hours_Studied` also shows a clear positive relationship with exam performance.
- `Previous_Scores` shows a weaker positive relationship.
- `Tutoring_Sessions` shows a weaker positive relationship.
- `Sleep_Hours` and `Physical_Activity` appear comparatively weak in the linear correlation screen.

These relationships are predictive observations, not evidence of causation.

### Multicollinearity

A numeric correlation heatmap was generated to identify relationships among predictors. Any highly correlated feature pairs should be reviewed before fitting highly interpretable linear models.

**Action:**

- Retain correlated variables initially for tree-based models.
- Review variance inflation or coefficient stability for linear models.
- Use cross-validation to determine whether removing a feature improves generalization.
- Avoid removing features solely because they have a low individual correlation with the target; nonlinear and interaction effects may still be useful.

### 5.2 Categorical-to-Target Insights

Categorical group comparisons were performed using boxplots and grouped summary statistics. The table below summarizes exam-score distributions by category for all 13 categorical features.

| Feature | Category | Count | Mean | Median | Std |
| :--- | :--- | ---: | ---: | ---: | ---: |
| `Parental_Involvement` | High | 1908 | 68.09 | 68.00 | 3.95 |
| | Medium | 3362 | 67.10 | 67.00 | 3.73 |
| | Low | 1337 | 66.36 | 66.00 | 3.97 |
| `Access_to_Resources` | High | 1975 | 68.09 | 68.00 | 3.95 |
| | Medium | 3319 | 67.13 | 67.00 | 3.87 |
| | Low | 1313 | 66.20 | 66.00 | 3.56 |
| `Extracurricular_Activities` | Yes | 3938 | 67.44 | 67.00 | 3.94 |
| | No | 2669 | 66.93 | 67.00 | 3.79 |
| `Motivation_Level` | High | 1319 | 67.70 | 67.00 | 3.88 |
| | Medium | 3351 | 67.33 | 67.00 | 3.83 |
| | Low | 1937 | 66.75 | 67.00 | 3.96 |
| `Internet_Access` | Yes | 6108 | 67.29 | 67.00 | 3.87 |
| | No | 499 | 66.54 | 66.00 | 4.12 |
| `Family_Income` | High | 1269 | 67.84 | 68.00 | 4.16 |
| | Medium | 2666 | 67.33 | 67.00 | 3.81 |
| | Low | 2672 | 66.85 | 67.00 | 3.80 |
| `Teacher_Quality` | High | 1947 | 67.68 | 68.00 | 3.98 |
| | Medium | 3925 | 67.11 | 67.00 | 3.85 |
| | Low | 657 | 66.75 | 67.00 | 3.87 |
| | NaN | 78 | 66.64 | 66.00 | 2.86 |
| `School_Type` | Private | 2009 | 67.29 | 67.00 | 3.85 |
| | Public | 4598 | 67.21 | 67.00 | 3.91 |
| `Peer_Influence` | Positive | 2638 | 67.62 | 67.00 | 3.92 |
| | Neutral | 2592 | 67.20 | 67.00 | 3.84 |
| | Negative | 1377 | 66.56 | 66.00 | 3.83 |
| `Learning_Disabilities` | No | 5912 | 67.35 | 67.00 | 3.85 |
| | Yes | 695 | 66.27 | 66.00 | 4.07 |
| `Parental_Education_Level` | Postgraduate | 1305 | 67.97 | 68.00 | 3.69 |
| | College | 1989 | 67.32 | 67.00 | 3.83 |
| | High School | 3223 | 66.89 | 67.00 | 3.98 |
| | NaN | 90 | 67.06 | 67.00 | 3.28 |
| `Distance_from_Home` | Near | 3884 | 67.51 | 67.00 | 3.88 |
| | Moderate | 1998 | 66.98 | 67.00 | 3.79 |
| | Far | 658 | 66.46 | 66.00 | 4.14 |
| | NaN | 67 | 66.43 | 66.00 | 3.22 |
| `Gender` | Female | 2793 | 67.24 | 67.00 | 4.05 |
| | Male | 3814 | 67.23 | 67.00 | 3.77 |

#### Key Observations

**Strongest categorical separations (High vs. Low mean difference ~1.7–1.9 points):**

- `Parental_Involvement` and `Access_to_Resources` show the clearest ordinal gradient — students in the "High" category average roughly 1.7–1.9 points above those in "Low," with the median shifting by a full point at each level. These features exhibit a consistent step-down pattern from High to Medium to Low, suggesting a monotonic relationship that ordinal encoding could capture effectively.
- `Parental_Education_Level` follows a similar pattern: Postgraduate (67.97) > College (67.32) > High School (66.89), a ~1.1-point spread with a natural educational ordering.

**Moderate separations (~0.8–1.1 points):**

- `Peer_Influence` separates Positive (67.62) from Negative (66.56), a ~1.1-point gap. The Neutral group falls between them, reinforcing the ordinal nature of this variable.
- `Learning_Disabilities` shows a ~1.1-point gap (No: 67.35 vs. Yes: 66.27), with slightly higher variability in the "Yes" group (std 4.07 vs. 3.85), suggesting more diverse outcomes among students with learning disabilities.
- `Distance_from_Home` shows a gradient from Near (67.51) to Far (66.46), a ~1.1-point spread. The NaN group (66.43) aligns closely with the "Far" category.
- `Family_Income` shows a ~1.0-point spread across its three levels, and `Motivation_Level` shows a ~0.95-point spread — both with a consistent ordinal gradient.

**Weak or negligible separations (<0.5 points):**

- `School_Type` shows virtually no difference between Private (67.29) and Public (67.21). This feature is unlikely to contribute meaningful predictive signal on its own.
- `Gender` shows no meaningful difference (Female: 67.24 vs. Male: 67.23). Standard deviations are comparable, indicating similar score distributions across genders.
- `Internet_Access` shows a 0.75-point gap, but the "No" group is small (499 of 6607 students), so the estimate carries more uncertainty.
- `Extracurricular_Activities` shows a modest 0.51-point difference (Yes: 67.44 vs. No: 66.93).

**Missing-value groups:** The NaN rows in `Teacher_Quality` (78), `Parental_Education_Level` (90), and `Distance_from_Home` (67) tend to have mean scores at or below the lowest named category and noticeably lower standard deviations. This could indicate that missingness is not random — a missingness indicator flag may carry predictive information.

**Interpretation rule:** All differences described above are associations observed in the dataset. They do not establish that any category causes higher or lower exam performance. Group sizes are unequal, distributions overlap substantially, and confounding between features has not been controlled for.

#### Encoding Implications

- **Ordinal features** (`Parental_Involvement`, `Access_to_Resources`, `Motivation_Level`, `Peer_Influence`, `Parental_Education_Level`, `Family_Income`, `Distance_from_Home`, `Teacher_Quality`): These show consistent gradients and should be tested with both ordinal encoding (to preserve the natural ordering) and one-hot encoding. Cross-validation should determine which performs better.
- **Nominal features** (`School_Type`, `Gender`, `Extracurricular_Activities`, `Internet_Access`, `Learning_Disabilities`): Binary or low-cardinality variables suitable for one-hot encoding.

---

## 6. Preprocessing & Feature Engineering Pipeline Blueprint

The EDA identified specific data characteristics that the preprocessing pipeline must handle. The steps below are ordered by dependency — schema validation first, then cleaning, then feature engineering, then modeling.

### 6.1 Schema & Target Handling

- [ ] Validate that the incoming dataset has exactly 20 columns matching the expected schema (7 numeric, 13 categorical).
- [ ] Preserve the target column name `Exam_Score` exactly as it appears in the raw data — or apply a deliberate, documented schema normalization step during ingestion.
- [ ] Separate `Exam_Score` from the feature matrix before any preprocessing. The target is complete (0 missing, 45 unique integer values, range 55–101), so no target imputation is needed.
- [ ] Investigate the `Exam_Score` maximum of 101 — the EDA flagged this as above the typical central range (mean 67.24, 75th percentile 69). Confirm whether this is a valid observation or a data-entry error before training.

### 6.2 Missing Value Strategy

Three categorical columns have missing values; all numeric columns are complete. No rows need to be dropped for target missingness.

| Column | Missing Count | Missing % | Strategy |
| :--- | ---: | ---: | :--- |
| `Parental_Education_Level` | 90 | 1.36% | Most-frequent or explicit `"Missing"` level |
| `Teacher_Quality` | 78 | 1.18% | Most-frequent or explicit `"Missing"` level |
| `Distance_from_Home` | 67 | 1.01% | Most-frequent or explicit `"Missing"` level |

- [ ] Impute these three columns within the training pipeline. The EDA showed that NaN groups in `Teacher_Quality` and `Distance_from_Home` have mean scores at or below the lowest named category and reduced standard deviations, suggesting missingness may not be random.
- [ ] Add missingness indicator flags for all three columns and evaluate whether they carry predictive signal during model selection.
- [ ] Fit all imputers on training data only to prevent data leakage.

### 6.3 Duplicate & Leakage Checks

- [ ] The EDA confirmed 0 duplicate rows — no deduplication step is needed.
- [ ] Confirm that no post-exam information leaks into the predictors. `Previous_Scores` refers to prior assessments and is valid.
- [ ] Ensure `Exam_Score` is never included in the feature matrix.

### 6.4 Feature Encoding

The EDA identified two encoding groups based on cardinality and variable semantics:

**Ordinal features (8 columns)** — these showed consistent score gradients across ordered levels (e.g., `Parental_Involvement` High→Medium→Low spans ~1.7 points, `Access_to_Resources` spans ~1.9 points):

- [ ] `Parental_Involvement` (Low < Medium < High)
- [ ] `Access_to_Resources` (Low < Medium < High)
- [ ] `Motivation_Level` (Low < Medium < High)
- [ ] `Teacher_Quality` (Low < Medium < High)
- [ ] `Family_Income` (Low < Medium < High)
- [ ] `Peer_Influence` (Negative < Neutral < Positive)
- [ ] `Parental_Education_Level` (High School < College < Postgraduate)
- [ ] `Distance_from_Home` (Far < Moderate < Near)
- [ ] Test both ordinal encoding (preserving order) and one-hot encoding. Use cross-validation to determine which performs better.

**Nominal features (5 binary columns)** — no meaningful ordering; suitable for one-hot encoding:

- [ ] `Extracurricular_Activities` (Yes/No)
- [ ] `Internet_Access` (Yes/No — note the heavy class imbalance: 92.4% Yes)
- [ ] `School_Type` (Private/Public — near-zero score difference observed)
- [ ] `Learning_Disabilities` (Yes/No — 10.5% Yes, ~1.1-point score gap)
- [ ] `Gender` (Female/Male — no meaningful score difference)

### 6.5 Numeric Feature Handling

All 6 numeric predictors are complete, with no missing values. The EDA revealed varying scales and distribution shapes:

| Feature | Mean | Std | Range | Skewness | Kurtosis |
| :--- | ---: | ---: | :--- | ---: | ---: |
| `Attendance` | 79.98 | 11.55 | 60–100 | 0.01 | -1.19 |
| `Hours_Studied` | 19.98 | 5.99 | 1–44 | 0.01 | 0.02 |
| `Previous_Scores` | 75.07 | 14.40 | 50–100 | -0.00 | -1.19 |
| `Tutoring_Sessions` | 1.49 | 1.23 | 0–8 | 0.82 | 0.64 |
| `Sleep_Hours` | 7.03 | 1.47 | 4–10 | -0.02 | -0.50 |
| `Physical_Activity` | 2.97 | 1.03 | 0–6 | -0.03 | -0.06 |

- [ ] Scale numeric variables for linear and distance-based models. `Attendance` and `Previous_Scores` have platykurtic distributions (kurtosis -1.19); `Tutoring_Sessions` is right-skewed (0.82). Consider robust scaling if linear model residuals indicate sensitivity.
- [ ] Tree-based models (CatBoost, XGBoost) do not require scaling — apply scaling conditionally via the pipeline.

### 6.6 Pipeline Architecture & Model Selection

- [ ] Use a `ColumnTransformer` to apply different transformations to numeric, ordinal, and nominal columns within a single pipeline, preventing preprocessing leakage.
- [ ] Establish a mean-prediction baseline to set the floor for model comparison.
- [ ] Include both a linear model and a tree-based model. The EDA showed that `Attendance` (r=0.581) and `Hours_Studied` have clear linear relationships, but `Sleep_Hours` (r=-0.017) and `Physical_Activity` show near-zero linear correlation — they may still contribute through nonlinear interactions that tree-based models can capture.
- [ ] Use `Tutoring_Sessions` mean scores (ranging from 66.49 at 0 sessions to 71.67 at 6 sessions) as a validation signal — the relationship appears monotonic but nonlinear.
- [ ] Evaluate all models using MAE, RMSE, and \(R^2\).
- [ ] Inspect residuals and prediction performance across low (<65), middle (65–69), and high (>69) score ranges separately. The target is concentrated around 67 (skewness 1.64, kurtosis 10.58), so aggregate metrics alone may mask poor performance at the tails.
- [ ] Use cross-validation during model selection to assess generalization.
- [ ] Confirm that all preprocessing steps — imputation, encoding, scaling — are fitted only on the training partition in every fold.

---

## 7. Final Findings and Modeling Decisions

### 7.1 Dataset Profile

The dataset contains **6,607 student records** across **20 columns** (7 numeric, 13 categorical) with **zero duplicates** and **235 total missing values** concentrated in three categorical columns. The target variable `Exam_Score` is an integer with no missing values, a mean of 67.24, a median of 67.00, and an observed range of 55–101. The distribution is highly concentrated around the high 60s (skewness 1.64, kurtosis 10.58), with a maximum of 101 that requires validation before training.

### 7.2 Key Predictive Signals

**Numeric features — ranked by Pearson correlation with `Exam_Score`:**

1. `Attendance` (r=0.581) — the strongest linear predictor. Each unit of attendance corresponds to a measurable increase in exam score across the observed range.
2. `Hours_Studied` — the second-strongest linear association, with a consistent positive trend visible in scatter plots.
3. `Previous_Scores` and `Tutoring_Sessions` — weaker positive correlations. `Tutoring_Sessions` shows a monotonic but nonlinear pattern in mean-score analysis (66.49 at 0 sessions rising to 71.67 at 6 sessions).
4. `Sleep_Hours` (r=-0.017) and `Physical_Activity` — near-zero linear correlation with the target. These may still contribute through interactions in tree-based models.

**Categorical features — ranked by High-vs-Low mean score spread:**

1. `Access_to_Resources` (~1.9-point spread) and `Parental_Involvement` (~1.7-point spread) — the strongest categorical separations, both with consistent ordinal gradients.
2. `Parental_Education_Level` (~1.1 points), `Peer_Influence` (~1.1 points), `Learning_Disabilities` (~1.1 points), and `Distance_from_Home` (~1.1 points) — moderate separations with ordinal patterns.
3. `School_Type` (~0.08 points) and `Gender` (~0.01 points) — negligible separations. These features are unlikely to add predictive value on their own but should be retained for potential interaction effects.

### 7.3 Data Quality Decisions

1. **No duplicate rows** were found — deduplication is not needed.
2. **Missing values** are limited to `Parental_Education_Level` (90), `Teacher_Quality` (78), and `Distance_from_Home` (67). The NaN groups tend to score at or below the lowest named category, suggesting missingness may carry information. Impute with most-frequent or an explicit `"Missing"` level and add indicator flags.
3. **The maximum `Exam_Score` of 101** is above the typical concentration range and should be confirmed as valid before training. If valid, retain it; if invalid, document and handle it during data cleaning.
4. **No multicollinearity concerns** were flagged among the numeric predictors in the correlation heatmap.

### 7.4 Modeling Strategy

1. **Problem type:** Supervised numeric regression predicting `Exam_Score`.
2. **Model approach:** Train both a linear model (to leverage the clear linear relationships from `Attendance` and `Hours_Studied`) and a tree-based model (CatBoost or XGBoost, to capture nonlinear effects, interactions, and the contributions of weakly-correlated features like `Sleep_Hours`). The linear model can extrapolate beyond the training range; the tree model cannot — using both provides complementary coverage.
3. **Evaluation metrics:** MAE (interpretable average error), RMSE (penalizes large errors), and \(R^2\) (explained variance relative to a mean-prediction baseline).
4. **Evaluation approach:** Assess performance across the full score range, not only near the mean. The concentrated target distribution means a naive mean predictor will appear competitive on aggregate metrics while failing at the tails. Residual analysis is required.
5. **Leakage prevention:** All imputation, encoding, and scaling must be fitted exclusively on training data in every cross-validation fold. The pipeline must use `ColumnTransformer` to enforce this separation.
6. **Feature retention:** Retain all 19 features for initial modeling, including weak predictors (`School_Type`, `Gender`, `Sleep_Hours`, `Physical_Activity`). Let model selection and cross-validation determine which features to drop rather than pre-filtering based on univariate screening alone.

### 7.5 Next Steps

This report documents findings from the raw-data EDA phase. The next stages are:

1. Implement the data transformation pipeline in `src/components/data_transformation.py` following the blueprint in Section 6.
2. Implement model training and evaluation in `src/components/model_trainer.py`.
3. Validate that model predictions generalize to unseen data and that the pipeline preserves schema consistency end-to-end.

All subsequent modeling conclusions should be based on validated model performance, not on the exploratory associations documented here.
