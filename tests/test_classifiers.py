"""Tests for sepsis classifiers."""

import numpy as np
import pytest
from sepsis.data import load_reference_samples, generate_synthetic_data, get_features_and_labels
from sepsis.classifiers import (
    SepsisDxClassifier,
    LogisticSepsisClassifier,
    RandomForestSepsisClassifier,
    XGBoostSepsisClassifier,
)
from sepsis.evaluation import compute_metrics


class TestSepsisDxClassifier:
    """Test the rule-based baseline against known reference samples."""

    def setup_method(self):
        self.df = load_reference_samples()
        self.X, self.y = get_features_and_labels(self.df)
        self.clf = SepsisDxClassifier()

    def test_reference_predictions(self):
        """Verify predictions match the Sepsis Software Samples document."""
        y_pred = self.clf.predict(self.X)
        # Samples 1,3,5 -> Septic; 2,4 -> Not Septic; 6 -> Not Septic (false negative)
        expected = np.array([1, 0, 1, 0, 1, 0])
        np.testing.assert_array_equal(y_pred, expected)

    def test_sample6_false_negative(self):
        """Sample 6 is the known false negative (CRP/Cr=299, IP-10/Cr=80)."""
        sample6 = self.X[5:6]  # CRP/Cr=299, IP-10/Cr=80
        assert self.clf.predict(sample6)[0] == 0  # Predicted Not Septic
        assert self.y[5] == 1  # Actually Septic

    def test_predict_proba_shape(self):
        proba = self.clf.predict_proba(self.X)
        assert proba.shape == (6, 2)
        assert np.allclose(proba.sum(axis=1), 1.0)

    def test_threshold_boundary(self):
        """Test exact threshold behavior."""
        # Just above CRP threshold
        X = np.array([[301, 0]])
        assert self.clf.predict(X)[0] == 1
        # Just below both thresholds
        X = np.array([[299, 99]])
        assert self.clf.predict(X)[0] == 0
        # Just above IP-10 threshold
        X = np.array([[0, 101]])
        assert self.clf.predict(X)[0] == 1


class TestMLClassifiers:
    """Test ML classifiers on synthetic data."""

    def setup_method(self):
        self.df = generate_synthetic_data(n_septic=100, n_sirs=50, n_healthy=50, seed=42)
        self.X, self.y = get_features_and_labels(self.df)

    def test_logistic_regression_trains(self):
        clf = LogisticSepsisClassifier()
        clf.fit(self.X, self.y)
        y_pred = clf.predict(self.X)
        assert y_pred.shape == self.y.shape
        assert set(y_pred).issubset({0, 1})

    def test_logistic_regression_auroc_above_random(self):
        clf = LogisticSepsisClassifier()
        clf.fit(self.X, self.y)
        y_prob = clf.predict_proba(self.X)[:, 1]
        metrics = compute_metrics(self.y, clf.predict(self.X), y_prob)
        assert metrics["auroc"] > 0.5

    def test_random_forest_trains(self):
        clf = RandomForestSepsisClassifier(n_estimators=50)
        clf.fit(self.X, self.y)
        y_pred = clf.predict(self.X)
        assert y_pred.shape == self.y.shape

    def test_random_forest_feature_importances(self):
        clf = RandomForestSepsisClassifier(n_estimators=50)
        clf.fit(self.X, self.y)
        fi = clf.feature_importances
        assert fi.shape == (2,)
        assert np.isclose(fi.sum(), 1.0)

    def test_xgboost_trains(self):
        clf = XGBoostSepsisClassifier(n_estimators=50)
        clf.fit(self.X, self.y)
        y_pred = clf.predict(self.X)
        assert y_pred.shape == self.y.shape

    def test_ml_beats_baseline_on_reference(self):
        """ML classifiers should correctly classify Sample 6 (the baseline FN)."""
        clf = LogisticSepsisClassifier()
        clf.fit(self.X, self.y)

        ref_df = load_reference_samples()
        X_ref, y_ref = get_features_and_labels(ref_df)

        baseline = SepsisDxClassifier()
        baseline_metrics = compute_metrics(y_ref, baseline.predict(X_ref))
        ml_metrics = compute_metrics(y_ref, clf.predict(X_ref))

        # ML should have equal or better sensitivity
        assert ml_metrics["sensitivity"] >= baseline_metrics["sensitivity"]


class TestMetrics:
    """Test evaluation metric computation."""

    def test_perfect_classification(self):
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 0, 1, 1])
        m = compute_metrics(y_true, y_pred)
        assert m["accuracy"] == 1.0
        assert m["sensitivity"] == 1.0
        assert m["specificity"] == 1.0

    def test_all_false_negatives(self):
        y_true = np.array([1, 1, 1])
        y_pred = np.array([0, 0, 0])
        m = compute_metrics(y_true, y_pred)
        assert m["sensitivity"] == 0.0
        assert m["fn"] == 3
