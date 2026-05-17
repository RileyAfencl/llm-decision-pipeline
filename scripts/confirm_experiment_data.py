# scripts/check_experiment_data.py
from __future__ import annotations

from pathlib import Path

import pandas as pd


CSV_PATH = Path("experiments/temp_stability/results.csv")


def main() -> None:
    df = pd.read_csv(CSV_PATH)

    print(f"Loaded {len(df)} rows from {CSV_PATH}")
    print(f"Shape: {df.shape}")

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nRows by experiment and temperature profile:")
    print(
        df.groupby(
            ["experiment_id", "temperature_profile"]
        ).size()
    )

    print("\nStatus counts:")
    print(df["status"].value_counts(dropna=False))

    print("\nTop missing-value counts:")
    print(
        df.isna()
        .sum()
        .sort_values(ascending=False)
        .head(20)
    )

    print("\nGrade summary by experiment and temperature profile:")
    print(
        df.groupby(
            ["experiment_id", "temperature_profile"]
        )["grade"]
        .agg(["count", "mean", "std", "min", "max"])
    )

    print("\nConfidence summary by experiment and temperature profile:")
    print(
        df.groupby(
            ["experiment_id", "temperature_profile"]
        )["score_confidence"]
        .agg(["count", "mean", "std", "min", "max"])
    )

    print("\nDuration summary by experiment and temperature profile:")
    print(
        df.groupby(
            ["experiment_id", "temperature_profile"]
        )["duration_ms"]
        .agg(["count", "mean", "std", "min", "max"])
    )


if __name__ == "__main__":
    main()