import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from app.db.session import Base


class CreditReport(Base):
    __tablename__ = "credit_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = Column(String, ForeignKey("submissions.id"), nullable=False, unique=True)

    # Score output
    score = Column(Integer, nullable=False)           # 0 – 100
    risk_tier = Column(
        Enum("low", "medium", "high", name="risk_tier"),
        nullable=False,
    )
    model_version = Column(String, nullable=False, default="xgb_v1")

    # Input features (stored as JSON string for auditability)
    features_json = Column(Text, nullable=True)

    # Score breakdown (JSON: list of {title, contribution, strength, percent, detail})
    breakdown_json = Column(Text, nullable=True)

    # LLM-generated human-readable sections
    summary_text = Column(Text, nullable=True)
    positive_signals_json = Column(Text, nullable=True)   # JSON list
    improvement_areas_json = Column(Text, nullable=True)  # JSON list

    # Sharing
    share_token = Column(String, unique=True, nullable=True)
    is_shared_with_lender = Column(Boolean, default=False)
    pdf_path = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    submission = relationship("Submission", back_populates="report")
    lender_decisions = relationship("LenderDecision", back_populates="report", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CreditReport id={self.id} score={self.score} risk={self.risk_tier}>"
