"""
Train the XGBoost credit scoring model.

Uses synthetic data that mirrors the 12 features the agent extracts.
In production this would be replaced with real labelled data.

Run: python -m app.ml.train_model
"""
from __future__ import annotations

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "scaler.joblib")

FEATURE_COLS = [
    "utility_payment_streak_months",
    "utility_on_time_rate",
    "avg_monthly_recharge_usd",
    "recharge_consistency_score",
    "rent_payment_consistency",
    "upi_tx_frequency_per_month",
    "avg_monthly_tx_volume_usd",
    "income_stability_score",
    "employment_type",
    "num_dependents",
    "had_informal_loan",
    "data_completeness_score",
]


def _generate_synthetic_data(n: int = 5000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    df = pd.DataFrame({
        "utility_payment_streak_months": rng.integers(0, 36, n),
        "utility_on_time_rate":          rng.uniform(0, 1, n),
        "avg_monthly_recharge_usd":       rng.uniform(0, 50, n),
        "recharge_consistency_score":     rng.uniform(0, 1, n),
        "rent_payment_consistency":       rng.uniform(0, 1, n),
        "upi_tx_frequency_per_month":     rng.uniform(0, 60, n),
        "avg_monthly_tx_volume_usd":      rng.uniform(0, 500, n),
        "income_stability_score":         rng.uniform(0, 1, n),
        "employment_type":                rng.integers(0, 4, n),
        "num_dependents":                 rng.integers(0, 4, n),
        "had_informal_loan":              rng.integers(0, 2, n),
        "data_completeness_score":        rng.uniform(0.3, 1.0, n),
    })

    # Deterministic label: good credit if average of key normalised features > 0.5
    score_proxy = (
        df["utility_on_time_rate"] * 0.25
        + df["recharge_consistency_score"] * 0.15
        + df["rent_payment_consistency"] * 0.15
        + df["income_stability_score"] * 0.20
        + (df["utility_payment_streak_months"] / 36) * 0.10
        + (df["employment_type"] / 3) * 0.10
        + df["data_completeness_score"] * 0.05
        - (df["num_dependents"] / 3) * 0.05
        + rng.uniform(-0.1, 0.1, n)   # noise
    )
    df["label"] = (score_proxy > 0.5).astype(int)
    return df


def train() -> None:
    print("Generating synthetic training data…")
    df = _generate_synthetic_data(8000)

    X = df[FEATURE_COLS]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("Training XGBoost…")
    model = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=42,
    )
    model.fit(X_train, y_train)

    auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    print(f"ROC-AUC on test set: {auc:.4f}")

    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    train()
