"""
ML Credit Scoring Service.

Uses a trained XGBoost model to score applicants based on
structured features extracted from documents + conversation.

For MVP: ships with a pre-trained proxy model (trained on
Kaggle "Give Me Some Credit" dataset features).
In production: retrain on real alternative data as it accumulates.
"""
import json
import os
import numpy as np
from typing import Optional
import joblib

# Feature order MUST match training — never change without retraining
FEATURE_ORDER = [
    "utility_payment_streak",        # months of consecutive on-time utility payments
    "on_time_payment_rate",          # 0.0 – 1.0
    "avg_monthly_recharge_amount",   # USD
    "recharge_consistency_score",    # 0.0 – 1.0
    "rent_payment_consistency",      # 0.0 – 1.0
    "transaction_frequency",         # transactions per month
    "avg_monthly_transaction_vol",   # USD
    "income_stability_score",        # 0.0 – 1.0 (from conversation)
    "employment_type_encoded",       # employee=3, self_employed=2, daily_wage=1, other=0
    "num_dependents",                # integer
    "has_repaid_informal_loan",      # 0 or 1
    "data_completeness_score",       # 0.0 – 1.0 (how much data we have)
    "months_of_data",                # total months of data provided
]

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../ml/credit_model.joblib")

_model = None


def _load_model():
    global _model
    if _model is None:
        if os.path.exists(MODEL_PATH):
            _model = joblib.load(MODEL_PATH)
        else:
            # Use a simple fallback rule-based scorer for development
            _model = "rule_based"
    return _model


EMPLOYMENT_ENCODING = {
    "employee": 3,
    "self_employed": 2,
    "daily_wage": 1,
    "unemployed": 0,
    "other": 1,
}


def build_feature_vector(
    doc_features: dict,
    conversation_features: dict,
) -> tuple[list[float], float]:
    """
    Merge document-extracted features with conversation-extracted features
    into the fixed-order feature vector expected by the model.

    Returns (feature_vector, data_completeness_score).
    """
    # Merge all sources (conversation features override if present)
    merged = {**doc_features, **conversation_features}

    def safe_float(key: str, default: float = 0.0) -> float:
        v = merged.get(key)
        if v is None:
            return default
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    # Calculate completeness: fraction of non-null features
    non_null = sum(1 for k in FEATURE_ORDER[:-2] if merged.get(k) is not None)
    completeness = non_null / (len(FEATURE_ORDER) - 2)

    employment_raw = merged.get("employment_type", "other")
    employment_enc = EMPLOYMENT_ENCODING.get(str(employment_raw).lower(), 1)

    vector = [
        safe_float("payment_streak_months", 0),
        safe_float("on_time_payment_rate", 0.5),
        safe_float("avg_monthly_recharge_amount", 0),
        safe_float("recharge_consistency_score", 0.5),
        safe_float("rent_payment_consistency", 0.5),
        safe_float("transaction_frequency_per_month", 0),
        safe_float("average_monthly_amount", 0),
        safe_float("income_stability_score", 0.5),
        float(employment_enc),
        safe_float("num_dependents", 2),
        safe_float("has_repaid_informal_loan", 0),
        completeness,
        safe_float("months_of_data", 0),
    ]

    return vector, completeness


def rule_based_score(feature_vector: list[float]) -> float:
    """
    Fallback rule-based scorer for development / when no model is trained.
    Returns a probability between 0.0 and 1.0.
    """
    (
        payment_streak, on_time_rate, recharge_amt, recharge_cons,
        rent_cons, txn_freq, txn_vol, income_stab, employment_enc,
        num_deps, repaid_loan, completeness, months_data,
    ) = feature_vector

    score = 0.0
    # Weights summing to 1.0
    score += on_time_rate * 0.25
    score += min(payment_streak / 24, 1.0) * 0.15
    score += recharge_cons * 0.10
    score += rent_cons * 0.10
    score += income_stab * 0.15
    score += (employment_enc / 3.0) * 0.10
    score += repaid_loan * 0.05
    score += completeness * 0.05
    score += min(months_data / 24, 1.0) * 0.05
    # Penalize many dependents
    score -= min(num_deps / 10.0, 0.10) * 0.10

    return max(0.0, min(score, 1.0))


def probability_to_score(probability: float) -> int:
    """Convert model output probability (0–1) to 0–100 score."""
    # Non-linear scaling: compress extremes, expand mid-range
    import math
    scaled = 10 + (probability ** 0.8) * 85
    return int(round(min(max(scaled, 0), 100)))


def tier_from_score(score: int) -> str:
    if score >= 71:
        return "low"
    elif score >= 41:
        return "medium"
    return "high"


def generate_score(
    doc_features: dict,
    conversation_features: dict,
) -> tuple[int, str, list[float], float]:
    """
    Main entry point: produce a credit score.

    Returns (score_0_100, risk_tier, feature_vector, data_completeness).
    """
    feature_vector, completeness = build_feature_vector(doc_features, conversation_features)

    model = _load_model()

    if model == "rule_based":
        probability = rule_based_score(feature_vector)
    else:
        arr = np.array([feature_vector])
        probability = float(model.predict_proba(arr)[0][1])

    score = probability_to_score(probability)
    tier = tier_from_score(score)

    return score, tier, feature_vector, completeness


def build_score_breakdown(
    feature_vector: list[float],
    score: int,
) -> list[dict]:
    """
    Generate the per-signal breakdown shown in the UI.
    Each signal contributes a portion of the final score.
    """
    (
        payment_streak, on_time_rate, recharge_amt, recharge_cons,
        rent_cons, txn_freq, txn_vol, income_stab, employment_enc,
        num_deps, repaid_loan, completeness, months_data,
    ) = feature_vector

    def strength(rate: float) -> str:
        if rate >= 0.8:
            return "strong"
        elif rate >= 0.6:
            return "good"
        elif rate >= 0.4:
            return "moderate"
        return "weak"

    total_score = max(score, 1)

    breakdown = [
        {
            "title": "Utility Payments",
            "icon": "Zap",
            "contribution": int(score * 0.30),
            "strength": strength(on_time_rate),
            "percent": int(on_time_rate * 100),
            "detail": (
                f"{int(payment_streak)} months of consistent payments"
                if payment_streak > 0
                else "No utility payment data found"
            ),
        },
        {
            "title": "Mobile Recharge",
            "icon": "Smartphone",
            "contribution": int(score * 0.20),
            "strength": strength(recharge_cons),
            "percent": int(recharge_cons * 100),
            "detail": (
                f"Average ₹{recharge_amt:.0f}/month recharge detected"
                if recharge_amt > 0
                else "No recharge history found"
            ),
        },
        {
            "title": "Transaction Activity",
            "icon": "ArrowLeftRight",
            "contribution": int(score * 0.25),
            "strength": strength(min(txn_freq / 30, 1.0)),
            "percent": int(min(txn_freq / 30, 1.0) * 100),
            "detail": (
                f"{int(txn_freq)} transactions/month on average"
                if txn_freq > 0
                else "Limited transaction history"
            ),
        },
        {
            "title": "Income Stability",
            "icon": "TrendingUp",
            "contribution": int(score * 0.25),
            "strength": strength(income_stab),
            "percent": int(income_stab * 100),
            "detail": "Based on your reported income and employment type",
        },
    ]

    return breakdown
