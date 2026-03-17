from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import get_db
from app.models.user import User
from app.models.report import CreditReport, LenderDecision
from app.models.document import Document
from app.schemas.report import LenderApplicantRow, ReportOut, SignalCard, LenderDecisionIn
from app.core.security import get_current_lender

router = APIRouter(prefix="/lender", tags=["lender"])


@router.get("/applicants", response_model=list[LenderApplicantRow])
async def list_applicants(
    search: str = Query(""),
    risk_tier: str = Query(""),
    current_lender: User = Depends(get_current_lender),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(CreditReport, User)
        .join(User, User.id == CreditReport.user_id)
        .where(CreditReport.is_shared_with_lender == True)  # noqa: E712
    )

    if risk_tier and risk_tier.upper() in ("LOW", "MEDIUM", "HIGH"):
        query = query.where(CreditReport.risk_tier == risk_tier.upper())

    result = await db.execute(query)
    rows = result.all()

    out = []
    for report, user in rows:
        if search and search.lower() not in user.name.lower():
            continue

        docs_result = await db.execute(
            select(Document.doc_type).where(Document.submission_id == report.submission_id)
        )
        sources = list({r[0] for r in docs_result.all()})

        out.append(LenderApplicantRow(
            report_id=report.id,
            name=user.name,
            score=report.score,
            risk_tier=report.risk_tier,
            country=user.country,
            created_at=report.created_at,
            sources=sources,
        ))

    return out


@router.get("/applicants/{report_id}", response_model=ReportOut)
async def get_applicant_report(
    report_id: int,
    current_lender: User = Depends(get_current_lender),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CreditReport, User)
        .join(User, User.id == CreditReport.user_id)
        .where(
            CreditReport.id == report_id,
            CreditReport.is_shared_with_lender == True,  # noqa: E712
        )
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found or not shared")

    report, user = row

    # Parse JSON fields safely
    def parse_json(val, default):
        if isinstance(val, list):
            return val
        try:
            return json.loads(val or "[]")
        except Exception:
            return default

    breakdown_raw = parse_json(report.score_breakdown, [])
    breakdown = []
    for s in breakdown_raw:
        try:
            breakdown.append(SignalCard(**s))
        except Exception:
            pass

    return ReportOut(
        id=report.id,
        submission_id=report.submission_id,
        user_name=user.name,
        score=report.score,
        risk_tier=report.risk_tier,
        ml_probability=report.ml_probability or 0.0,
        score_breakdown=breakdown,
        positive_signals=parse_json(report.positive_signals, []),
        improvement_areas=parse_json(report.improvement_areas, []),
        report_text=report.report_text or "",
        data_sources=parse_json(report.data_sources, []),
        model_version=report.model_version or "xgboost-v1",
        is_shared_with_lender=report.is_shared_with_lender,
        lender_decision=report.lender_decision,
        created_at=report.created_at,
    )


@router.patch("/applicants/{report_id}/decision")
async def record_decision(
    report_id: int,
    body: LenderDecisionIn,
    current_lender: User = Depends(get_current_lender),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CreditReport).where(CreditReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")

    report.lender_decision = LenderDecision(body.decision)
    report.lender_notes = body.notes
    report.decision_at = datetime.now(timezone.utc)
    await db.commit()
    return {"report_id": report_id, "decision": body.decision}