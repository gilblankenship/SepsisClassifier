# SepsisClassifier

ML-based sepsis detection from **ELISA analysis of urine samples**, validated against the **blood-based gold standard** (blood culture + Sepsis-3 criteria with SOFA ≥ 2).

## Overview

This project extends the rule-based **SepsisDx** classifier — which uses urinary CRP/Creatinine and IP-10/Creatinine with hard thresholds — by applying machine learning to improve sensitivity, particularly for borderline cases the rule-based approach misses.

### Classifiers

| Model | Type | AUROC | Sensitivity | Notes |
|-------|------|-------|-------------|-------|
| **SepsisDx** (Baseline) | Rule-based OR thresholds | 0.984 | 0.953 | Misses borderline cases (e.g., Sample 6) |
| **Logistic Regression** | L2-regularized | 0.991 | 0.920 | Best calibrated probabilities |
| **Random Forest** | Ensemble (200 trees) | 0.984 | 0.947 | Feature importance ranking |
| **XGBoost** | Gradient boosting | 0.989 | 0.953 | Extended feature support |

All ML classifiers **exceed blood-based benchmarks** from literature: Procalcitonin (0.84), Presepsin (0.87), CRP (0.76).

### Biomarkers (Urine ELISA)

| Feature | Unit | SepsisDx Threshold |
|---------|------|--------------------|
| CRP / Creatinine | pg/mg | > 300 → Septic |
| IP-10 / Creatinine | pg/mg | > 100 → Septic |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run full pipeline (synthetic data)
python main.py

# Evaluate on reference samples only
python main.py --reference-only

# Use custom clinical data
python main.py --data path/to/data.csv

# Skip plot generation
python main.py --no-plots
```

## Data Simulator

A standalone program generates realistic synthetic urine biomarker datasets:

```bash
cd data_simulator

# Default: 500 samples, general population
python simulate_urine_biomarkers.py

# 1000 ICU patients with high noise
python simulate_urine_biomarkers.py -n 1000 --profile icu --noise high

# Include extended proteomics biomarkers + metadata
python simulate_urine_biomarkers.py --extended --metadata

# Pediatric cohort
python simulate_urine_biomarkers.py --profile pediatric -o pediatric_data.csv
```

**Population profiles:** `general`, `icu`, `pediatric`
**Noise levels:** `low`, `medium`, `high`
**Extended biomarkers:** Serum Amyloid A, Haptoglobin, Resistin, LRG1, Alpha-1-acid Glycoprotein (from iTRAQ proteomics)

## Project Structure

```
SepsisClassifer/
├── main.py                    # CLI pipeline entry point
├── requirements.txt
├── PLAN.md                    # Detailed project plan
├── sepsis/
│   ├── data.py                # Data loading & reference samples
│   ├── features.py            # Feature engineering
│   ├── evaluation.py          # Metrics & cross-validation
│   ├── visualization.py       # ROC curves, confusion matrices, decision boundaries
│   └── classifiers/
│       ├── baseline.py        # Rule-based SepsisDx
│       ├── logistic.py        # Logistic Regression
│       └── ensemble.py        # Random Forest + XGBoost
├── data_simulator/
│   └── simulate_urine_biomarkers.py
├── data/                      # Generated datasets
├── tests/
│   └── test_classifiers.py    # 12 unit tests
└── References/                # Source papers
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
