"""Rule-based SepsisDx classifier from the Sepsis Software Samples reference."""

from __future__ import annotations

import numpy as np


class SepsisDxClassifier:
    """Threshold-based classifier using CRP/Cr and IP-10/Cr with logical OR.

    Decision rule (from reference):
        Septic if CRP/Cr > 300 pg/mg  OR  IP-10/Cr > 100 pg/mg
    """

    def __init__(self, crp_cr_threshold: float = 300.0, ip10_cr_threshold: float = 100.0):
        self.crp_cr_threshold = crp_cr_threshold
        self.ip10_cr_threshold = ip10_cr_threshold

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SepsisDxClassifier":
        """No-op — rule-based classifier has no trainable parameters."""
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Classify samples. X columns: [crp_cr_pg_mg, ip10_cr_pg_mg]."""
        crp_cr = X[:, 0]
        ip10_cr = X[:, 1]
        return ((crp_cr > self.crp_cr_threshold) | (ip10_cr > self.ip10_cr_threshold)).astype(int)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Return pseudo-probabilities based on distance from thresholds.

        Uses a sigmoid-like mapping of the max normalized distance to produce
        a continuous score, enabling ROC curve generation for fair comparison.
        """
        crp_norm = X[:, 0] / self.crp_cr_threshold
        ip10_norm = X[:, 1] / self.ip10_cr_threshold
        max_ratio = np.maximum(crp_norm, ip10_norm)
        # Sigmoid centered at threshold (ratio = 1.0)
        prob_septic = 1.0 / (1.0 + np.exp(-5.0 * (max_ratio - 1.0)))
        return np.column_stack([1 - prob_septic, prob_septic])

    def get_params(self, deep: bool = True) -> dict:
        return {
            "crp_cr_threshold": self.crp_cr_threshold,
            "ip10_cr_threshold": self.ip10_cr_threshold,
        }

    def __repr__(self) -> str:
        return (
            f"SepsisDxClassifier(CRP/Cr>{self.crp_cr_threshold}, "
            f"IP-10/Cr>{self.ip10_cr_threshold})"
        )
