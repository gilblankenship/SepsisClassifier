# SepsisClassifier — Project Plan

## Overview

ML-based sepsis detection from **ELISA analysis of urine samples**, validated against the
**blood-based "gold standard"** (blood culture + clinical Sepsis-3 criteria with SOFA scoring).

The project extends the rule-based **SepsisDx** classifier (from *Sepsis Software Samples*)
that uses two creatinine-normalized urinary biomarkers — CRP/Cr and IP-10/Cr — with hard
thresholds and a logical-OR decision rule. That baseline has a known false-negative problem
when both markers fall just below their thresholds (e.g., Sample 6: CRP/Cr=299, IP-10/Cr=80).

## Data & Biomarkers

### Primary Features (Urine ELISA)
| Feature | Unit | Baseline Threshold | Direction |
|---------|------|--------------------|-----------|
| Creatinine | nmol/mL | normalizer | — |
| CRP / Creatinine | pg/mg | > 300 | ↑ Septic |
| IP-10 / Creatinine | pg/mg | > 100 | ↑ Septic |

### Labels (Gold Standard — Blood-Based)
- **Septic** — positive blood culture + Sepsis-3 criteria (SOFA ≥ 2)
- **SIRS** — systemic inflammatory response without infection
- **Healthy** — no infection / inflammation

### Supplementary Proteomics (from Excel supplement)
45 differentially-expressed proteins (iTRAQ) including CRP, Serum Amyloid A, Haptoglobin,
Resistin, LRG1. These can serve as candidate features for an expanded model.

## Architecture

```
SepsisClassifer/
├── main.py                  # CLI entry point
├── requirements.txt
├── PLAN.md
├── References/              # Papers & data (read-only)
├── sepsis/
│   ├── __init__.py
│   ├── data.py              # Data loading, synthetic generation, preprocessing
│   ├── features.py          # Feature engineering & normalization
│   ├── classifiers/
│   │   ├── __init__.py
│   │   ├── baseline.py      # Rule-based SepsisDx (OR-threshold)
│   │   ├── logistic.py      # Logistic Regression
│   │   ├── ensemble.py      # Random Forest + XGBoost
│   │   └── neural.py        # Simple feed-forward NN (optional)
│   ├── evaluation.py        # Metrics, ROC, confusion matrix, gold-standard comparison
│   └── visualization.py     # Plots: ROC curves, feature importance, decision boundaries
└── tests/
    └── test_classifiers.py
```

## Classifiers

### 1. Baseline — SepsisDx (Rule-Based)
- CRP/Cr > 300 OR IP-10/Cr > 100 → Septic
- Reproduces the reference classifier for benchmarking

### 2. Logistic Regression
- L2-regularized, trained on CRP/Cr + IP-10/Cr
- Provides interpretable coefficients and probability calibration
- Addresses the hard-boundary false-negative problem

### 3. Random Forest + XGBoost
- Ensemble methods capturing non-linear interactions
- Feature importance ranking
- Hyperparameter tuning via cross-validation

### 4. Neural Network (stretch goal)
- Small feed-forward network (2 → 16 → 8 → 1)
- Sigmoid output for probability estimation

## Evaluation Strategy

All models evaluated against the **blood-based gold standard** labels:

| Metric | Purpose |
|--------|---------|
| AUROC | Overall discriminative ability |
| Sensitivity (Recall) | Critical — minimize missed sepsis cases |
| Specificity | Avoid unnecessary treatment |
| PPV / NPV | Clinical decision utility |
| F1-Score | Balanced precision/recall |
| Confusion Matrix | Per-class error analysis |
| Calibration Curve | Probability reliability |

### Cross-Validation
- Stratified K-Fold (k=5) for robust estimates
- Leave-one-out for small datasets

### Gold Standard Comparison
- Blood culture positivity + Sepsis-3 (SOFA ≥ 2) as ground truth
- Compare urine ELISA classifier performance to blood-based PCT (AUC ~0.84)
  and Presepsin (AUC ~0.87) benchmarks from literature

## Data Strategy

Since only 6 reference samples are provided, the system supports:
1. **Reference samples** — the 6 from Sepsis Software Samples (for validation)
2. **Synthetic data generation** — parameterized distributions based on literature
   biomarker ranges to create training sets
3. **CSV import** — load real clinical data when available

## Implementation Phases

1. **Phase 1**: Core infrastructure — data models, baseline classifier, evaluation
2. **Phase 2**: ML classifiers — logistic regression, ensemble methods
3. **Phase 3**: Visualization, reporting, CLI interface
4. **Phase 4**: Extended features — proteomics integration, neural network
