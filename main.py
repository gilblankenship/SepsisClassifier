#!/usr/bin/env python3
"""SepsisClassifier — ML-based sepsis detection from urine ELISA biomarkers.

Compares urine-based CRP/Cr and IP-10/Cr classifiers against the blood-based
gold standard (blood culture + Sepsis-3 criteria with SOFA >= 2).

Usage:
    python main.py                    # Full pipeline with synthetic data
    python main.py --data path.csv    # Use custom clinical data
    python main.py --reference-only   # Evaluate on 6 reference samples only
    python main.py --no-plots         # Skip visualization
"""

from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

from sepsis.data import (
    load_reference_samples,
    generate_synthetic_data,
    load_csv,
    get_features_and_labels,
)
from sepsis.features import add_engineered_features, FEATURE_COLS_BASIC, FEATURE_COLS_EXTENDED
from sepsis.classifiers import (
    SepsisDxClassifier,
    LogisticSepsisClassifier,
    RandomForestSepsisClassifier,
    XGBoostSepsisClassifier,
)
from sepsis.evaluation import (
    compute_metrics,
    cross_validate,
    compare_models,
    literature_benchmarks,
)


def print_header(text: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def evaluate_reference_samples() -> None:
    """Evaluate all classifiers on the 6 reference samples from the paper."""
    print_header("Reference Sample Evaluation (Sepsis Software Samples)")

    df = load_reference_samples()
    X, y = get_features_and_labels(df)

    print("\nReference Data:")
    print(df[["sample_id", "clinical_status", "crp_cr_pg_mg", "ip10_cr_pg_mg", "gold_standard_label"]].to_string(index=False))

    # Baseline rule-based classifier
    baseline = SepsisDxClassifier()
    y_pred = baseline.predict(X)

    print(f"\n--- SepsisDx (Rule-Based Baseline) ---")
    print(f"Predictions: {y_pred}")
    print(f"Gold Std:    {y}")

    metrics = compute_metrics(y, y_pred)
    print(f"Accuracy:    {metrics['accuracy']:.3f}")
    print(f"Sensitivity: {metrics['sensitivity']:.3f}")
    print(f"Specificity: {metrics['specificity']:.3f}")
    print(f"F1 Score:    {metrics['f1_score']:.3f}")
    print(f"TP={metrics['tp']} FP={metrics['fp']} FN={metrics['fn']} TN={metrics['tn']}")

    # Identify misclassifications
    for i in range(len(y)):
        if y_pred[i] != y[i]:
            status = "FN (missed sepsis)" if y[i] == 1 else "FP (false alarm)"
            print(f"  Sample {df.iloc[i]['sample_id']}: {status} "
                  f"(CRP/Cr={df.iloc[i]['crp_cr_pg_mg']}, IP-10/Cr={df.iloc[i]['ip10_cr_pg_mg']})")


def run_full_pipeline(data_path: str | None = None, show_plots: bool = True) -> None:
    """Run the full training and evaluation pipeline."""
    print_header("SepsisClassifier — Full Pipeline")

    # Load data
    if data_path:
        print(f"\nLoading clinical data from: {data_path}")
        df = load_csv(data_path)
    else:
        print("\nGenerating synthetic training data (n=300)...")
        df = generate_synthetic_data(n_septic=150, n_sirs=75, n_healthy=75)

    print(f"  Total samples: {len(df)}")
    print(f"  Septic: {(df['gold_standard_label'] == 1).sum()}")
    print(f"  Non-Septic: {(df['gold_standard_label'] == 0).sum()}")
    print(f"  Class distribution: {df['clinical_status'].value_counts().to_dict()}")

    # Basic features
    X_basic, y = get_features_and_labels(df)

    # Extended features
    df_ext = add_engineered_features(df)
    X_extended = df_ext[FEATURE_COLS_EXTENDED].values

    # Define classifiers
    classifiers_basic = {
        "SepsisDx (Baseline)": SepsisDxClassifier(),
        "Logistic Regression": LogisticSepsisClassifier(C=1.0),
        "Random Forest": RandomForestSepsisClassifier(n_estimators=200, max_depth=5),
    }

    classifiers_extended = {
        "XGBoost (Extended)": XGBoostSepsisClassifier(n_estimators=200, max_depth=4),
    }

    # Cross-validation comparison — basic features
    print_header("Cross-Validation Results (Basic Features: CRP/Cr, IP-10/Cr)")
    comparison_basic = compare_models(classifiers_basic, X_basic, y, n_splits=5)
    _print_comparison(comparison_basic)

    # Cross-validation — extended features
    print_header("Cross-Validation Results (Extended Features)")
    comparison_ext = compare_models(classifiers_extended, X_extended, y, n_splits=5)
    _print_comparison(comparison_ext)

    # Literature benchmark comparison
    print_header("Comparison with Blood-Based Gold Standard Benchmarks")
    benchmarks = literature_benchmarks()
    print("\nBlood-based biomarker AUROC (from literature):")
    for name, auroc_val in benchmarks.items():
        print(f"  {name}: {auroc_val:.2f}")

    all_comparisons = pd.concat([comparison_basic, comparison_ext], ignore_index=True)
    print("\nUrine ELISA classifier AUROC (this study):")
    for _, row in all_comparisons.iterrows():
        auroc = row.get("auroc_mean")
        if auroc is not None:
            std = row.get("auroc_std", 0)
            print(f"  {row['model']}: {auroc:.3f} +/- {std:.3f}")

    # Train final models on full data for visualization
    if show_plots:
        _generate_plots(classifiers_basic, X_basic, y, benchmarks)

    # Validate against reference samples
    print_header("Final Model Validation on Reference Samples")
    ref_df = load_reference_samples()
    X_ref, y_ref = get_features_and_labels(ref_df)

    for name, clf in classifiers_basic.items():
        clf.fit(X_basic, y)
        y_pred = clf.predict(X_ref)
        y_prob = clf.predict_proba(X_ref)[:, 1]
        metrics = compute_metrics(y_ref, y_pred)
        print(f"\n{name}:")
        print(f"  Predictions: {y_pred}  (Gold Std: {y_ref})")
        print(f"  Sensitivity={metrics['sensitivity']:.3f}  Specificity={metrics['specificity']:.3f}  F1={metrics['f1_score']:.3f}")

        for i in range(len(y_ref)):
            if y_pred[i] != y_ref[i]:
                print(f"  -> Misclassified Sample {ref_df.iloc[i]['sample_id']}: "
                      f"pred={y_pred[i]}, actual={y_ref[i]}, prob={y_prob[i]:.3f}")


def _print_comparison(df: pd.DataFrame) -> None:
    """Pretty-print model comparison table."""
    cols = ["model", "auroc_mean", "sensitivity_mean", "specificity_mean", "f1_score_mean"]
    display = df[[c for c in cols if c in df.columns]].copy()
    for col in display.columns:
        if col != "model" and display[col].dtype == float:
            std_col = col.replace("_mean", "_std")
            if std_col in df.columns:
                display[col] = df.apply(
                    lambda r: f"{r[col]:.3f} +/- {r[std_col]:.3f}" if pd.notna(r[col]) else "N/A",
                    axis=1,
                )
    print(display.to_string(index=False))


def _generate_plots(
    classifiers: dict,
    X: np.ndarray,
    y: np.ndarray,
    benchmarks: dict,
) -> None:
    """Generate all evaluation visualizations."""
    try:
        from sepsis.visualization import (
            plot_roc_curves,
            plot_confusion_matrices,
            plot_decision_boundary,
            plot_feature_importance,
        )
    except ImportError as e:
        print(f"\nSkipping plots (missing dependency: {e})")
        return

    print("\nGenerating plots...")

    # Train all models on full data
    roc_data = {}
    cm_data = {}
    for name, clf in classifiers.items():
        clf.fit(X, y)
        y_pred = clf.predict(X)
        y_prob = clf.predict_proba(X)[:, 1]
        roc_data[name] = (y, y_prob)
        cm_data[name] = (y, y_pred)

    plot_roc_curves(roc_data, benchmarks, save=True)
    plot_confusion_matrices(cm_data, save=True)

    # Decision boundary for each model
    for name, clf in classifiers.items():
        safe_name = name.lower().replace(" ", "_").replace("(", "").replace(")", "")
        plot_decision_boundary(
            clf, X, y,
            title=f"Decision Boundary — {name}",
            filename=f"decision_boundary_{safe_name}.png",
        )

    # Feature importance for Random Forest
    rf = classifiers.get("Random Forest")
    if rf is not None and hasattr(rf, "feature_importances"):
        plot_feature_importance(
            ["CRP/Cr", "IP-10/Cr"],
            rf.feature_importances,
            title="Random Forest — Feature Importance",
        )

    print("  Plots saved to output/")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SepsisClassifier: ML-based sepsis detection from urine ELISA",
    )
    parser.add_argument("--data", type=str, help="Path to CSV with clinical data")
    parser.add_argument("--reference-only", action="store_true", help="Evaluate on reference samples only")
    parser.add_argument("--no-plots", action="store_true", help="Skip plot generation")
    args = parser.parse_args()

    if args.reference_only:
        evaluate_reference_samples()
    else:
        evaluate_reference_samples()
        run_full_pipeline(data_path=args.data, show_plots=not args.no_plots)

    print_header("Done")


if __name__ == "__main__":
    main()
