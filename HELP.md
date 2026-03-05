# SepsisClassifier User Manual

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Main Pipeline (main.py)](#main-pipeline)
5. [Data Simulator](#data-simulator)
6. [Using Exported Models](#using-exported-models)
7. [Understanding the Output](#understanding-the-output)
8. [Input Data Format](#input-data-format)
9. [Classifiers](#classifiers)
10. [SHAP Explainability](#shap-explainability)
11. [Threshold Optimization](#threshold-optimization)
12. [Generated Plots](#generated-plots)
13. [Running Tests](#running-tests)
14. [Troubleshooting](#troubleshooting)
15. [Glossary](#glossary)

---

## Introduction

SepsisClassifier is a machine learning system for detecting sepsis from **urine ELISA biomarker** measurements. It uses two urinary biomarker ratios — CRP/Creatinine and IP-10/Creatinine — to classify patients as septic or non-septic.

The system is validated against the **blood-based gold standard**: positive blood culture combined with Sepsis-3 criteria (SOFA score >= 2).

### Why urine?

Traditional sepsis detection relies on blood draws and lab cultures, which are invasive and slow. Urine-based ELISA testing offers a non-invasive, rapid alternative. This software improves on the existing rule-based SepsisDx classifier by using machine learning to catch borderline cases that hard-threshold rules miss.

---

## Installation

### Prerequisites

- Python 3.10 or later
- pip package manager

### Setup

```bash
# Clone the repository
git clone https://github.com/gilblankenship/SepsisClassifier.git
cd SepsisClassifier

# Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate    # macOS/Linux
# .venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

| Package | Purpose |
|---------|---------|
| numpy | Numerical computation |
| pandas | Data manipulation |
| scikit-learn | ML classifiers, metrics, cross-validation |
| xgboost | Gradient boosting classifier |
| matplotlib | Plot generation |
| seaborn | Enhanced visualizations |
| shap | Model explainability |
| openpyxl | Excel file support |

---

## Quick Start

```bash
# Run the full pipeline with default synthetic data (300 samples)
python main.py

# Run with a larger simulated dataset
python main.py --data data/simulated_5000.csv

# Quick evaluation on the 6 reference samples only
python main.py --reference-only

# Full pipeline without generating plots (faster)
python main.py --data data/simulated_5000.csv --no-plots

# Full pipeline with hyperparameter grid search (slower, more thorough)
python main.py --data data/simulated_5000.csv --tune
```

---

## Main Pipeline

The main pipeline (`main.py`) runs the following steps in order:

### 1. Reference Sample Evaluation

Evaluates all classifiers on the 6 clinically validated reference samples from the Sepsis Software Samples paper. This always runs first as a sanity check.

### 2. Data Loading

Loads training data from one of three sources:
- **CSV file** (via `--data path/to/file.csv`) — your own clinical or simulated data
- **Default synthetic data** — 300 samples generated automatically if no file is specified

### 3. Cross-Validation

Runs stratified 5-fold cross-validation for all classifiers on:
- **Basic features**: CRP/Creatinine and IP-10/Creatinine (2 features)
- **Extended features**: Basic features plus 5 engineered features (7 total)

Reports AUROC, sensitivity, specificity, and F1 score with standard deviations.

### 4. Literature Benchmark Comparison

Compares urine ELISA classifier performance against published blood-based biomarker AUROC values from the literature.

### 5. Threshold Optimization

For each ML classifier, finds the optimal classification threshold using four clinical strategies (see [Threshold Optimization](#threshold-optimization)).

### 6. Calibration Analysis

Computes the Expected Calibration Error (ECE) for each model to assess how trustworthy the predicted probabilities are.

### 7. SHAP Explainability

Computes SHAP values for the Random Forest classifier and generates per-feature importance rankings and per-patient explanations (see [SHAP Explainability](#shap-explainability)).

### 8. Model Export

Trains all classifiers on the full dataset and exports them to the `models/` directory as serialized `.pkl` files with JSON metadata (see [Using Exported Models](#using-exported-models)).

### 9. Prediction API Demo

Demonstrates the `SepsisPredictor` API on notable samples, including the borderline Sample 6 that the rule-based system misses.

### 10. Final Validation

Validates all trained models against the 6 reference samples and reports any misclassifications.

### Command-Line Options

| Flag | Description |
|------|-------------|
| `--data PATH` | Path to a CSV file with clinical data (see [Input Data Format](#input-data-format)) |
| `--reference-only` | Only evaluate on the 6 reference samples; skip the full pipeline |
| `--no-plots` | Skip all plot generation (faster execution) |
| `--tune` | Run hyperparameter grid search before training (significantly slower) |

---

## Data Simulator

The data simulator generates realistic synthetic urine biomarker datasets for training and testing. It is located at `data_simulator/simulate_urine_biomarkers.py`.

### Basic Usage

```bash
cd data_simulator

# Generate 500 samples (default)
python simulate_urine_biomarkers.py

# Generate 5000 samples
python simulate_urine_biomarkers.py -n 5000

# Save to a specific file
python simulate_urine_biomarkers.py -n 2000 -o ../data/my_dataset.csv
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `-n`, `--num-samples` | 500 | Total number of samples to generate |
| `--profile` | general | Patient population profile: `general`, `icu`, or `pediatric` |
| `--noise` | medium | Noise level: `low`, `medium`, or `high` |
| `--extended` | off | Include 5 additional proteomics biomarkers |
| `--metadata` | off | Save a JSON metadata file alongside the CSV |
| `--seed` | 42 | Random seed for reproducibility |
| `-o`, `--output` | auto | Output CSV file path (auto-generated if not specified) |

### Population Profiles

| Profile | Description |
|---------|-------------|
| `general` | General hospital population. Standard biomarker distributions. |
| `icu` | ICU patients. Higher baseline inflammation, lower creatinine (renal impairment), more elevated biomarkers in septic patients. |
| `pediatric` | Pediatric patients. Lower creatinine, slightly different biomarker ranges. |

### Noise Levels

| Level | Multiplier | Use Case |
|-------|------------|----------|
| `low` | 0.7x | Clean data, testing ideal performance |
| `medium` | 1.0x | Realistic clinical variation |
| `high` | 1.5x | Stress-testing classifier robustness |

### Extended Biomarkers

When `--extended` is enabled, the simulator adds 5 proteomics-derived biomarker fold-changes based on iTRAQ data:

| Biomarker | Septic Fold-Change | Source |
|-----------|-------------------|--------|
| Serum Amyloid A | ~6.87x | iTRAQ proteomics |
| Haptoglobin | ~3.23x | iTRAQ proteomics |
| Resistin | ~3.64x | iTRAQ proteomics |
| LRG1 | ~5.85x | iTRAQ proteomics |
| Alpha-1-acid Glycoprotein | ~4.06x | iTRAQ proteomics |

### Examples

```bash
# ICU cohort with high noise and extended biomarkers
python simulate_urine_biomarkers.py -n 3000 --profile icu --noise high --extended --metadata

# Reproducible pediatric dataset
python simulate_urine_biomarkers.py -n 1000 --profile pediatric --seed 123 -o pediatric.csv

# Large general population dataset for robust training
python simulate_urine_biomarkers.py -n 10000 --profile general --noise medium -o ../data/large_dataset.csv
```

---

## Using Exported Models

After running the main pipeline, trained models are saved to the `models/` directory. Each model consists of two files:

- `<model_name>.pkl` — serialized classifier (Python pickle)
- `<model_name>_meta.json` — metadata including parameters, threshold, features, and training metrics

### Available Models

| Model File | Description |
|-----------|-------------|
| `random_forest.pkl` | Random Forest (typically best overall performance) |
| `logistic_regression.pkl` | Logistic Regression (fast, well-calibrated) |
| `neural_network.pkl` | Neural Network MLP (best calibration) |
| `sepsisdx_baseline.pkl` | Rule-based SepsisDx baseline |

### Single Patient Prediction

```python
from sepsis.model_export import SepsisPredictor

# Load the best model
predictor = SepsisPredictor.from_exported("random_forest")

# Predict from urine ELISA measurements
result = predictor.predict_sample(crp_cr=450.0, ip10_cr=85.0)

# Access results
print(result["prediction"])      # "Septic" or "Not Septic"
print(result["probability"])     # 0.0 to 1.0
print(result["risk_level"])      # "LOW", "MODERATE", "HIGH", or "VERY HIGH"
print(result["threshold_used"])  # Classification threshold used
print(result["clinical_note"])   # Actionable clinical guidance
print(result["sepsisdx_comparison"])  # What the rule-based system would say
```

### Prediction Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `prediction` | str | "Septic" or "Not Septic" |
| `probability` | float | Probability of sepsis (0.0-1.0) |
| `risk_level` | str | LOW (<0.2), MODERATE (0.2-0.5), HIGH (0.5-0.8), VERY HIGH (>0.8) |
| `threshold_used` | float | The classification threshold applied |
| `model` | str | Name of the model used |
| `input` | dict | The input biomarker values |
| `sepsisdx_comparison` | str | What the rule-based SepsisDx system would predict |
| `clinical_note` | str | Brief clinical context and guidance |

### Custom Threshold

You can override the model's optimized threshold:

```python
# Use a lower threshold to catch more sepsis cases (higher sensitivity)
result = predictor.predict_sample(crp_cr=280.0, ip10_cr=75.0, threshold=0.3)
```

### Batch Prediction

For predicting multiple patients from a DataFrame:

```python
import pandas as pd
from sepsis.model_export import SepsisPredictor

predictor = SepsisPredictor.from_exported("random_forest")

# Load your data (must have crp_cr_pg_mg and ip10_cr_pg_mg columns)
df = pd.read_csv("patient_samples.csv")

# Predict all patients
results = predictor.predict_batch(df)

# New columns added:
#   ml_probability      — probability of sepsis
#   ml_prediction       — "Septic" or "Not Septic"
#   ml_risk_level       — LOW / MODERATE / HIGH / VERY HIGH
#   sepsisdx_prediction — rule-based system comparison
#   models_agree        — True/False whether ML and SepsisDx agree

# Save results
results.to_csv("predictions.csv", index=False)
```

### Listing Exported Models

```python
from sepsis.model_export import list_exported_models

for model in list_exported_models():
    print(f"{model['name']:30s}  AUROC={model['auroc']:.4f}  threshold={model['threshold']:.3f}")
```

### Loading a Model Directly

```python
from sepsis.model_export import load_model

classifier, metadata = load_model("random_forest")

# Use the classifier directly
import numpy as np
X = np.array([[450.0, 85.0], [100.0, 10.0]])
probabilities = classifier.predict_proba(X)[:, 1]
predictions = classifier.predict(X)
```

---

## Understanding the Output

### Console Output Sections

When you run `python main.py --data data/simulated_5000.csv`, you will see:

1. **Reference Sample Evaluation** — Shows predictions vs gold standard for 6 reference samples. Look for "FN (missed sepsis)" entries — the baseline SepsisDx always misses Sample 6.

2. **Cross-Validation Results** — Table of AUROC, sensitivity, specificity, and F1 for each classifier, averaged over 5 folds with standard deviations. Higher is better for all metrics.

3. **Literature Benchmarks** — Comparison showing that urine ELISA classifiers (AUROC ~0.99) outperform blood-based methods like Procalcitonin (0.84) and Presepsin (0.87).

4. **Threshold Optimization** — Four optimization strategies per model showing the trade-off between sensitivity and specificity at different thresholds.

5. **Calibration Analysis** — ECE (Expected Calibration Error) per model. Lower ECE means the predicted probabilities are more trustworthy. Neural Network typically has the best calibration.

6. **SHAP Analysis** — Feature importance rankings and per-patient explanations showing how each biomarker contributes to each prediction.

7. **Model Export** — Confirmation of exported model files with their AUROC and threshold values.

8. **Prediction API Demo** — Live predictions on notable samples including the borderline Sample 6.

9. **Final Validation** — Each model's predictions on the 6 reference samples. All ML models should correctly classify all 6, including Sample 6.

### Key Metrics

| Metric | What It Means | Clinical Importance |
|--------|--------------|---------------------|
| **AUROC** | Area under the ROC curve (0.5=random, 1.0=perfect) | Overall discriminative ability |
| **Sensitivity** | True positive rate (catches septic patients) | Critical — missed sepsis can be fatal |
| **Specificity** | True negative rate (avoids false alarms) | Reduces unnecessary treatment |
| **F1 Score** | Harmonic mean of precision and sensitivity | Balanced performance measure |
| **ECE** | Expected Calibration Error | How trustworthy the probability estimates are |

---

## Input Data Format

### Required Columns

To use your own clinical data with `--data`, your CSV must contain these columns:

| Column | Type | Description |
|--------|------|-------------|
| `crp_cr_pg_mg` | float | CRP/Creatinine ratio in pg/mg |
| `ip10_cr_pg_mg` | float | IP-10/Creatinine ratio in pg/mg |
| `clinical_status` | str | One of: "Septic", "SIRS", or "Healthy" |

### Optional Columns

| Column | Type | Description |
|--------|------|-------------|
| `sample_id` | int/str | Sample identifier |
| `gold_standard_label` | int | 0 = not septic, 1 = septic (auto-derived from clinical_status if missing) |

### Label Mapping

The system maps clinical statuses to binary labels:
- **"Septic"** -> 1 (positive)
- **"SIRS"** -> 0 (negative)
- **"Healthy"** -> 0 (negative)

### Example CSV

```csv
sample_id,clinical_status,crp_cr_pg_mg,ip10_cr_pg_mg
1,Septic,994.2,33.5
2,SIRS,234.2,-2.6
3,Healthy,272.8,-5.4
4,Septic,299.0,80.0
```

---

## Classifiers

### SepsisDx Baseline (Rule-Based)

The original rule-based classifier from the Sepsis Software Samples paper:
- **Rule**: CRP/Cr > 300 **OR** IP-10/Cr > 100 -> Septic
- **Limitation**: Uses hard thresholds, so borderline cases just below the thresholds (e.g., CRP/Cr=299, IP-10/Cr=80) are missed.

### Logistic Regression

- L2-regularized logistic regression with internal feature scaling
- Fast to train, produces well-calibrated probabilities
- Good baseline ML model

### Random Forest

- Ensemble of 200 decision trees (max depth 5)
- Handles non-linear decision boundaries
- Provides feature importance rankings
- Typically the best overall performer

### XGBoost (Extended Features)

- Gradient boosting with 200 estimators
- Uses all 7 features (basic + engineered)
- Automatic class imbalance handling via `scale_pos_weight`

### Neural Network

- Feed-forward MLP with architecture: 32 -> 16 -> 8 -> output
- ReLU activation, Adam optimizer, early stopping
- Automatic minority class oversampling
- Best calibration (lowest ECE)

---

## SHAP Explainability

SHAP (SHapley Additive exPlanations) values show how each biomarker contributes to individual predictions. This is critical for clinical trust — clinicians need to understand *why* a model makes a particular prediction, not just *what* it predicts.

### How to Read SHAP Values

- **Positive SHAP value** -> feature pushes prediction toward "Septic"
- **Negative SHAP value** -> feature pushes prediction toward "Not Septic"
- **Larger absolute value** -> stronger influence on the prediction

### Example: Borderline Sample 6

```
Sample 6 (Septic):
  Prediction:  Septic (prob=0.971)
  Base rate:   0.426
  Feature contributions:
    IP-10/Cr     =  80.00  ->  +0.5922 (increases sepsis risk)
    CRP/Cr       = 299.00  ->  -0.0475 (decreases sepsis risk)
```

This shows that IP-10/Cr=80 (elevated but below the SepsisDx threshold of 100) is the primary driver pushing the prediction toward septic. The ML model has learned that 80 pg/mg is still clinically significant, unlike the hard threshold rule.

### Generated SHAP Plots

All SHAP plots are saved to the `output/` directory:

| File | Description |
|------|-------------|
| `shap_summary.png` | Beeswarm plot showing feature impact distribution across all patients |
| `shap_bar.png` | Mean absolute SHAP values per feature |
| `shap_waterfall_septic.png` | Prediction breakdown for a septic patient |
| `shap_waterfall_nonseptic.png` | Prediction breakdown for a non-septic patient |
| `shap_dependence_crp_cr.png` | CRP/Cr value vs its SHAP impact |
| `shap_dependence_ip-10_cr.png` | IP-10/Cr value vs its SHAP impact |

---

## Threshold Optimization

The default classification threshold of 0.5 is not always optimal for clinical use. The pipeline evaluates four strategies:

### Strategies

| Strategy | Goal | Best For |
|----------|------|----------|
| **max_f1** | Maximize F1 score | Balanced precision/sensitivity |
| **max_sensitivity_90spec** | Maximum sensitivity while keeping specificity >= 90% | Screening: catch as many cases as possible with acceptable false alarm rate |
| **max_youden** | Maximize Youden's J (sensitivity + specificity - 1) | Optimal balance between sensitivity and specificity |
| **min_missed** | Minimize false negatives (specificity >= 80%) | Critical care: never miss a sepsis case |

### Choosing a Strategy

- **For screening** (e.g., emergency department triage): use `max_sensitivity_90spec` or `min_missed` — missing sepsis is more dangerous than a false alarm.
- **For confirmation** (e.g., before starting antibiotics): use `max_f1` or `max_youden` — you want balanced accuracy.
- **For research**: use `max_youden` for the statistically optimal cutpoint.

The exported models use the `max_youden` threshold by default. You can override it when making predictions:

```python
result = predictor.predict_sample(crp_cr=280.0, ip10_cr=75.0, threshold=0.3)
```

---

## Generated Plots

All plots are saved to the `output/` directory in PNG format (150 DPI).

| File | Description |
|------|-------------|
| `roc_curves.png` | ROC curves for all classifiers with blood-based literature benchmarks |
| `confusion_matrices.png` | Side-by-side confusion matrices for all classifiers |
| `decision_boundary_*.png` | 2D decision boundary for each classifier with SepsisDx threshold lines overlaid |
| `feature_importance.png` | Random Forest feature importance bar chart |
| `calibration_curves.png` | Calibration (reliability) diagrams and prediction distributions |
| `threshold_analysis_*.png` | Sensitivity/specificity/F1 across thresholds for each ML model |
| `shap_summary.png` | SHAP beeswarm summary plot |
| `shap_bar.png` | Mean absolute SHAP values |
| `shap_waterfall_septic.png` | SHAP waterfall for a septic patient |
| `shap_waterfall_nonseptic.png` | SHAP waterfall for a non-septic patient |
| `shap_dependence_*.png` | SHAP dependence plots per feature |

---

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run a specific test class
python -m pytest tests/test_classifiers.py::TestSepsisDxClassifier -v

# Run with coverage (if pytest-cov is installed)
python -m pytest tests/ --cov=sepsis --cov-report=term-missing
```

### Test Suite

The test suite (`tests/test_classifiers.py`) contains 12 tests in 3 classes:

| Test Class | Tests | What It Validates |
|------------|-------|-------------------|
| `TestSepsisDxClassifier` | 4 | Reference sample predictions, Sample 6 false negative, predict_proba shape, threshold boundaries |
| `TestMLClassifiers` | 6 | Training succeeds, AUROC above random, feature importances, ML beats baseline on reference samples |
| `TestMetrics` | 2 | Perfect classification metrics, all-false-negative edge case |

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'sepsis'"

Make sure you are running from the project root directory (`SepsisClassifier/`), not from a subdirectory.

### "ModuleNotFoundError: No module named 'shap'"

Install SHAP: `pip install shap`

Or install all dependencies: `pip install -r requirements.txt`

### "FileNotFoundError: Model not found"

You need to run the full pipeline first to export models:
```bash
python main.py --data data/simulated_5000.csv
```

### Pipeline runs slowly

- Use `--no-plots` to skip visualization (saves time on SHAP and decision boundary plots)
- Don't use `--tune` unless you need hyperparameter optimization (grid search is slow)
- For quick testing, use a smaller dataset or `--reference-only`

### "TreeExplainer failed, falling back to KernelExplainer"

This is normal — the system automatically falls back to a model-agnostic SHAP method. KernelExplainer is slower but works with all classifier types.

### Plots not generating

Ensure matplotlib is installed and you have a working display backend. On headless servers, matplotlib uses the "Agg" backend automatically, which saves files but does not display them. Check the `output/` directory for saved plots.

---

## Glossary

| Term | Definition |
|------|------------|
| **AUROC** | Area Under the Receiver Operating Characteristic curve. Measures overall classifier discrimination. Range: 0.5 (random) to 1.0 (perfect). |
| **Calibration** | How well predicted probabilities match actual outcomes. A well-calibrated model that predicts 70% sepsis probability should be correct ~70% of the time. |
| **CRP** | C-Reactive Protein. An acute-phase inflammatory biomarker. Elevated in infection and inflammation. |
| **CRP/Cr** | CRP concentration normalized by urinary creatinine. Expressed in pg/mg. Corrects for urine dilution. |
| **ECE** | Expected Calibration Error. Measures the average gap between predicted probabilities and actual outcomes. Lower is better. |
| **ELISA** | Enzyme-Linked Immunosorbent Assay. A plate-based assay for detecting and quantifying biomarkers in urine or blood. |
| **F1 Score** | Harmonic mean of precision and sensitivity. Balances false positives and false negatives. |
| **Gold Standard** | The reference test against which the urine classifier is validated — positive blood culture + Sepsis-3 criteria (SOFA >= 2). |
| **IP-10** | Interferon gamma-induced Protein 10 (CXCL10). A chemokine elevated in sepsis. |
| **IP-10/Cr** | IP-10 concentration normalized by urinary creatinine. Expressed in pg/mg. |
| **NPV** | Negative Predictive Value. Probability that a "Not Septic" prediction is correct. |
| **PPV** | Positive Predictive Value (Precision). Probability that a "Septic" prediction is correct. |
| **Sensitivity** | True Positive Rate (Recall). Proportion of actual sepsis cases correctly identified. Critical for sepsis where missed cases can be fatal. |
| **Sepsis-3** | The Third International Consensus Definitions for Sepsis (2016). Defines sepsis as life-threatening organ dysfunction caused by a dysregulated host response to infection, with SOFA score >= 2. |
| **SepsisDx** | The original rule-based classifier. Predicts septic if CRP/Cr > 300 OR IP-10/Cr > 100. |
| **SHAP** | SHapley Additive exPlanations. A game-theoretic approach to explain individual predictions by computing the contribution of each feature. |
| **SIRS** | Systemic Inflammatory Response Syndrome. Inflammation without infection. Classified as non-septic in this system. |
| **SOFA** | Sequential Organ Failure Assessment. A scoring system for organ dysfunction. SOFA >= 2 is part of the Sepsis-3 definition. |
| **Specificity** | True Negative Rate. Proportion of non-septic patients correctly identified. |
| **Youden's J** | Sensitivity + Specificity - 1. A single metric for optimal threshold selection. Maximized when both sensitivity and specificity are high. |
