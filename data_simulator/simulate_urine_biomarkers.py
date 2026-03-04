#!/usr/bin/env python3
"""Simulated Urine-Based Biomarker Data Generator for Sepsis Research.

Generates realistic synthetic ELISA urine biomarker datasets with configurable
patient cohort sizes, biomarker distributions, and noise levels. Output is
written to CSV files compatible with the SepsisClassifier pipeline.

Biomarker distributions are parameterized from:
  - Sepsis Software Samples reference (6 clinical samples)
  - Published literature on urinary CRP, IP-10, and creatinine in sepsis
  - iTRAQ proteomics supplement (45 differentially-expressed proteins)

Usage:
    python simulate_urine_biomarkers.py                          # Default: 500 samples
    python simulate_urine_biomarkers.py -n 1000 -o my_data.csv   # Custom size & output
    python simulate_urine_biomarkers.py --profile icu             # ICU patient profile
    python simulate_urine_biomarkers.py --extended                # Include extra biomarkers
    python simulate_urine_biomarkers.py --seed 123 --noise high   # Reproducible, noisy data
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

import numpy as np
import pandas as pd


# ──────────────────────────────────────────────────────────────────────
# Biomarker Distribution Profiles
# ──────────────────────────────────────────────────────────────────────

@dataclass
class BiomarkerProfile:
    """Distribution parameters for a single clinical group."""
    creatinine_mean: float
    creatinine_std: float
    crp_cr_log_mean: float      # log-space mean for CRP/Cr (lognormal)
    crp_cr_log_std: float
    ip10_cr_mean: float
    ip10_cr_std: float
    ip10_cr_elevated_frac: float = 0.0   # fraction with elevated IP-10
    ip10_cr_elevated_mean: float = 0.0
    ip10_cr_elevated_std: float = 0.0


# Default profiles derived from reference samples + literature
PROFILES = {
    "general": {
        "Septic": BiomarkerProfile(
            creatinine_mean=23.0, creatinine_std=3.5,
            crp_cr_log_mean=np.log(800), crp_cr_log_std=0.6,
            ip10_cr_mean=40, ip10_cr_std=30,
            ip10_cr_elevated_frac=0.4,
            ip10_cr_elevated_mean=150, ip10_cr_elevated_std=60,
        ),
        "SIRS": BiomarkerProfile(
            creatinine_mean=25.0, creatinine_std=4.0,
            crp_cr_log_mean=np.log(200), crp_cr_log_std=0.4,
            ip10_cr_mean=10, ip10_cr_std=15,
        ),
        "Healthy": BiomarkerProfile(
            creatinine_mean=26.0, creatinine_std=3.5,
            crp_cr_log_mean=np.log(100), crp_cr_log_std=0.5,
            ip10_cr_mean=0, ip10_cr_std=10,
        ),
    },
    "icu": {
        "Septic": BiomarkerProfile(
            creatinine_mean=18.0, creatinine_std=5.0,  # lower due to renal impairment
            crp_cr_log_mean=np.log(1200), crp_cr_log_std=0.5,
            ip10_cr_mean=80, ip10_cr_std=40,
            ip10_cr_elevated_frac=0.6,
            ip10_cr_elevated_mean=250, ip10_cr_elevated_std=80,
        ),
        "SIRS": BiomarkerProfile(
            creatinine_mean=22.0, creatinine_std=5.0,
            crp_cr_log_mean=np.log(350), crp_cr_log_std=0.45,
            ip10_cr_mean=25, ip10_cr_std=20,
        ),
        "Healthy": BiomarkerProfile(
            creatinine_mean=27.0, creatinine_std=3.0,
            crp_cr_log_mean=np.log(80), crp_cr_log_std=0.4,
            ip10_cr_mean=-2, ip10_cr_std=8,
        ),
    },
    "pediatric": {
        "Septic": BiomarkerProfile(
            creatinine_mean=15.0, creatinine_std=4.0,
            crp_cr_log_mean=np.log(700), crp_cr_log_std=0.7,
            ip10_cr_mean=50, ip10_cr_std=35,
            ip10_cr_elevated_frac=0.35,
            ip10_cr_elevated_mean=130, ip10_cr_elevated_std=50,
        ),
        "SIRS": BiomarkerProfile(
            creatinine_mean=16.0, creatinine_std=3.5,
            crp_cr_log_mean=np.log(180), crp_cr_log_std=0.45,
            ip10_cr_mean=12, ip10_cr_std=12,
        ),
        "Healthy": BiomarkerProfile(
            creatinine_mean=18.0, creatinine_std=3.0,
            crp_cr_log_mean=np.log(70), crp_cr_log_std=0.5,
            ip10_cr_mean=2, ip10_cr_std=8,
        ),
    },
}

# Noise multipliers for biomarker variance
NOISE_LEVELS = {
    "low": 0.7,
    "medium": 1.0,
    "high": 1.5,
}

# Extended biomarkers from proteomics literature (fold-changes from iTRAQ data)
EXTENDED_BIOMARKERS = {
    "serum_amyloid_a_fold": {"Septic": (6.87, 1.5), "SIRS": (2.5, 0.8), "Healthy": (1.0, 0.3)},
    "haptoglobin_fold": {"Septic": (3.23, 0.8), "SIRS": (1.8, 0.5), "Healthy": (1.0, 0.2)},
    "resistin_fold": {"Septic": (3.64, 1.0), "SIRS": (1.5, 0.4), "Healthy": (1.0, 0.2)},
    "lrg1_fold": {"Septic": (5.85, 1.2), "SIRS": (2.0, 0.6), "Healthy": (1.0, 0.3)},
    "alpha1_acid_glycoprotein_fold": {"Septic": (4.06, 0.9), "SIRS": (2.2, 0.5), "Healthy": (1.0, 0.2)},
}


# ──────────────────────────────────────────────────────────────────────
# Data Generation
# ──────────────────────────────────────────────────────────────────────

def generate_group(
    rng: np.random.Generator,
    profile: BiomarkerProfile,
    n: int,
    noise_mult: float = 1.0,
) -> dict[str, np.ndarray]:
    """Generate biomarker values for a single clinical group."""
    creatinine = rng.normal(
        profile.creatinine_mean,
        profile.creatinine_std * noise_mult,
        size=n,
    )
    creatinine = np.clip(creatinine, 3.0, None)

    crp_cr = rng.lognormal(
        profile.crp_cr_log_mean,
        profile.crp_cr_log_std * noise_mult,
        size=n,
    )

    # IP-10/Cr: mixture model for septic patients (bimodal)
    ip10_cr = rng.normal(
        profile.ip10_cr_mean,
        profile.ip10_cr_std * noise_mult,
        size=n,
    )
    if profile.ip10_cr_elevated_frac > 0:
        elevated_mask = rng.random(n) < profile.ip10_cr_elevated_frac
        n_elevated = elevated_mask.sum()
        if n_elevated > 0:
            ip10_cr[elevated_mask] = rng.lognormal(
                np.log(profile.ip10_cr_elevated_mean),
                profile.ip10_cr_elevated_std / profile.ip10_cr_elevated_mean * noise_mult,
                size=n_elevated,
            )

    return {
        "creatinine_nmol_ml": creatinine,
        "crp_cr_pg_mg": crp_cr,
        "ip10_cr_pg_mg": ip10_cr,
    }


def generate_extended_biomarkers(
    rng: np.random.Generator,
    clinical_status: str,
    n: int,
    noise_mult: float = 1.0,
) -> dict[str, np.ndarray]:
    """Generate extended proteomics-derived biomarker values."""
    result = {}
    for marker_name, group_params in EXTENDED_BIOMARKERS.items():
        mean, std = group_params.get(clinical_status, (1.0, 0.3))
        values = rng.lognormal(np.log(mean), std / mean * noise_mult, size=n)
        result[marker_name] = values
    return result


def simulate_dataset(
    n_septic: int = 200,
    n_sirs: int = 100,
    n_healthy: int = 100,
    profile_name: str = "general",
    noise: str = "medium",
    extended: bool = False,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate a complete simulated urine biomarker dataset.

    Args:
        n_septic: Number of septic patient samples.
        n_sirs: Number of SIRS (non-infectious inflammation) samples.
        n_healthy: Number of healthy control samples.
        profile_name: Patient population profile ("general", "icu", "pediatric").
        noise: Noise level ("low", "medium", "high").
        extended: Include extended proteomics-derived biomarkers.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns compatible with the SepsisClassifier pipeline.
    """
    rng = np.random.default_rng(seed)
    noise_mult = NOISE_LEVELS[noise]
    profiles = PROFILES[profile_name]

    groups = [
        ("Septic", n_septic),
        ("SIRS", n_sirs),
        ("Healthy", n_healthy),
    ]

    all_rows = []
    for status, n in groups:
        profile = profiles[status]
        biomarkers = generate_group(rng, profile, n, noise_mult)

        group_df = pd.DataFrame(biomarkers)
        group_df["clinical_status"] = status

        if extended:
            ext = generate_extended_biomarkers(rng, status, n, noise_mult)
            for col, vals in ext.items():
                group_df[col] = vals

        all_rows.append(group_df)

    df = pd.concat(all_rows, ignore_index=True)

    # Shuffle
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    df["sample_id"] = range(1, len(df) + 1)

    # Gold standard labels (blood-based diagnosis as ground truth)
    label_map = {"Healthy": 0, "SIRS": 0, "Septic": 1}
    df["gold_standard_label"] = df["clinical_status"].map(label_map)

    # Add metadata
    df["assay_type"] = "ELISA"
    df["sample_type"] = "urine"

    # Reorder columns
    core_cols = [
        "sample_id", "clinical_status", "gold_standard_label",
        "creatinine_nmol_ml", "crp_cr_pg_mg", "ip10_cr_pg_mg",
        "assay_type", "sample_type",
    ]
    ext_cols = [c for c in df.columns if c not in core_cols]
    df = df[core_cols + ext_cols]

    return df


def generate_metadata(
    n_septic: int,
    n_sirs: int,
    n_healthy: int,
    profile_name: str,
    noise: str,
    extended: bool,
    seed: int,
) -> dict:
    """Generate metadata describing the simulation parameters."""
    return {
        "generator": "simulate_urine_biomarkers.py",
        "version": "1.0.0",
        "parameters": {
            "n_septic": n_septic,
            "n_sirs": n_sirs,
            "n_healthy": n_healthy,
            "total_samples": n_septic + n_sirs + n_healthy,
            "profile": profile_name,
            "noise_level": noise,
            "noise_multiplier": NOISE_LEVELS[noise],
            "extended_biomarkers": extended,
            "seed": seed,
        },
        "biomarkers": {
            "primary": ["crp_cr_pg_mg", "ip10_cr_pg_mg"],
            "normalizer": "creatinine_nmol_ml",
            "extended": list(EXTENDED_BIOMARKERS.keys()) if extended else [],
        },
        "gold_standard": "Blood culture + Sepsis-3 criteria (SOFA >= 2)",
        "assay": "ELISA (Enzyme-Linked Immunosorbent Assay)",
        "sample_type": "Urine",
        "thresholds_reference": {
            "crp_cr_septic": "> 300 pg/mg",
            "ip10_cr_septic": "> 100 pg/mg",
            "source": "Sepsis Software Samples (SepsisDx classifier)",
        },
    }


# ──────────────────────────────────────────────────────────────────────
# Summary Statistics
# ──────────────────────────────────────────────────────────────────────

def print_summary(df: pd.DataFrame) -> None:
    """Print summary statistics for the generated dataset."""
    print("\n" + "=" * 60)
    print("  Generated Dataset Summary")
    print("=" * 60)

    print(f"\nTotal samples: {len(df)}")
    print(f"\nClass distribution:")
    for status in ["Septic", "SIRS", "Healthy"]:
        n = (df["clinical_status"] == status).sum()
        print(f"  {status:8s}: {n:4d} ({100*n/len(df):.1f}%)")

    print(f"\nBiomarker statistics:")
    for col in ["creatinine_nmol_ml", "crp_cr_pg_mg", "ip10_cr_pg_mg"]:
        print(f"\n  {col}:")
        for status in ["Septic", "SIRS", "Healthy"]:
            subset = df.loc[df["clinical_status"] == status, col]
            print(f"    {status:8s}: mean={subset.mean():8.1f}  std={subset.std():7.1f}  "
                  f"min={subset.min():8.1f}  max={subset.max():8.1f}")

    # SepsisDx threshold analysis
    septic = df[df["clinical_status"] == "Septic"]
    above_crp = (septic["crp_cr_pg_mg"] > 300).mean()
    above_ip10 = (septic["ip10_cr_pg_mg"] > 100).mean()
    above_either = ((septic["crp_cr_pg_mg"] > 300) | (septic["ip10_cr_pg_mg"] > 100)).mean()

    print(f"\n  SepsisDx threshold analysis (Septic patients):")
    print(f"    CRP/Cr > 300:         {100*above_crp:.1f}%")
    print(f"    IP-10/Cr > 100:       {100*above_ip10:.1f}%")
    print(f"    Either (OR rule):     {100*above_either:.1f}%")
    print(f"    Missed (both below):  {100*(1-above_either):.1f}%")

    # Check for extended biomarkers
    ext_cols = [c for c in df.columns if c.endswith("_fold")]
    if ext_cols:
        print(f"\n  Extended biomarkers ({len(ext_cols)}):")
        for col in ext_cols:
            septic_mean = df.loc[df["clinical_status"] == "Septic", col].mean()
            healthy_mean = df.loc[df["clinical_status"] == "Healthy", col].mean()
            print(f"    {col:35s}: septic_mean={septic_mean:.2f}  healthy_mean={healthy_mean:.2f}  "
                  f"fold_diff={septic_mean/healthy_mean:.2f}x")


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate simulated urine-based ELISA biomarker data for sepsis research",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python simulate_urine_biomarkers.py                         # 500 samples, general profile
  python simulate_urine_biomarkers.py -n 1000 --profile icu   # 1000 ICU samples
  python simulate_urine_biomarkers.py --extended --noise high  # Extended markers, high noise
  python simulate_urine_biomarkers.py -o training_data.csv     # Custom output filename
        """,
    )
    parser.add_argument(
        "-n", "--total", type=int, default=500,
        help="Total number of samples (default: 500). Split: 40%% septic, 30%% SIRS, 30%% healthy",
    )
    parser.add_argument(
        "--n-septic", type=int, default=None,
        help="Override number of septic samples",
    )
    parser.add_argument(
        "--n-sirs", type=int, default=None,
        help="Override number of SIRS samples",
    )
    parser.add_argument(
        "--n-healthy", type=int, default=None,
        help="Override number of healthy samples",
    )
    parser.add_argument(
        "--profile", choices=list(PROFILES.keys()), default="general",
        help="Patient population profile (default: general)",
    )
    parser.add_argument(
        "--noise", choices=list(NOISE_LEVELS.keys()), default="medium",
        help="Noise level for biomarker variance (default: medium)",
    )
    parser.add_argument(
        "--extended", action="store_true",
        help="Include extended proteomics-derived biomarkers",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "-o", "--output", type=str, default=None,
        help="Output CSV filename (default: simulated_urine_biomarkers_<profile>.csv)",
    )
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="Output directory (default: ../data/)",
    )
    parser.add_argument(
        "--metadata", action="store_true",
        help="Also write a JSON metadata file describing the simulation",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Suppress summary output",
    )
    args = parser.parse_args()

    # Determine sample sizes
    if args.n_septic is not None or args.n_sirs is not None or args.n_healthy is not None:
        n_septic = args.n_septic or int(args.total * 0.4)
        n_sirs = args.n_sirs or int(args.total * 0.3)
        n_healthy = args.n_healthy or int(args.total * 0.3)
    else:
        n_septic = int(args.total * 0.4)
        n_sirs = int(args.total * 0.3)
        n_healthy = args.total - n_septic - n_sirs

    # Generate data
    df = simulate_dataset(
        n_septic=n_septic,
        n_sirs=n_sirs,
        n_healthy=n_healthy,
        profile_name=args.profile,
        noise=args.noise,
        extended=args.extended,
        seed=args.seed,
    )

    # Output path
    output_dir = Path(args.output_dir) if args.output_dir else Path(__file__).parent.parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = args.output or f"simulated_urine_biomarkers_{args.profile}.csv"
    output_path = output_dir / filename

    df.to_csv(output_path, index=False)

    if not args.quiet:
        print_summary(df)
        print(f"\nData written to: {output_path}")
        print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")

    if args.metadata:
        meta = generate_metadata(
            n_septic, n_sirs, n_healthy,
            args.profile, args.noise, args.extended, args.seed,
        )
        meta_path = output_path.with_suffix(".json")
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
        if not args.quiet:
            print(f"  Metadata: {meta_path}")


if __name__ == "__main__":
    main()
