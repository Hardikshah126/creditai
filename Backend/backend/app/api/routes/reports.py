import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.submission import Submission
from app.models.alternative_data import AlternativeData
from app.models.agent_conversation import AgentConversation
from app.models.credit_report import CreditReport
from app.models.lender_decision import LenderDecision
from app.core.security import get_current_user, get_current_lender
from app.schemas.report import (
    CreditReportResponse,
    SignalBreakdown,
    ShareReportRequest,
    ShareReportResponse,
    LenderApplicantSummary,
    LenderDecisionRequest,
    LenderDecisionResponse,
)
from app.services.scoring_service import generate_score, build_score_breakdown
from app.services.report_service import generate_report_narrative, generate_share_token
from app.services.agent_service import extract_features_from_conversation

router = APIRouter(prefix="/reports", tags=["reports"])


def _aggregate_doc_features(submission: Submission) -> dict:
    features = {}
    for doc in submission.documents:
        if doc.extracted_features:
            try:
                features.update(json.loads(doc.extracted_features))
            except json.JSONDecodeError:
                pass
    return features


def _aggregate_conversation_features(submission: Submission) -> dict:
    history = [
        {"role": m.role, "message": m.message}
        for m in sorted(submission.conversations, key=lambda x: int(x.turn_index))
    ]
    return extract_features_from_conversation(history)


def _report_to_response(report: CreditReport) -> CreditReportResponse:
    breakdown = json.loads(report.breakdown_json) if report.breakdown_json else []
    positive = json.loads(report.positive_signals_json) if report.positive_signals_json else []
    improvement = json.loads(report.improvement_areas_json) if report.improvement_areas_json else []
    return CreditReportResponse(
        id=report.id,
        submission_id=report.submission_id,
        score=report.score,
        risk_tier=report.risk_tier,
        model_version=report.model_version,
        breakdown=[SignalBreakdown(**s) for s in breakdown],
        summary_text=report.summary_text,
        positive_signals=positive,
        improvement_areas=improvement,
        share_token=report.share_token,
        is_shared_with_lender=report.is_shared_with_lender,
        created_at=report.created_at,
    )


# ── Applicant endpoints ────────────────────────────────────────────────────────

@router.post("/{submission_id}/generate", response_model=CreditReportResponse)
def generate_report(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate (or regenerate) the credit report for a submission.
    Call this after the AI conversation is complete.
    """
    submission = db.query(Submission).filter(
        Submission.id == submission_id,
        Submission.user_id == current_user.id,
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if not submission.documents:
        raise HTTPException(status_code=400, detail="No documents uploaded")

    # Merge all feature sources
    doc_features = _aggregate_doc_features(submission)
    convo_features = _aggregate_conversation_features(submission)

    # Run the ML model
    score, risk_tier, feature_vector, completeness = generate_score(doc_features, convo_features)

    # Build per-signal breakdown
    breakdown = build_score_breakdown(feature_vector, score)

    # Generate narrative with Claude
    summary, positives, improvements = generate_report_narrative(
        applicant_name=current_user.name,
        score=score,
        risk_tier=risk_tier,
        breakdown=breakdown,
        feature_vector=feature_vector,
    )

    # Upsert report
    existing = db.query(CreditReport).filter(
        CreditReport.submission_id == submission_id
    ).first()

    if existing:
        report = existing
    else:
        report = CreditReport(submission_id=submission_id)
        db.add(report)

    report.score = score
    report.risk_tier = risk_tier
    report.model_version = "xgb_v1"
    report.features_json = json.dumps({"doc": doc_features, "convo": convo_features})
    report.breakdown_json = json.dumps(breakdown)
    report.summary_text = summary
    report.positive_signals_json = json.dumps(positives)
    report.improvement_areas_json = json.dumps(improvements)

    submission.status = "scored"
    db.commit()
    db.refresh(report)

    return _report_to_response(report)


@router.get("/my/latest", response_model=CreditReportResponse)
def get_my_latest_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the most recent credit report for the logged-in applicant."""
    report = (
        db.query(CreditReport)
        .join(Submission)
        .filter(Submission.user_id == current_user.id)
        .order_by(CreditReport.created_at.desc())
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="No credit report found")
    return _report_to_response(report)


@router.get("/my/history", response_model=List[CreditReportResponse])
def get_my_report_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reports = (
        db.query(CreditReport)
        .join(Submission)
        .filter(Submission.user_id == current_user.id)
        .order_by(CreditReport.created_at.desc())
        .all()
    )
    return [_report_to_response(r) for r in reports]


@router.post("/{report_id}/share", response_model=ShareReportResponse)
def share_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a shareable link for a credit report."""
    report = (
        db.query(CreditReport)
        .join(Submission)
        .filter(CreditReport.id == report_id, Submission.user_id == current_user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if not report.share_token:
        report.share_token = generate_share_token()
        report.is_shared_with_lender = True
        db.commit()

    return ShareReportResponse(
        share_token=report.share_token,
        share_url=f"https://creditai.app/report/{report.share_token}",
    )


# ── Public shared report endpoint (no auth) ────────────────────────────────────

@router.get("/shared/{token}", response_model=CreditReportResponse)
def get_shared_report(token: str, db: Session = Depends(get_db)):
    """Publicly accessible report via share token (for lenders)."""
    report = db.query(CreditReport).filter(CreditReport.share_token == token).first()
    if not report or not report.is_shared_with_lender:
        raise HTTPException(status_code=404, detail="Report not found or not shared")
    return _report_to_response(report)


# ── Lender endpoints ───────────────────────────────────────────────────────────

@router.get("/lender/applicants", response_model=List[LenderApplicantSummary])
def list_lender_applicants(
    risk_tier: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_lender: User = Depends(get_current_lender),
):
    """List all applicants who have shared their reports."""
    query = (
        db.query(CreditReport, Submission, User)
        .join(Submission, CreditReport.submission_id == Submission.id)
        .join(User, Submission.user_id == User.id)
        .filter(CreditReport.is_shared_with_lender == True)
    )
    if risk_tier:
        query = query.filter(CreditReport.risk_tier == risk_tier)

    results = query.order_by(CreditReport.created_at.desc()).all()

    summaries = []
    for report, submission, user in results:
        if search and search.lower() not in user.name.lower():
            continue
        sources = [doc.doc_type.replace("_", " ").title() for doc in submission.documents]
        summaries.append(
            LenderApplicantSummary(
                report_id=report.id,
                applicant_name=user.name,
                applicant_country=user.country,
                score=report.score,
                risk_tier=report.risk_tier,
                sources=list(set(sources)),
                submitted_at=report.created_at,
            )
        )
    return summaries


@router.get("/lender/{report_id}", response_model=CreditReportResponse)
def get_report_for_lender(
    report_id: str,
    db: Session = Depends(get_db),
    current_lender: User = Depends(get_current_lender),
):
    """Get a full credit report (lender view)."""
    report = db.query(CreditReport).filter(
        CreditReport.id == report_id,
        CreditReport.is_shared_with_lender == True,
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _report_to_response(report)


@router.post("/lender/decision", response_model=LenderDecisionResponse)
def record_decision(
    body: LenderDecisionRequest,
    db: Session = Depends(get_db),
    current_lender: User = Depends(get_current_lender),
):
    """Record a lender's decision (approved / declined / manual_review) on a report."""
    if body.decision not in ("approved", "declined", "manual_review"):
        raise HTTPException(status_code=400, detail="Invalid decision value")

    report = db.query(CreditReport).filter(CreditReport.id == body.report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    decision = LenderDecision(
        report_id=body.report_id,
        lender_id=current_lender.id,
        decision=body.decision,
        notes=body.notes,
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision
