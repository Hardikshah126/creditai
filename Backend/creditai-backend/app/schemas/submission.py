from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.submission import SubmissionStatus


class SubmissionCreate(BaseModel):
    pass  # just POST /submissions/ – user comes from JWT


class DocumentOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    original_filename: str
    doc_type: str
    file_size_bytes: Optional[int]
    is_low_confidence: bool
    created_at: datetime


class SubmissionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    status: SubmissionStatus
    documents: List[DocumentOut] = []
    created_at: datetime
    updated_at: datetime


class DashboardStats(BaseModel):
    """Data for the applicant Dashboard page."""
    name: str
    country: str
    profile_complete_pct: int         # 0-100
    documents_uploaded: int
    report_generated: bool
    score: Optional[int]
    risk_tier: Optional[str]
    latest_submission_id: Optional[int]
    recent_activity: List[dict]
