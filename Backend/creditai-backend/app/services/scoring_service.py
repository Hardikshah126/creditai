"""
Scoring Service
===============
Loads the trained XGBoost model and converts the feature dict from the agent
into a 0-100 credit score + risk tier + score breakdown cards.
"""
from __future__ import annotations

import json
import os
from typing import Optional

import joblib
import numpy as np

from app.ml.train_model import FEATURE_COLS, MODEL_PATH

_model = None   # lazy-loaded


def _get_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise RuntimeError(
                "ML model not found. Run: python -m app.ml.train_model"
            )
        _model = joblib.load(MODEL_PATH)
    return _model


def _fill_defaults(features: dict) -> dict:
    """Replace None values with sensible defaults so the model always gets numbers."""
    defaults = {
        "utility_payment_streak_months": 0,
        "utility_on_time_rate":           0.5,
        "avg_monthly_recharge_usd":       5.0,
        "recharge_consistency_score":     0.5,
        "rent_payment_consistency":       0.5,
        "upi_tx_frequency_per_month":     2.0,
        "avg_monthly_tx_volume_usd":      50.0,
        "income_stability_score":         0.5,
        "employment_type":                1,
        "num_dependents":                 1,
        "had_informal_loan":              0,
        "data_completeness_score":        0.5,
    }
    filled = {k: (features.get(k) if features.get(k) is not None else defaults[k])
              for k in FEATURE_COLS}
    return filled


def _compute_completeness(features: dict) -> float:
    provided = sum(1 for k in FEATURE_COLS if features.get(k) is not None)
    return round(provided / len(FEATURE_COLS), 2)


def predict(raw_features: dict) -> dict:
    """
    Returns:
        score          int  0-100
        risk_tier      str  "low"|"medium"|"high"
        ml_probability float
        score_breakdown list[dict]  – matches SignalCard schema
    """
    features = dict(raw_features)
    features["data_completeness_score"] = _compute_completeness(features)

    filled = _fill_defaults(features)
    row = np.array([[filled[k] for k in FEATURE_COLS]], dtype=float)

    model = _get_model()
    prob = float(model.predict_proba(row)[0][1])

    # Scale probability to 0-100, clamp
    score = int(round(min(max(prob * 100, 1), 99)))

    risk_tier = "low" if score > 70 else ("medium" if score >= 40 else "high")

    breakdown = _build_breakdown(filled, score)
    return {
        "score": score,
        "risk_tier": risk_tier,
        "ml_probability": round(prob, 4),
        "score_breakdown": breakdown,
    }


def _build_breakdown(f: dict, total_score: int) -> list[dict]:
    """
    Build the four SignalCard objects that match the frontend's expected shape.
    Contributions are approximated from feature values.
    """

    def strength(val: float) -> str:
        if val >= 0.75: return "strong"
        if val >= 0.55: return "good"
        if val >= 0.35: return "moderate"
        return "weak"

    util_rate = f["utility_on_time_rate"]
    util_streak = min(f["utility_payment_streak_months"] / 24, 1.0)
    util_combined = (util_rate * 0.6 + util_streak * 0.4)

    recharge_val = min(f["recharge_consistency_score"], 1.0)
    tx_freq = min(f["upi_tx_frequency_per_month"] / 30, 1.0)
    tx_vol = min(f["avg_monthly_tx_volume_usd"] / 300, 1.0)
    tx_combined = tx_freq * 0.5 + tx_vol * 0.5

    income_val = f["income_stability_score"]

    # Contributions sum to total_score (roughly)
    weights = [0.33, 0.25, 0.22, 0.20]
    contributions = [int(round(total_score * w)) for w in weights]

    streak_months = int(f["utility_payment_streak_months"])
    avg_recharge = round(f["avg_monthly_recharge_usd"], 1)

    return [
        {
            "title": "Utility Payments",
            "icon": "Zap",
            "contribution": contributions[0],
            "strength": strength(util_combined),
            "percent": int(util_combined * 100),
            "detail": f"{streak_months} months of payment history detected",
        },
        {
            "title": "Mobile Recharge",
            "icon": "Smartphone",
            "contribution": contributions[1],
            "strength": strength(recharge_val),
            "percent": int(recharge_val * 100),
            "detail": f"Avg. ${avg_recharge}/month in recharges",
        },
        {
            "title": "Transaction Activity",
            "icon": "ArrowLeftRight",
            "contribution": contributions[2],
            "strength": strength(tx_combined),
            "percent": int(tx_combined * 100),
            "detail": f"{int(f['upi_tx_frequency_per_month'])} transactions/month on average",
        },
        {
            "title": "Income Stability",
            "icon": "TrendingUp",
            "contribution": contributions[3],
            "strength": strength(income_val),
            "percent": int(income_val * 100),
            "detail": "Based on self-reported income and employment type",
        },
    ]
