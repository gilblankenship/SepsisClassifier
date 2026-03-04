"""Neural network classifier for sepsis detection."""

from __future__ import annotations

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier


class NeuralNetSepsisClassifier:
    """Feed-forward neural network for sepsis detection.

    Architecture: input → 32 → 16 → 8 → 1 (sigmoid)
    Uses early stopping to prevent overfitting and class weighting
    to handle imbalanced sepsis datasets.
    """

    def __init__(
        self,
        hidden_layers: tuple = (32, 16, 8),
        learning_rate_init: float = 0.001,
        max_iter: int = 500,
        alpha: float = 0.001,
    ):
        self.hidden_layers = hidden_layers
        self.learning_rate_init = learning_rate_init
        self.max_iter = max_iter
        self.alpha = alpha
        self._scaler = StandardScaler()
        self._model = MLPClassifier(
            hidden_layer_sizes=hidden_layers,
            activation="relu",
            solver="adam",
            learning_rate_init=learning_rate_init,
            max_iter=max_iter,
            alpha=alpha,
            early_stopping=True,
            validation_fraction=0.15,
            n_iter_no_change=20,
            random_state=42,
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> "NeuralNetSepsisClassifier":
        X_scaled = self._scaler.fit_transform(X)
        # Manual class weighting via sample replication for MLPClassifier
        # (sklearn MLP doesn't support class_weight directly)
        n_pos = np.sum(y == 1)
        n_neg = np.sum(y == 0)
        if n_pos > 0 and n_neg > 0:
            weight_ratio = n_neg / n_pos
            sample_weight = np.where(y == 1, weight_ratio, 1.0)
            # Oversample minority class indices
            if weight_ratio > 1.5:
                pos_idx = np.where(y == 1)[0]
                extra = np.random.default_rng(42).choice(
                    pos_idx, size=int(n_pos * (weight_ratio - 1)), replace=True
                )
                X_scaled = np.vstack([X_scaled, X_scaled[extra]])
                y = np.concatenate([y, y[extra]])
        self._model.fit(X_scaled, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X_scaled = self._scaler.transform(X)
        return self._model.predict(X_scaled)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X_scaled = self._scaler.transform(X)
        return self._model.predict_proba(X_scaled)

    def get_params(self, deep: bool = True) -> dict:
        return {
            "hidden_layers": self.hidden_layers,
            "learning_rate_init": self.learning_rate_init,
            "max_iter": self.max_iter,
            "alpha": self.alpha,
        }

    def __repr__(self) -> str:
        return f"NeuralNetSepsisClassifier(layers={self.hidden_layers})"
