from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import get_db
from app.models.user import User
from app.models.submission import Submission, SubmissionStatus
from app.models.report import CreditReport, RiskTier
from app.schemas.report import ReportOut, SignalCard
from app.core.security import get_current_user
from app.services import scoring_service, report_service

router = APIRouter(prefix="/reports", tags=["reports"])


def _parse_report(report: CreditReport) -> ReportOut:
    def safe_parse(val, default):
        if isinstance(val, list):
            return val
        try:
            return json.loads(val or "[]")
        except Exception:
            return default

    breakdown_raw = safe_parse(report.score_breakdown, [])
    breakdown = []
    for s in breakdown_raw:
        try:
            breakdown.append(SignalCard(**s))
        except Exception:
            pass

    return ReportOut(
        id=report.id,
        submission_id=report.submission_id,
        score=report.score,
        risk_tier=report.risk_tier,
        ml_probability=report.ml_probability or 0.0,
        score_breakdown=breakdown,
        positive_signals=safe_parse(report.positive_signals, []),
        improvement_areas=safe_parse(report.improvement_areas, []),
        report_text=report.report_text or "",
        data_sources=safe_parse(report.data_sources, []),
        model_version=report.model_version or "xgboost-v1",
        is_shared_with_lender=report.is_shared_with_lender,
        lender_decision=report.lender_decision,
        created_at=report.created_at,
    )


@router.post("/{submission_id}/generate", response_model=ReportOut, status_code=201)
async def generate_report(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub_result = await db.execute(
        select(Submission).where(
            Submission.id == submission_id,
            Submission.user_id == current_user.id,
        )
    )
    sub = sub_result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Submission not found")
    if sub.status not in (SubmissionStatus.SCORING, SubmissionStatus.COMPLETED):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Submission is not ready for scoring (status: {sub.status})",
        )

    # Idempotent – return existing report if already generated
    existing_result = await db.execute(
        select(CreditReport).where(CreditReport.submission_id == submission_id)
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        return _parse_report(existing)

    # ── Run ML model ──────────────────────────────────────────────────────────
    features = json.loads(sub.extracted_features or "{}")

    # Calculate data_completeness_score before scoring
    non_null = sum(1 for k, v in features.items()
                   if k != "data_completeness_score" and v is not None)
    total = len([k for k in features if k != "data_completeness_score"])
    features["data_completeness_score"] = round(non_null / total, 2) if total else 0.5

    prediction = scoring_service.predict(features)

    score = prediction["score"]
    risk_tier = RiskTier(prediction["risk_tier"])
    breakdown = prediction["score_breakdown"]

    # ── Derive signal lists ───────────────────────────────────────────────────
    positives, improvements = report_service.derive_signals(features, breakdown)

    # ── Get document source names ─────────────────────────────────────────────
    from app.models.document import Document
    docs_result = await db.execute(
        select(Document).where(Document.submission_id == submission_id)
    )
    docs = docs_result.scalars().all()
    data_sources = list({d.doc_type for d in docs})

    # ── LLM report narrative ──────────────────────────────────────────────────
    report_text = await report_service.generate_report_text(
        name=current_user.name,
        score=score,
        risk_tier=risk_tier.value,
        breakdown=breakdown,
        positive_signals=positives,
        improvement_areas=improvements,
    )

    report = CreditReport(
        submission_id=submission_id,
        user_id=current_user.id,
        score=score,
        risk_tier=risk_tier,
        ml_probability=prediction["ml_probability"],
        score_breakdown=json.dumps(breakdown),
        positive_signals=json.dumps(positives),
        improvement_areas=json.dumps(improvements),
        report_text=report_text,
        data_sources=json.dumps(data_sources),
        model_version="xgboost-v1",
        is_shared_with_lender=False,
    )
    db.add(report)
    sub.status = SubmissionStatus.COMPLETED
    await db.commit()
    await db.refresh(report)
    return _parse_report(report)


@router.get("/latest", response_model=ReportOut)
async def get_latest_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CreditReport)
        .where(CreditReport.user_id == current_user.id)
        .order_by(CreditReport.created_at.desc())
        .limit(1)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No report found")
    return _parse_report(report)


@router.get("/{submission_id}", response_model=ReportOut)
async def get_report(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CreditReport).where(
            CreditReport.submission_id == submission_id,
            CreditReport.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
    return _parse_report(report)


@router.post("/{submission_id}/share")
async def share_report(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CreditReport).where(
            CreditReport.submission_id == submission_id,
            CreditReport.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
    report.is_shared_with_lender = True
    await db.commit()
    return {"shared": True, "report_id": report.id}


@router.get("/{submission_id}/pdf")
async def download_pdf(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CreditReport).where(
            CreditReport.submission_id == submission_id,
            CreditReport.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")

    pdf_bytes = report_service.build_pdf(
        name=current_user.name,
        country=current_user.country,
        score=report.score,
        risk_tier=report.risk_tier.value,
        report_text=report.report_text or "",
        positive_signals=json.loads(report.positive_signals or "[]"),
        improvement_areas=json.loads(report.improvement_areas or "[]"),
        report_id=f"CR-{report.id:08d}",
        generated_date=report.created_at.strftime("%b %d, %Y"),
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=creditai-report-{report.id}.pdf"
        },
    )