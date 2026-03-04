"""Feature engineering and normalization for sepsis classification."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features that may improve classification.

    New features:
    - crp_cr_log: log-transformed CRP/Cr (handles skewed distribution)
    - ip10_cr_clipped: IP-10/Cr with negative values clipped to 0
    - biomarker_sum: CRP/Cr + IP-10/Cr (captures combined elevation)
    - crp_ip10_ratio: CRP/Cr / (IP-10/Cr + 1) (relative marker balance)
    - proximity_score: distance from the SepsisDx decision boundary
    """
    out = df.copy()
    out["crp_cr_log"] = np.log1p(np.clip(out["crp_cr_pg_mg"], 0, None))
    out["ip10_cr_clipped"] = np.clip(out["ip10_cr_pg_mg"], 0, None)
    out["biomarker_sum"] = out["crp_cr_pg_mg"] + out["ip10_cr_pg_mg"]
    out["crp_ip10_ratio"] = out["crp_cr_pg_mg"] / (out["ip10_cr_clipped"] + 1)

    # Proximity to SepsisDx thresholds (higher = closer to septic boundary)
    crp_proximity = out["crp_cr_pg_mg"] / 300.0
    ip10_proximity = out["ip10_cr_pg_mg"] / 100.0
    out["proximity_score"] = np.maximum(crp_proximity, ip10_proximity)

    return out


FEATURE_COLS_BASIC = ["crp_cr_pg_mg", "ip10_cr_pg_mg"]
FEATURE_COLS_EXTENDED = [
    "crp_cr_pg_mg",
    "ip10_cr_pg_mg",
    "crp_cr_log",
    "ip10_cr_clipped",
    "biomarker_sum",
    "crp_ip10_ratio",
    "proximity_score",
]


def scale_features(
    X_train: np.ndarray, X_test: np.ndarray | None = None
) -> tuple[np.ndarray, np.ndarray | None, StandardScaler]:
    """Standardize features using training set statistics."""
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test) if X_test is not None else None
    return X_train_scaled, X_test_scaled, scaler
