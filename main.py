#!/usr/bin/env python3
"""SepsisClassifier — ML-based sepsis detection from urine ELISA biomarkers.

Compares urine-based CRP/Cr and IP-10/Cr classifiers against the blood-based
gold standard (blood culture + Sepsis-3 criteria with SOFA >= 2).

Usage:
    python main.py                    # Full pipeline with synthetic data
    python main.py --data path.csv    # Use custom clinical data
    python main.py --reference-only   # Evaluate on 6 reference samples only
    python main.py --no-plots         # Skip visualization
    python main.py --tune             # Run hyperparameter tuning
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
    NeuralNetSepsisClassifier,
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


def run_full_pipeline(data_path: str | None = None, show_plots: bool = True, run_tuning: bool = False) -> None:
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

    # Define classifiers — now includes Neural Network
    classifiers_basic = {
        "SepsisDx (Baseline)": SepsisDxClassifier(),
        "Logistic Regression": LogisticSepsisClassifier(C=1.0),
        "Random Forest": RandomForestSepsisClassifier(n_estimators=200, max_depth=5),
        "Neural Network": NeuralNetSepsisClassifier(hidden_layers=(32, 16, 8)),
    }

    classifiers_extended = {
        "XGBoost (Extended)": XGBoostSepsisClassifier(n_estimators=200, max_depth=4),
        "Neural Net (Extended)": NeuralNetSepsisClassifier(hidden_layers=(64, 32, 16)),
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

    # ── Hyperparameter Tuning ──
    if run_tuning:
        _run_tuning(X_basic, X_extended, y)

    # ── Threshold Optimization ──
    _run_threshold_optimization(classifiers_basic, X_basic, y)

    # ── Calibration Analysis ──
    _run_calibration_analysis(classifiers_basic, X_basic, y, show_plots)

    # ── SHAP Explainability ──
    _run_shap_analysis(classifiers_basic, X_basic, y, show_plots)

    # ── Model Export ──
    _run_model_export(classifiers_basic, X_basic, y)

    # Train final models on full data for visualization
    if show_plots:
        _generate_plots(classifiers_basic, X_basic, y, benchmarks)

    # ── Predict on Reference Samples with Exported Model ──
    _demo_prediction_api()

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


def _run_tuning(X_basic: np.ndarray, X_extended: np.ndarray, y: np.ndarray) -> None:
    """Run hyperparameter grid search for all tunable models."""
    from sepsis.tuning import tune_logistic, tune_random_forest, tune_xgboost

    print_header("Hyperparameter Tuning (Grid Search)")

    print("\nTuning Logistic Regression...")
    lr_result = tune_logistic(X_basic, y)
    print(f"  Best params: {lr_result['best_params']}")
    print(f"  Best AUROC:  {lr_result['best_auroc']:.4f}")

    print("\nTuning Random Forest...")
    rf_result = tune_random_forest(X_basic, y)
    print(f"  Best params: {rf_result['best_params']}")
    print(f"  Best AUROC:  {rf_result['best_auroc']:.4f}")

    print("\nTuning XGBoost...")
    xgb_result = tune_xgboost(X_extended, y)
    print(f"  Best params: {xgb_result['best_params']}")
    print(f"  Best AUROC:  {xgb_result['best_auroc']:.4f}")


def _run_threshold_optimization(classifiers: dict, X: np.ndarray, y: np.ndarray) -> None:
    """Optimize classification thresholds for each model."""
    from sepsis.tuning import optimize_all_strategies

    print_header("Threshold Optimization")
    print("(Optimizing for clinical use: minimize missed sepsis cases)")

    for name, clf in classifiers.items():
        if name.startswith("SepsisDx"):
            continue

        clf.fit(X, y)
        y_prob = clf.predict_proba(X)[:, 1]
        results = optimize_all_strategies(y, y_prob)

        print(f"\n{name}:")
        for _, row in results.iterrows():
            print(f"  {row['strategy']:30s}  threshold={row['optimal_threshold']:.3f}  "
                  f"sens={row['sensitivity']:.3f}  spec={row['specificity']:.3f}  "
                  f"F1={row['f1_score']:.3f}")


def _run_calibration_analysis(classifiers: dict, X: np.ndarray, y: np.ndarray, show_plots: bool) -> None:
    """Compute and display calibration metrics."""
    from sepsis.tuning import compute_calibration

    print_header("Calibration Analysis")
    print("(ECE = Expected Calibration Error, lower is better)")

    cal_data = {}
    for name, clf in classifiers.items():
        clf.fit(X, y)
        y_prob = clf.predict_proba(X)[:, 1]
        cal = compute_calibration(y, y_prob)
        cal_data[name] = (y, y_prob)
        print(f"  {name:30s}  ECE = {cal['ece']:.4f}")

    if show_plots:
        try:
            from sepsis.visualization import plot_calibration_curves, plot_threshold_analysis
            plot_calibration_curves(cal_data, save=True)

            # Threshold analysis for best ML model
            for name in ["Logistic Regression", "Random Forest", "Neural Network"]:
                if name in classifiers:
                    clf = classifiers[name]
                    clf.fit(X, y)
                    y_prob = clf.predict_proba(X)[:, 1]
                    plot_threshold_analysis(y, y_prob, model_name=name, save=True)
        except ImportError:
            pass


def _run_shap_analysis(classifiers: dict, X: np.ndarray, y: np.ndarray, show_plots: bool) -> None:
    """Run SHAP explainability analysis on the best models."""
    from sepsis.explainability import (
        compute_shap_values,
        compute_shap_tree,
        explain_single_patient,
        print_patient_explanation,
        plot_shap_summary,
        plot_shap_bar,
        plot_shap_waterfall,
        plot_shap_dependence,
    )

    print_header("SHAP Explainability Analysis")
    feature_names = ["CRP/Cr", "IP-10/Cr"]

    # Use Random Forest (tree-based SHAP is fast)
    rf = classifiers.get("Random Forest")
    if rf is None:
        print("  Skipping — no Random Forest classifier found")
        return

    rf.fit(X, y)

    print("\nComputing SHAP values (Random Forest)...")
    try:
        explanation = compute_shap_tree(rf, X, feature_names)
    except Exception:
        print("  TreeExplainer failed, falling back to KernelExplainer...")
        explanation = compute_shap_values(rf, X, feature_names, background_size=100)

    # Mean absolute SHAP values
    shap_vals = explanation.values
    if shap_vals.ndim > 2:
        shap_vals = shap_vals[:, :, 1]  # Class 1 for binary
    mean_shap = np.abs(shap_vals).mean(axis=0)
    print("\nMean |SHAP| feature importance:")
    for fname, val in sorted(zip(feature_names, mean_shap), key=lambda x: -x[1]):
        print(f"  {fname:15s}: {val:.4f}")

    # Explain reference samples (especially the tricky Sample 6)
    print("\nExplaining reference samples:")
    ref_df = load_reference_samples()
    X_ref, y_ref = get_features_and_labels(ref_df)

    rng = np.random.default_rng(42)
    bg_idx = rng.choice(len(X), size=min(100, len(X)), replace=False)
    background = X[bg_idx]

    for i in range(len(X_ref)):
        label = f"Sample {ref_df.iloc[i]['sample_id']} ({ref_df.iloc[i]['clinical_status']})"
        expl = explain_single_patient(rf, X_ref[i], feature_names, background, label)
        print_patient_explanation(expl)

    if show_plots:
        print("\nGenerating SHAP plots...")
        try:
            plot_shap_summary(explanation, title="SHAP Summary — Random Forest", save=True)
            plt_close()
            plot_shap_bar(explanation, title="Mean |SHAP| — Random Forest", save=True)
            plt_close()
            # Waterfall for a septic and non-septic sample
            septic_idx = np.where(y == 1)[0][0]
            nonseptic_idx = np.where(y == 0)[0][0]
            plot_shap_waterfall(explanation, septic_idx,
                                title="SHAP Waterfall — Septic Patient", filename="shap_waterfall_septic.png")
            plt_close()
            plot_shap_waterfall(explanation, nonseptic_idx,
                                title="SHAP Waterfall — Non-Septic Patient", filename="shap_waterfall_nonseptic.png")
            plt_close()
            plot_shap_dependence(explanation, feature="CRP/Cr", save=True)
            plt_close()
            plot_shap_dependence(explanation, feature="IP-10/Cr", save=True)
            plt_close()
            print("  SHAP plots saved to output/")
        except Exception as e:
            print(f"  SHAP plot error: {e}")


def _run_model_export(classifiers: dict, X: np.ndarray, y: np.ndarray) -> None:
    """Export all trained models to disk."""
    from sepsis.model_export import export_all_models, list_exported_models

    print_header("Model Export")
    feature_names = ["crp_cr_pg_mg", "ip10_cr_pg_mg"]

    # Get optimal thresholds (Youden's J) for each model
    from sepsis.tuning import optimize_threshold
    thresholds = {}
    for name, clf in classifiers.items():
        if name.startswith("SepsisDx"):
            thresholds[name] = 0.5
            continue
        clf.fit(X, y)
        y_prob = clf.predict_proba(X)[:, 1]
        opt = optimize_threshold(y, y_prob, strategy="max_youden")
        thresholds[name] = opt["optimal_threshold"]

    export_all_models(classifiers, X, y, feature_names, thresholds)

    print("\nExported models:")
    for m in list_exported_models():
        print(f"  {m['name']:30s}  AUROC={m['auroc']:.4f}  threshold={m['threshold']:.3f}")


def _demo_prediction_api() -> None:
    """Demo the prediction API on reference samples."""
    from sepsis.model_export import SepsisPredictor, list_exported_models

    print_header("Prediction API Demo")

    models = list_exported_models()
    if not models:
        print("  No exported models found")
        return

    # Use Random Forest
    rf_models = [m for m in models if "random_forest" in m["name"]]
    model_name = rf_models[0]["name"] if rf_models else models[0]["name"]

    predictor = SepsisPredictor.from_exported(model_name)
    print(f"Using model: {model_name}")

    # Predict on notable samples
    test_cases = [
        ("Sample 1 (Septic, clear)", 994.2, 33.5),
        ("Sample 4 (Healthy)", 272.8, -5.4),
        ("Sample 6 (Septic, borderline)", 299.0, 80.0),
        ("New patient (moderate CRP)", 350.0, 45.0),
    ]

    for label, crp_cr, ip10_cr in test_cases:
        result = predictor.predict_sample(crp_cr=crp_cr, ip10_cr=ip10_cr)
        print(f"\n  {label}:")
        print(f"    ML Prediction: {result['prediction']} (prob={result['probability']:.3f}, risk={result['risk_level']})")
        print(f"    SepsisDx:      {result['sepsisdx_comparison']}")
        print(f"    Note: {result['clinical_note']}")


def plt_close():
    """Close all matplotlib figures to free memory."""
    import matplotlib.pyplot as plt
    plt.close("all")


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

    # Decision boundary for each model (only for 2-feature models)
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
    parser.add_argument("--tune", action="store_true", help="Run hyperparameter grid search (slower)")
    args = parser.parse_args()

    if args.reference_only:
        evaluate_reference_samples()
    else:
        evaluate_reference_samples()
        run_full_pipeline(data_path=args.data, show_plots=not args.no_plots, run_tuning=args.tune)

    print_header("Done")


if __name__ == "__main__":
    main()
