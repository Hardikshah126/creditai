"""Unit tests for scoring_service – no DB, no model file needed."""
from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.scoring_service import _fill_defaults, _compute_completeness, _build_breakdown, FEATURE_COLS


def test_fill_defaults_fills_nones():
    features = {k: None for k in FEATURE_COLS}
    filled = _fill_defaults(features)
    assert all(v is not None for v in filled.values())


def test_compute_completeness_all_none():
    features = {k: None for k in FEATURE_COLS}
    assert _compute_completeness(features) == 0.0


def test_compute_completeness_all_set():
    features = {k: 1 for k in FEATURE_COLS}
    assert _compute_completeness(features) == 1.0


def test_compute_completeness_partial():
    features = {k: None for k in FEATURE_COLS}
    features[FEATURE_COLS[0]] = 5
    features[FEATURE_COLS[1]] = 0.8
    result = _compute_completeness(features)
    assert 0 < result < 1


def test_build_breakdown_structure():
    from app.services.scoring_service import _fill_defaults, FEATURE_COLS
    raw = {k: None for k in FEATURE_COLS}
    filled = _fill_defaults(raw)
    breakdown = _build_breakdown(filled, 65)
    assert len(breakdown) == 4
    for card in breakdown:
        assert "title" in card
        assert "icon" in card
        assert "contribution" in card
        assert "strength" in card
        assert card["strength"] in ("strong", "good", "moderate", "weak")
        assert 0 <= card["percent"] <= 100


def test_strength_thresholds():
    from app.services.scoring_service import _build_breakdown
    # High-scoring features → "strong"
    filled = {
        "utility_payment_streak_months": 24,
        "utility_on_time_rate": 0.95,
        "avg_monthly_recharge_usd": 20,
        "recharge_consistency_score": 0.95,
        "rent_payment_consistency": 0.95,
        "upi_tx_frequency_per_month": 25,
        "avg_monthly_tx_volume_usd": 250,
        "income_stability_score": 0.95,
        "employment_type": 3,
        "num_dependents": 0,
        "had_informal_loan": 0,
        "data_completeness_score": 1.0,
    }
    breakdown = _build_breakdown(filled, 90)
    assert breakdown[0]["strength"] in ("strong", "good")
