from __future__ import annotations
import enum
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, Text, Integer, Float, Boolean
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.submission import Submission


class RiskTier(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LenderDecision(str, enum.Enum):
    APPROVED = "approved"
    DECLINED = "declined"
    MANUAL_REVIEW = "manual_review"


class CreditReport(Base):
    __tablename__ = "credit_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id"), unique=True, index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    score: Mapped[int] = mapped_column(Integer)
    risk_tier: Mapped[RiskTier] = mapped_column(SAEnum(RiskTier))
    ml_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # All stored as JSON strings
    score_breakdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    positive_signals: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    improvement_areas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    report_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_sources: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    model_version: Mapped[str] = mapped_column(String(50), default="xgboost-v1")
    is_shared_with_lender: Mapped[bool] = mapped_column(Boolean, default=False)

    # Lender decision (recorded via PATCH)
    lender_decision: Mapped[Optional[LenderDecision]] = mapped_column(
        SAEnum(LenderDecision), nullable=True
    )
    lender_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decision_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="reports")
    submission: Mapped["Submission"] = relationship(back_populates="report")
