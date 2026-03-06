"""Data loading, synthetic generation, and preprocessing for sepsis classification."""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple

# Clinical status encoding
LABEL_MAP = {"Healthy": 0, "SIRS": 0, "Septic": 1}
LABEL_NAMES = {0: "Not Septic", 1: "Septic"}


def load_reference_samples() -> pd.DataFrame:
    """Return the 6 reference samples from the Sepsis Software Samples document.

    Columns: sample_id, clinical_status, creatinine_nmol_ml,
             crp_cr_pg_mg, ip10_cr_pg_mg, gold_standard_label
    """
    data = {
        "sample_id": [1, 2, 3, 4, 5, 6],
        "clinical_status": ["Septic", "SIRS", "Septic", "Healthy", "Septic", "Septic"],
        "creatinine_nmol_ml": [22.36, 28.4, 20.6, 25.6, 24.3, 23.4],
        "crp_cr_pg_mg": [994.2, 234.2, 1141.0, 272.8, 1320.3, 299.0],
        "ip10_cr_pg_mg": [33.5, -2.6, 214.0, -5.4, 58.06, 80.0],
    }
    df = pd.DataFrame(data)
    df["gold_standard_label"] = df["clinical_status"].map(LABEL_MAP)
    return df


def generate_synthetic_data(
    n_septic: int = 150,
    n_sirs: int = 75,
    n_healthy: int = 75,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate synthetic urine ELISA data based on literature-derived distributions.

    Distributions are parameterized from the reference samples and published biomarker
    ranges for CRP and IP-10 in urine, normalized to creatinine.
    """
    rng = np.random.default_rng(seed)
    records = []

    # Septic patients: elevated CRP/Cr and variable IP-10/Cr
    for _ in range(n_septic):
        creatinine = rng.normal(23.0, 3.0)
        creatinine = max(creatinine, 5.0)
        # Most septic patients have CRP/Cr > 300, but some borderline
        crp_cr = rng.lognormal(np.log(800), 0.6)
        # IP-10/Cr: bimodal — some elevated, some not
        if rng.random() < 0.4:
            ip10_cr = rng.lognormal(np.log(150), 0.5)
        else:
            ip10_cr = rng.normal(40, 30)
        records.append(("Septic", creatinine, crp_cr, ip10_cr))

    # SIRS patients: moderate CRP/Cr, low IP-10/Cr
    for _ in range(n_sirs):
        creatinine = rng.normal(25.0, 4.0)
        creatinine = max(creatinine, 5.0)
        crp_cr = rng.lognormal(np.log(200), 0.4)
        ip10_cr = rng.normal(10, 15)
        records.append(("SIRS", creatinine, crp_cr, ip10_cr))

    # Healthy controls: low CRP/Cr and IP-10/Cr
    for _ in range(n_healthy):
        creatinine = rng.normal(26.0, 3.5)
        creatinine = max(creatinine, 5.0)
        crp_cr = rng.lognormal(np.log(100), 0.5)
        ip10_cr = rng.normal(0, 10)
        records.append(("Healthy", creatinine, crp_cr, ip10_cr))

    df = pd.DataFrame(records, columns=[
        "clinical_status", "creatinine_nmol_ml", "crp_cr_pg_mg", "ip10_cr_pg_mg"
    ])
    df["sample_id"] = range(1, len(df) + 1)
    df["gold_standard_label"] = df["clinical_status"].map(LABEL_MAP)
    return df


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load clinical data from CSV.

    Required columns: clinical_status, crp_cr_pg_mg, ip10_cr_pg_mg
    Optional columns: creatinine_nmol_ml, sample_id, gold_standard_label
    """
    df = pd.read_csv(path)
    # Derive clinical_status from sepsis_label if missing
    if "clinical_status" not in df.columns and "sepsis_label" in df.columns:
        df["clinical_status"] = df["sepsis_label"].map({1: "Septic", 0: "Healthy"})
    required = {"clinical_status", "crp_cr_pg_mg", "ip10_cr_pg_mg"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")
    if "creatinine_nmol_ml" not in df.columns:
        df["creatinine_nmol_ml"] = 0.0
    if "gold_standard_label" not in df.columns:
        df["gold_standard_label"] = df["clinical_status"].map(LABEL_MAP)
    if "sample_id" not in df.columns:
        df["sample_id"] = range(1, len(df) + 1)
    return df


def get_features_and_labels(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Extract feature matrix X and label vector y from a dataframe."""
    X = df[["crp_cr_pg_mg", "ip10_cr_pg_mg"]].values
    y = df["gold_standard_label"].values
    return X, y


def load_proteomics_supplement(
    path: str | Path | None = None,
) -> pd.DataFrame:
    """Load the iTRAQ proteomics supplement (45 differentially-expressed proteins)."""
    if path is None:
        path = (
            Path(__file__).resolve().parent.parent
            / "References"
            / "41598_2021_99595_MOESM1_ESM(1).xlsx"
        )
    df = pd.read_excel(path, sheet_name="proteins")
    # Drop empty columns
    df = df.dropna(axis=1, how="all")
    df.columns = ["unused_score", "accession", "name", "peptides_95", "fold_change", "pvalue"]
    return df
