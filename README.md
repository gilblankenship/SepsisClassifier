# SepsisClassifier

ML-based sepsis detection from **ELISA analysis of urine samples**, validated against the **blood-based gold standard** (blood culture + Sepsis-3 criteria with SOFA >= 2).

## Overview

This project extends the rule-based **SepsisDx** classifier — which uses urinary CRP/Creatinine and IP-10/Creatinine with hard thresholds — by applying machine learning to improve sensitivity, particularly for borderline cases the rule-based approach misses.

### Classifiers

| Model | Type | AUROC | Sensitivity | Specificity | F1 |
|-------|------|-------|-------------|-------------|-----|
| **SepsisDx** (Baseline) | Rule-based OR thresholds | 0.989 | 0.965 | 0.912 | 0.921 |
| **Logistic Regression** | L2-regularized | 0.994 | 0.956 | 0.978 | 0.961 |
| **Random Forest** | Ensemble (200 trees) | 0.995 | 0.964 | 0.979 | 0.966 |
| **Neural Network** | MLP (32-16-8) | 0.995 | 0.953 | 0.986 | 0.966 |
| **XGBoost** (Extended) | Gradient boosting | 0.994 | 0.958 | 0.980 | 0.964 |

All ML classifiers **exceed blood-based benchmarks** from literature: Procalcitonin (0.84), Presepsin (0.87), CRP (0.76), CD64 (0.94).

### Biomarkers (Urine ELISA)

| Feature | Unit | SepsisDx Threshold |
|---------|------|--------------------|
| CRP / Creatinine | pg/mg | > 300 -> Septic |
| IP-10 / Creatinine | pg/mg | > 100 -> Septic |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run full pipeline (synthetic data)
python main.py

# Use custom clinical data
python main.py --data path/to/data.csv

# Evaluate on reference samples only
python main.py --reference-only

# Run with hyperparameter tuning
python main.py --tune

# Skip plot generation
python main.py --no-plots
```

## Using Exported Models

After running the pipeline, trained models are saved to `models/`. Use the prediction API:

```python
from sepsis.model_export import SepsisPredictor

# Load the best model
predictor = SepsisPredictor.from_exported("random_forest")

# Predict a single patient
result = predictor.predict_sample(crp_cr=450.0, ip10_cr=85.0)
print(result["prediction"])    # "Septic" or "Not Septic"
print(result["probability"])   # 0.0-1.0
print(result["risk_level"])    # LOW / MODERATE / HIGH / VERY HIGH
print(result["clinical_note"]) # Actionable guidance

# Batch prediction on a DataFrame
import pandas as pd
df = pd.read_csv("new_samples.csv")  # needs crp_cr_pg_mg, ip10_cr_pg_mg columns
results = predictor.predict_batch(df)
```

## SHAP Explainability

The pipeline generates SHAP-based explanations showing how each biomarker contributes to predictions:

- **Summary plot** — feature impact distribution across all patients
- **Waterfall plots** — per-patient prediction decomposition
- **Dependence plots** — feature value vs SHAP impact

Example output for the borderline Sample 6 (CRP/Cr=299, IP-10/Cr=80):
```
Sample 6 (Septic):
  Prediction:  Septic (prob=0.971)
  Base rate:   0.426
  Feature contributions:
    IP-10/Cr         =      80.00  ->  +0.5922 (increases sepsis risk)
    CRP/Cr           =     299.00  ->  -0.0475 (decreases sepsis risk)
```

The ML model correctly identifies this as septic (97.1% probability) where the rule-based SepsisDx system misses it.

## Data Simulator

A standalone program generates realistic synthetic urine biomarker datasets:

```bash
cd data_simulator

# Default: 500 samples, general population
python simulate_urine_biomarkers.py

# 5000 ICU patients with high noise
python simulate_urine_biomarkers.py -n 5000 --profile icu --noise high

# Include extended proteomics biomarkers + metadata
python simulate_urine_biomarkers.py --extended --metadata

# Pediatric cohort
python simulate_urine_biomarkers.py --profile pediatric -o pediatric_data.csv
```

**Population profiles:** `general`, `icu`, `pediatric`
**Noise levels:** `low`, `medium`, `high`
**Extended biomarkers:** Serum Amyloid A, Haptoglobin, Resistin, LRG1, Alpha-1-acid Glycoprotein (from iTRAQ proteomics)

## Pipeline Features

- **Cross-validation**: Stratified 5-fold CV for all models
- **Threshold optimization**: 4 strategies (max F1, max sensitivity at 90% specificity, Youden's J, min missed)
- **Calibration analysis**: Expected Calibration Error (ECE) per model
- **SHAP explainability**: Feature importance and per-patient explanations
- **Model export**: Serialized models with metadata and prediction API
- **Visualization**: ROC curves, confusion matrices, decision boundaries, calibration plots, threshold analysis

## Project Structure

```
SepsisClassifier/
├── main.py                       # CLI pipeline entry point
├── requirements.txt
├── PLAN.md                       # Detailed project plan
├── sepsis/
│   ├── data.py                   # Data loading & reference samples
│   ├── features.py               # Feature engineering
│   ├── evaluation.py             # Metrics & cross-validation
│   ├── visualization.py          # ROC, confusion matrices, decision boundaries
│   ├── tuning.py                 # Hyperparameter tuning & threshold optimization
│   ├── explainability.py         # SHAP-based model explanations
│   ├── model_export.py           # Model export, import & prediction API
│   └── classifiers/
│       ├── baseline.py           # Rule-based SepsisDx
│       ├── logistic.py           # Logistic Regression
│       ├── ensemble.py           # Random Forest + XGBoost
│       └── neural.py             # Neural Network (MLP)
├── data_simulator/
│   └── simulate_urine_biomarkers.py
├── data/                         # Generated datasets
├── models/                       # Exported trained models
├── output/                       # Generated plots and figures
├── tests/
│   └── test_classifiers.py       # 12 unit tests
└── References/                   # Source papers
```

## Tests

```bash
python -m pytest tests/ -v
```

## References

- Komorowski et al. "Sepsis biomarkers and diagnostic tools with a focus on machine learning" (eBioMedicine, 2022)
- Melegari et al. "Sepsis Biomarkers: What Surgeons Need to Know" (Anesthesia Research, 2025)
- He et al. "Sepsis Biomarkers: Advancements and Clinical Applications" (IJMS, 2024)
- SepsisDx rule-based classifier (Sepsis Software Samples)
