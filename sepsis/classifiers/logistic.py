"""Logistic Regression classifier for sepsis detection."""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


class LogisticSepsisClassifier:
    """L2-regularized logistic regression on urine ELISA biomarkers.

    Advantages over the rule-based SepsisDx:
    - Learns a smooth decision boundary instead of hard thresholds
    - Captures the combined effect of both biomarkers (not just OR logic)
    - Produces calibrated probability estimates
    - Addresses the false-negative problem for borderline samples
    """

    def __init__(self, C: float = 1.0, class_weight: str = "balanced"):
        self.C = C
        self.class_weight = class_weight
        self._scaler = StandardScaler()
        self._model = LogisticRegression(
            C=C,
            class_weight=class_weight,
            solver="lbfgs",
            max_iter=1000,
            random_state=42,
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LogisticSepsisClassifier":
        X_scaled = self._scaler.fit_transform(X)
        self._model.fit(X_scaled, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X_scaled = self._scaler.transform(X)
        return self._model.predict(X_scaled)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X_scaled = self._scaler.transform(X)
        return self._model.predict_proba(X_scaled)

    @property
    def coefficients(self) -> np.ndarray:
        return self._model.coef_[0]

    @property
    def intercept(self) -> float:
        return self._model.intercept_[0]

    def get_params(self, deep: bool = True) -> dict:
        return {"C": self.C, "class_weight": self.class_weight}

    def __repr__(self) -> str:
        return f"LogisticSepsisClassifier(C={self.C})"
