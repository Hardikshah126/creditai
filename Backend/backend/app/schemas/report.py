from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SignalBreakdown(BaseModel):
    title: str
    icon: str
    contribution: int
    strength: str   # "strong" | "good" | "moderate" | "weak"
    percent: int
    detail: str


class CreditReportResponse(BaseModel):
    id: str
    submission_id: str
    score: int
    risk_tier: str
    model_version: str
    breakdown: List[SignalBreakdown]
    summary_text: Optional[str]
    positive_signals: List[str]
    improvement_areas: List[str]
    share_token: Optional[str]
    is_shared_with_lender: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ShareReportRequest(BaseModel):
    report_id: str


class ShareReportResponse(BaseModel):
    share_url: str
    share_token: str


# Lender-facing schemas
class LenderApplicantSummary(BaseModel):
    report_id: str
    applicant_name: str
    applicant_country: str
    score: int
    risk_tier: str
    sources: List[str]
    submitted_at: datetime


class LenderDecisionRequest(BaseModel):
    report_id: str
    decision: str   # "approved" | "declined" | "manual_review"
    notes: Optional[str] = None


class LenderDecisionResponse(BaseModel):
    id: str
    report_id: str
    decision: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
