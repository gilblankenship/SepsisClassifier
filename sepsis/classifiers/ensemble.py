"""Ensemble classifiers (Random Forest, XGBoost) for sepsis detection."""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler


class RandomForestSepsisClassifier:
    """Random Forest classifier for sepsis detection.

    Captures non-linear biomarker interactions and provides
    feature importance rankings.
    """

    def __init__(
        self,
        n_estimators: int = 200,
        max_depth: int | None = 5,
        class_weight: str = "balanced",
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.class_weight = class_weight
        self._model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            class_weight=class_weight,
            random_state=42,
            n_jobs=-1,
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RandomForestSepsisClassifier":
        self._model.fit(X, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self._model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self._model.predict_proba(X)

    @property
    def feature_importances(self) -> np.ndarray:
        return self._model.feature_importances_

    def get_params(self, deep: bool = True) -> dict:
        return {
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "class_weight": self.class_weight,
        }

    def __repr__(self) -> str:
        return f"RandomForestSepsisClassifier(n={self.n_estimators}, depth={self.max_depth})"


class XGBoostSepsisClassifier:
    """XGBoost gradient-boosted classifier for sepsis detection.

    Typically achieves the best discriminative performance on tabular
    biomarker data (literature reports AUROC 0.84+ for sepsis prediction).
    """

    def __init__(
        self,
        n_estimators: int = 200,
        max_depth: int = 4,
        learning_rate: float = 0.1,
        scale_pos_weight: float | None = None,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.scale_pos_weight = scale_pos_weight
        self._scaler = StandardScaler()
        self._model = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "XGBoostSepsisClassifier":
        import xgboost as xgb

        X_scaled = self._scaler.fit_transform(X)
        spw = self.scale_pos_weight
        if spw is None:
            n_neg = np.sum(y == 0)
            n_pos = np.sum(y == 1)
            spw = n_neg / max(n_pos, 1)

        self._model = xgb.XGBClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            scale_pos_weight=spw,
            eval_metric="logloss",
            random_state=42,
            verbosity=0,
        )
        self._model.fit(X_scaled, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X_scaled = self._scaler.transform(X)
        return self._model.predict(X_scaled)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X_scaled = self._scaler.transform(X)
        return self._model.predict_proba(X_scaled)

    @property
    def feature_importances(self) -> np.ndarray:
        return self._model.feature_importances_

    def get_params(self, deep: bool = True) -> dict:
        return {
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "learning_rate": self.learning_rate,
            "scale_pos_weight": self.scale_pos_weight,
        }

    def __repr__(self) -> str:
        return (
            f"XGBoostSepsisClassifier(n={self.n_estimators}, "
            f"depth={self.max_depth}, lr={self.learning_rate})"
        )
