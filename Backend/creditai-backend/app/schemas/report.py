from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.report import RiskTier, LenderDecision


class SignalCard(BaseModel):
    title: str
    icon: str
    contribution: int
    strength: str       # "strong" | "good" | "moderate" | "weak"
    percent: int
    detail: str


class ReportOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    submission_id: int
    user_name: str = ""     # applicant name — populated by lender routes
    score: int
    risk_tier: RiskTier
    ml_probability: float = 0.0
    score_breakdown: List[SignalCard]
    positive_signals: List[str]
    improvement_areas: List[str]
    report_text: str
    data_sources: List[str]
    model_version: str
    is_shared_with_lender: bool
    lender_decision: Optional[LenderDecision]
    created_at: datetime


# ── Lender-facing schemas ─────────────────────────────────────────────────────

class LenderApplicantRow(BaseModel):
    """One row in the lender applicants table."""
    report_id: int          # used by frontend for navigation
    name: str
    score: int
    risk_tier: RiskTier
    country: str
    created_at: datetime
    sources: List[str]


class LenderDecisionIn(BaseModel):
    decision: LenderDecision
    notes: Optional[str] = None