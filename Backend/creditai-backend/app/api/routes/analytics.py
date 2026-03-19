from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import get_db
from app.models.user import User
from app.models.report import CreditReport, RiskTier, LenderDecision
from app.core.security import get_current_lender

router = APIRouter(prefix="/lender", tags=["lender"])


@router.get("/analytics")
async def get_analytics(
    current_lender: User = Depends(get_current_lender),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CreditReport).where(CreditReport.is_shared_with_lender == True)  # noqa: E712
    )
    reports = result.scalars().all()

    if not reports:
        return {
            "total": 0,
            "approved": 0,
            "rejected": 0,
            "pending": 0,
            "avg_score": 0,
            "risk_distribution": {"low": 0, "medium": 0, "high": 0},
            "score_buckets": [],
            "recent_decisions": [],
        }

    total = len(reports)
    approved = sum(1 for r in reports if r.lender_decision == LenderDecision.APPROVED)
    rejected = sum(1 for r in reports if r.lender_decision == LenderDecision.DECLINED)
    pending = total - approved - rejected
    avg_score = round(sum(r.score for r in reports) / total)

    risk_distribution = {
        "low":    sum(1 for r in reports if r.risk_tier == RiskTier.LOW),
        "medium": sum(1 for r in reports if r.risk_tier == RiskTier.MEDIUM),
        "high":   sum(1 for r in reports if r.risk_tier == RiskTier.HIGH),
    }

    buckets = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    for r in reports:
        if r.score <= 20:   buckets["0-20"] += 1
        elif r.score <= 40: buckets["21-40"] += 1
        elif r.score <= 60: buckets["41-60"] += 1
        elif r.score <= 80: buckets["61-80"] += 1
        else:               buckets["81-100"] += 1

    score_buckets = [{"range": k, "count": v} for k, v in buckets.items()]

    decided = [r for r in reports if r.lender_decision is not None]
    decided.sort(key=lambda r: r.decision_at or r.created_at, reverse=True)

    recent_decisions = []
    for r in decided[:5]:
        user_result = await db.execute(select(User).where(User.id == r.user_id))
        user = user_result.scalar_one_or_none()
        recent_decisions.append({
            "name": user.name if user else "Unknown",
            "score": r.score,
            "decision": r.lender_decision.value.upper(),
            "decided_at": r.decision_at.isoformat() if r.decision_at else r.created_at.isoformat(),
        })

    return {
        "total": total,
        "approved": approved,
        "rejected": rejected,
        "pending": pending,
        "avg_score": avg_score,
        "risk_distribution": risk_distribution,
        "score_buckets": score_buckets,
        "recent_decisions": recent_decisions,
    }